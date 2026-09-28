# StegoShield 🛡️

### Securely Hide. Safely Share.

[![Production Deployment](https://img.shields.io/badge/Deployment-Live%20on%20Render-00f2fe?style=for-the-badge&logo=render)](https://stegoshield-bbl7.onrender.com)
[![Status](https://img.shields.io/badge/Status-Operational%20%28200%20OK%29-10b981?style=for-the-badge)](https://stegoshield-bbl7.onrender.com/health)
[![PWA Ready](https://img.shields.io/badge/PWA-Installable-3b82f6?style=for-the-badge)](https://stegoshield-bbl7.onrender.com)

**Live Cloud URL:** [https://stegoshield-bbl7.onrender.com](https://stegoshield-bbl7.onrender.com)

**StegoShield** is a production-grade, cybersecurity-focused web platform for image steganography and cryptographic message transport. It enables users to embed confidential text inside ordinary images using Least Significant Bit (LSB) steganography, layered with optional authenticated encryption (AES-256-GCM) and tamper-proof SHA-256 integrity verification.

---


## Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                STEGOSHIELD PLATFORM                               |
+-----------------------------------------------------------------------------------+

[ SENDER: HIDE WORKFLOW ]
  +-------------------+
  | Plaintext Message |  (UTF-8 / Unicode / Emojis)
  +---------+---------+
            |
            v
     [ Password Set? ]
       /          \
     (YES)        (NO)
      /             \
     v               v
+------------------+  +--------------------+
| PBKDF2-HMAC-SHA  |  | Plaintext Payload  |
| 600,000 iters    |  +---------+----------+
| 16B Salt / 12B IV|            |
+--------+---------+            |
         |                      |
         v                      |
+------------------+            |
|   AES-256-GCM    |            |
| Encrypted Cipher |            |
+--------+---------+            |
         \                      /
          \                    /
           v                  v
+---------------------------------------------------+
| 48-Byte Binary Header Builder                     |
| [MAGIC: STGSHLD!] [VER: 1] [FLAGS] [LEN] [SHA256] |
+-------------------------+-------------------------+
                          |
                          v
+---------------------------------------------------+
| LSB Bit Stream Embedder (Pillow Engine)           |
| Replaces LSB of RGB color channels (Delta <= 0.39%)|
+-------------------------+-------------------------+
                          |
                          v
                +--------------------+
                | Lossless Stego PNG |
                +--------------------+

-------------------------------------------------------------------------------------

[ RECEIVER: EXTRACT WORKFLOW ]
                +--------------------+
                | Lossless Stego PNG |
                +---------+----------+
                          |
                          v
+---------------------------------------------------+
| LSB Bit Stream Reader                             |
| Extracts first 48 bytes -> Validates STGSHLD! Magic|
+-------------------------+-------------------------+
                          |
                          v
+---------------------------------------------------+
| Integrity Check                                   |
| Computes SHA-256 digest == Header Checksum?       |
+-------------------------+-------------------------+
                          |
                          v
     [ Encrypted Flag Set? ]
       /                 \
     (YES)               (NO)
      /                    \
     v                      v
+--------------------+   +--------------------+
| Prompt for Password|   | Direct UTF-8 Decode|
| AES-256-GCM Decrypt|   +---------+----------+
+---------+----------+             |
          \                       /
           \                     /
            v                   v
     +----------------------------------+
     | Recovered & Verified Message     |
     +----------------------------------+
```

---

## Features

- **Progressive Web App (PWA) Architecture:** Fully installable as a standalone app on Android, iOS, Windows, macOS, and tablets from a single codebase, while remaining 100% usable in standard web browsers without installation.
- **Root-Scoped Service Worker & Offline Caching:** Pre-caches the application shell, stylesheet, fonts, icons, and educational pages (`/how-it-works`, `/security`, `/offline`) with network-first and stale-while-revalidate caching strategies.
- **Cross-Platform Install Prompts:** Seamlessly handles native Chromium `beforeinstallprompt` triggers and provides an interactive iOS Safari "Add to Home Screen" guide modal.
- **Lossless LSB Steganography:** Modifies only the least significant bit of Red, Green, and Blue pixel channels, resulting in undetectable visual changes.
- **AES-256-GCM Authenticated Encryption:** Protects message contents against eavesdropping and brute force using 600,000-iteration PBKDF2-HMAC-SHA256 key derivation.
- **Robust 48-Byte Binary Header:** Replaces fragile string delimiters with a structured packet format containing magic identifier (`STGSHLD!`), protocol version, flags, payload length, and a 256-bit SHA-256 integrity checksum.
- **Tamper & Corruption Detection:** Automatically identifies modified, compressed, or corrupted images, preventing garbled or forged plaintexts from being displayed.
- **Full Multilingual & Unicode Support:** Supports English, numbers, punctuation, emojis (🚀, 🔐), Indian scripts (Telugu, Hindi), Japanese, Chinese, and multiline text.
- **Real-Time Client-Side Capacity Calculator:** Computes exact usable bytes, payload sizing, and gauge metrics dynamically as text is typed.
- **Zero-Storage Privacy Architecture:** Processes all uploads and stego outputs ephemerally with automated cleanup routines. No permanent databases or message logging.
- **Mobile-First Responsive Cybersecurity UI:** Modern dark glassmorphic interface with safe area insets (`env(safe-area-inset-*)`), touch targets >= 48px, and high-contrast accessibility.

---

## How Steganography Works

Least Significant Bit (LSB) steganography takes advantage of human visual limitations. In standard 24-bit color images, each pixel consists of 3 bytes (Red, Green, Blue), with each channel having a value from `0` to `255`.

### Binary Example

Consider a pixel with Red channel value `255`:
```
Decimal: 255
Binary:  1 1 1 1 1 1 1 [1]  <-- Least Significant Bit (LSB)
```

Suppose the next bit in our secret payload is `0`. We overwrite the LSB:
```
Original: 1 1 1 1 1 1 1 [1]  (255)
Embedded: 1 1 1 1 1 1 1 [0]  (254)
```

The brightness of the red component changes from `255` to `254`—a difference of `1 / 255 ≈ 0.39%`. Because human photoreceptors cannot distinguish this minute fluctuation on a display, the image looks 100% identical.

### Capacity Formula

For an RGB image of dimensions $W \times H$:
$$\text{Total Available Bits} = W \times H \times 3$$
$$\text{Total Available Bytes} = \lfloor \frac{\text{Total Available Bits}}{8} \rfloor$$
$$\text{Usable Message Capacity} = \text{Total Available Bytes} - 48\text{ bytes (Header)}$$

---

## Technology Stack

- **Backend:** Python 3.11, Flask 3.1
- **Imaging Engine:** Pillow (PIL) 12.0
- **Cryptography:** Python `cryptography` library (AES-256-GCM, PBKDF2-HMAC-SHA256)
- **Frontend:** Semantic HTML5, Vanilla CSS (Custom Design System, Glassmorphism, CSS Variables), Vanilla JavaScript (ES6+)
- **Testing:** Python `unittest` framework (31 automated unit and integration tests)

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- `pip` package manager

### 1. Clone or Navigate to Repository
```bash
cd "Is project real"
```

### 2. Create and Activate Virtual Environment
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 5. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## Automated Testing

StegoShield includes a comprehensive suite of 31 automated tests covering cryptographic functions, binary headers, capacity limits, image formats, and end-to-end workflows:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Test Coverage Highlights (38 Tests Passing):
1. `test_acceptance_test_1_basic_png_flow`: Standard hide -> save PNG -> reload -> extract message.
2. `test_acceptance_test_2_password_protection`: AES-256-GCM encryption + PBKDF2 derivation (600,000 rounds).
3. `test_acceptance_test_3_wrong_password`: Verifies rejection on invalid credentials without leaking internal stack traces.
4. `test_acceptance_test_4_ordinary_image_detection`: Verifies detection of non-stego cover images.
5. `test_acceptance_test_5_oversized_message_rejection`: Enforces capacity constraints prior to processing.
6. `test_acceptance_test_6_unicode_and_emojis`: Verifies Telugu, Japanese, emojis, and symbols.
7. `test_corrupted_stego_image_raises_integrity_error`: Tampered pixel detection via SHA-256 checksum verification.
8. `test_non_square_rgba_image`: Validates transparent PNGs with alpha preservation.
9. `test_health_check_endpoint`: Validates cloud container health monitoring (`/health`).
10. `test_security_headers_present`: Validates strict CSP, HSTS, X-Content-Type nosniff, and X-Frame-Options.
11. `test_api_wipe_existing_file`: Validates on-demand server file shredding for immediate user privacy.

---

## Production Cloud Deployment (Render / PaaS)

StegoShield is fully prepared for continuous cloud hosting (e.g., Render) so it runs 24/7 independently of any local machine.

### Deployment Files Provided:
- **`render.yaml`**: Infrastructure-as-code blueprint for 1-click Render web service deployment.
- **`Procfile`**: Process configuration for Gunicorn WSGI (`web: gunicorn --config gunicorn.conf.py app:app`).
- **`gunicorn.conf.py`**: Production WSGI server settings with `gthread` concurrency, 120s timeout, and port binding.
- **`runtime.txt`**: Pinned Python runtime (`python-3.11.9`).
- **`FINAL_DEPLOYMENT.md`**: Complete step-by-step deployment guide with verification procedures.

To deploy in under 3 minutes, follow the comprehensive instructions in [`FINAL_DEPLOYMENT.md`](FINAL_DEPLOYMENT.md).

---

## Security Model & Distinctions

| Aspect | Steganography | Encryption | StegoShield Combined |
| :--- | :--- | :--- | :--- |
| **Primary Goal** | Conceal message existence | Conceal message content | Conceals both existence and content |
| **Adversary Visibility** | Sees an ordinary picture | Sees scrambled ciphertext | Sees an ordinary picture |
| **If Algorithm Known** | Data can be extracted | Content remains secure | Ciphertext extracted, cannot decrypt |
| **Integrity Check** | Typically absent | GCM authentication tag | SHA-256 digest + GCM auth tag |
| **Privacy Guarantee** | N/A | N/A | Ephemeral storage + On-demand server shredding |

---

## Supported Formats & File Limits

- **Input Formats:** PNG, JPG, JPEG, BMP, WEBP (automatically converted to RGB / RGBA in-memory).
- **Output Format:** **Strictly PNG**. Lossless compression is mandatory to preserve least significant bits.
- **Upload Size Limit:** 10 MB per image (configurable via `config.py`).
- **Maximum Message Length:** 50,000 characters.
- **Image Bomb Mitigation:** `MAX_IMAGE_PIXELS = 25_000_000` (Pillow decompression safeguard).

---

## Project Structure

```
StegoShield/
├── app.py                      # Flask entry point, routes, /health, /api/wipe
├── config.py                   # Centralized configuration & privacy limits
├── gunicorn.conf.py            # Production WSGI server configuration
├── Procfile                    # Cloud PaaS process definition
├── render.yaml                 # Render Blueprint automated deployment spec
├── runtime.txt                 # Pinned Python version (3.11.9)
├── requirements.txt            # Python dependencies (Flask, Pillow, cryptography, Gunicorn)
├── .gitignore                  # Git ignore rules
├── .env.example                # Sample environment file
├── README.md                   # Project overview & documentation
├── FINAL_DEPLOYMENT.md         # Step-by-step cloud deployment & verification guide
│
├── steganography/              # Core steganography & crypto package
│   ├── __init__.py             # Public module interface
│   ├── crypto.py               # AES-256-GCM, PBKDF2-HMAC-SHA256 (600k iters)
│   ├── payload.py              # 48-byte binary header, packing, SHA-256
│   ├── encoder.py              # LSB bit embedder & capacity calculator
│   ├── decoder.py              # LSB bit extractor & integrity verification
│   └── utils.py                # Image validation, decompression bomb guard, file cleanup
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Main cybersecurity shell, navbar & footer, PWA modal
│   ├── index.html              # Landing hero, pipeline illustration, features
│   ├── hide.html               # 4-step wizard, capacity meter, on-demand shredder
│   ├── extract.html            # Decoder upload, password challenge modal, terminal
│   ├── how-it-works.html       # Interactive bit playground & educational guide
│   ├── security.html           # Threat model & cryptographic specifications
│   └── offline.html            # Graceful offline connectivity fallback page
│
├── static/                     # Static web assets & PWA files
│   ├── manifest.json           # Web App Manifest with icons & shortcuts
│   ├── sw.js                   # Root-scoped Service Worker (offline cache)
│   ├── css/
│   │   └── style.css           # Premium cyber design system (responsive)
│   ├── js/
│   │   ├── app.js              # Toasts, copy utils, mobile menu, PWA install prompt
│   │   ├── hide.js             # Drag & drop, capacity meter, generation & wipe UI
│   │   └── extract.js          # Extraction flow, password modal, verified reveal
│   └── images/
│       ├── logo.svg            # Custom SVG cyber shield logo
│       └── icons/              # PWA icons (192, 512, maskable, apple-touch, favicon)
│
├── uploads/                    # Ephemeral upload buffer (purged in finally blocks)
├── outputs/                    # Ephemeral output buffer (purged periodically & on-demand)
│
└── tests/                      # Automated test suite (38 tests)
    ├── __init__.py
    ├── test_crypto.py          # Cryptography unit tests
    ├── test_payload.py         # Binary header unit tests
    ├── test_encoder.py         # Capacity & embedding unit tests
    ├── test_decoder.py         # Decoding & inspection unit tests
    ├── test_end_to_end.py      # Acceptance test suite
    └── test_api.py             # Health check, security headers, PWA & wipe API tests
```


---

## License & Attribution

Designed and engineered for educational, portfolio, and security research purposes.
Free to use under the MIT License.
