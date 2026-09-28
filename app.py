"""
StegoShield Web Application
Production-ready Flask application for secure image steganography and AES-256-GCM message encryption.
"""

import os
import atexit
from threading import Thread
import time
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    send_from_directory,
    make_response,
    url_for,
    abort
)
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from steganography import (
    hide_message_in_image,
    extract_message_from_image,
    inspect_image_header,
    calculate_image_capacity,
    DecryptionError,
    PayloadError,
    HeaderCorruptionError
)
from steganography.encoder import CapacityExceededError
from steganography.payload import NoStegoHeaderError
from steganography.utils import (
    is_allowed_file,
    validate_and_open_image,
    generate_unique_filename,
    safe_join_paths,
    cleanup_expired_files
)

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Background file cleanup worker
_cleanup_running = True


def periodic_cleanup():
    while _cleanup_running:
        try:
            cleanup_expired_files(app.config['UPLOAD_FOLDER'], app.config['FILE_MAX_AGE_SECONDS'])
            cleanup_expired_files(app.config['OUTPUT_FOLDER'], app.config['FILE_MAX_AGE_SECONDS'])
        except Exception:
            pass
        time.sleep(app.config['CLEANUP_INTERVAL_SECONDS'])


cleanup_thread = Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()


@atexit.register
def stop_cleanup():
    global _cleanup_running
    _cleanup_running = False


# Security response headers
@app.after_request
def apply_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:;"
    )
    # HSTS when served over HTTPS (Render / production reverse proxy)
    if request.is_secure or request.headers.get('X-Forwarded-Proto', '').lower() == 'https':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response



# Error handlers
@app.errorhandler(413)
@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    if request.path.startswith('/api/'):
        return jsonify({
            "success": False,
            "error": f"Image exceeds the {app.config['MAX_UPLOAD_SIZE_MB']} MB upload limit."
        }), 413
    return render_template('base.html', error=f"File exceeds {app.config['MAX_UPLOAD_SIZE_MB']} MB limit."), 413


@app.errorhandler(404)
def handle_not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "Requested resource was not found."}), 404
    return render_template('base.html', error="404 - Page not found"), 404


@app.errorhandler(500)
def handle_server_error(e):
    if request.path.startswith('/api/'):
        return jsonify({
            "success": False,
            "error": "Something went wrong while processing the image. Please try again."
        }), 500
    return render_template('base.html', error="500 - Server error"), 500


# Health check endpoint for cloud PaaS (Render, Railway, Uptime monitors)
@app.route('/health')
@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "stegoshield",
        "version": "1.0.0",
        "storage": "operational"
    }), 200


# Page routes
@app.route('/')
def index():
    return render_template('index.html', active_page='home')



@app.route('/hide')
def hide_page():
    return render_template('hide.html', active_page='hide', max_chars=app.config['MAX_MESSAGE_CHARACTERS'])


@app.route('/extract')
def extract_page():
    return render_template('extract.html', active_page='extract')


@app.route('/how-it-works')
def how_it_works():
    return render_template('how-it-works.html', active_page='how-it-works')


@app.route('/security')
def security_page():
    return render_template('security.html', active_page='security')


@app.route('/offline')
def offline_page():
    return render_template('offline.html', active_page='offline')


@app.route('/manifest.json')
def web_manifest():
    """Serves the PWA Web App Manifest with correct MIME type."""
    response = make_response(send_from_directory('static', 'manifest.json'))
    response.headers['Content-Type'] = 'application/manifest+json; charset=utf-8'
    return response


@app.route('/sw.js')
def service_worker():
    """
    Serves the root-scoped Service Worker.
    Header Service-Worker-Allowed: / ensures scope covers entire domain.
    """
    response = make_response(send_from_directory('static', 'sw.js'))
    response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


