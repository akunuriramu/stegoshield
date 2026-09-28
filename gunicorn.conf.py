"""
StegoShield Production Gunicorn Configuration
Tuned for containerized and cloud PaaS environments (Render, Railway, Fly.io).
"""

import os
import multiprocessing

# Network Binding
# Render and cloud platforms supply PORT dynamically in the environment
port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Concurrency Model
# Steganography and PBKDF2 (600,000 iterations) are CPU-intensive.
# gthread worker class allows handling concurrent I/O with threads while keeping workers lean.
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
worker_class = "gthread"

# Timeouts
# Increased timeout prevents 502/504 errors during high-resolution LSB processing
# and PBKDF2-HMAC-SHA256 key derivation under constrained cloud vCPU.
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))

# Memory Management & Worker Lifecycle
# Automatically restart workers after serving requests to prevent memory leaks from Pillow
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "50"))

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")
capture_output = True
enable_stdio_inheritance = True

# Process Naming
proc_name = "stegoshield_production"