# REST API endpoints
@app.route('/api/inspect', methods=['POST'])
def api_inspect():
    """
    Inspects an uploaded image to determine if it contains a StegoShield payload.
    """
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image file provided."}), 400
        
    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({"success": False, "error": "Please select an image file."}), 400
        
    if not is_allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": "Unsupported image format. Please upload PNG, JPG, JPEG, or BMP."
        }), 400

    temp_filename = generate_unique_filename("upload")
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
    
    try:
        file.save(temp_path)
        img = validate_and_open_image(temp_path)
        header_info = inspect_image_header(img)
        
        return jsonify({
            "success": True,
            "has_stego": header_info.get("has_stego", False),
            "is_encrypted": header_info.get("is_encrypted", False),
            "payload_length": header_info.get("payload_length", 0),
            "width": header_info.get("width", img.width),
            "height": header_info.get("height", img.height),
            "error": header_info.get("error")
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "error": "Unable to analyze the uploaded image."}), 500
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@app.route('/api/hide', methods=['POST'])
def api_hide():
    """
    Encodes secret message into the image using LSB steganography and optional AES-256-GCM encryption.
    """
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image file provided."}), 400
        
    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({"success": False, "error": "Please select an image file."}), 400
        
    if not is_allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": "Unsupported image format. Please upload PNG, JPG, JPEG, or BMP."
        }), 400

    message = request.form.get('message', '').strip()
    if not message:
        return jsonify({"success": False, "error": "Please enter a message to hide."}), 400

    if len(message) > app.config['MAX_MESSAGE_CHARACTERS']:
        return jsonify({
            "success": False,
            "error": f"Message exceeds maximum character limit of {app.config['MAX_MESSAGE_CHARACTERS']}."
        }), 400

    use_password = request.form.get('use_password', 'false').lower() == 'true'
    password = request.form.get('password', '').strip() if use_password else None

    if use_password and not password:
        return jsonify({"success": False, "error": "Password cannot be empty when password protection is enabled."}), 400

    temp_upload = os.path.join(app.config['UPLOAD_FOLDER'], generate_unique_filename("upload"))
    out_filename = generate_unique_filename("png")
    out_path = os.path.join(app.config['OUTPUT_FOLDER'], out_filename)

    try:
        file.save(temp_upload)
        img = validate_and_open_image(temp_upload)
        
        stego_img, meta = hide_message_in_image(img, message, password=password)
        
        # Save output strictly as PNG
        stego_img.save(out_path, format="PNG", optimize=False)
        
        return jsonify({
            "success": True,
            "download_url": f"/download/{out_filename}",
            "preview_url": f"/preview/{out_filename}",
            "filename": out_filename,
            "metadata": {
                "width": meta["width"],
                "height": meta["height"],
                "is_encrypted": meta["is_encrypted"],
                "payload_bytes": meta["payload_bytes"],
                "total_embedded_bytes": meta["total_embedded_bytes"],
                "capacity_bytes": meta["capacity_bytes"],
                "capacity_used_percent": meta["capacity_used_percent"],
                "original_filename": file.filename
            }
        })
    except CapacityExceededError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "An error occurred while generating the stego image. Please try again."
        }), 500
    finally:
        if os.path.exists(temp_upload):
            try:
                os.remove(temp_upload)
            except OSError:
                pass


@app.route('/api/extract', methods=['POST'])
def api_extract():
    """
    Extracts and verifies the secret message from an uploaded stego image.
    """
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "No image file provided."}), 400
        
    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({"success": False, "error": "Please select an image file."}), 400
        
    if not is_allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": "Unsupported image format. Please upload PNG, JPG, JPEG, or BMP."
        }), 400

    password = request.form.get('password', '').strip() or None
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], generate_unique_filename("upload"))

    try:
        file.save(temp_path)
        img = validate_and_open_image(temp_path)
        
        # First inspect header to see if password is required
        header_info = inspect_image_header(img)
        if not header_info.get("has_stego"):
            return jsonify({
                "success": False,
                "error": header_info.get("error", "No StegoShield message was detected in this image.")
            }), 400

        if header_info.get("is_encrypted") and not password:
            return jsonify({
                "success": False,
                "password_required": True,
                "error": "This message is protected with a password. Please enter the password to decrypt."
            }), 401

        recovered_msg, meta = extract_message_from_image(img, password=password)
        
        return jsonify({
            "success": True,
            "message": recovered_msg,
            "metadata": {
                "width": meta["width"],
                "height": meta["height"],
                "is_encrypted": meta["is_encrypted"],
                "payload_bytes": meta["payload_bytes"],
                "checksum": meta["checksum"],
                "version": meta["version"]
            }
        })
    except NoStegoHeaderError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except HeaderCorruptionError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except DecryptionError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception:
        return jsonify({
            "success": False,
            "error": "Something went wrong while processing the image. Please try again."
        }), 500
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@app.route('/download/<filename>')
def download_file(filename):
    """Safely serves the generated stego PNG image as an attachment."""
    try:
        safe_path = safe_join_paths(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.isfile(safe_path):
            abort(404)
        return send_file(
            safe_path,
            as_attachment=True,
            download_name="stego_shield_image.png",
            mimetype="image/png"
        )
    except Exception:
        abort(404)


@app.route('/preview/<filename>')
def preview_file(filename):
    """Safely serves the generated stego PNG image inline for browser preview."""
    try:
        safe_path = safe_join_paths(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.isfile(safe_path):
            abort(404)
        return send_file(
            safe_path,
            as_attachment=False,
            mimetype="image/png"
        )
    except Exception:
        abort(404)


@app.route('/api/wipe/<filename>', methods=['POST', 'DELETE'])
def api_wipe_file(filename):
    """
    Immediate privacy wipe: securely deletes an ephemeral output file upon client request.
    """
    try:
        safe_path = safe_join_paths(app.config['OUTPUT_FOLDER'], filename)
        if os.path.isfile(safe_path):
            os.remove(safe_path)
            return jsonify({"success": True, "message": "File wiped from server storage."}), 200
        return jsonify({"success": False, "error": "File does not exist or has already expired."}), 404
    except Exception:
        return jsonify({"success": False, "error": "Unable to wipe file."}), 400



if __name__ == '__main__':
    # Local development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')
    app.run(host='0.0.0.0', port=port, debug=debug)
