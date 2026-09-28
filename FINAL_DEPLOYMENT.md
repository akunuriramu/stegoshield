# StegoShield Production Deployment Guide

This guide provides the authoritative instructions for deploying **StegoShield** to a public cloud server so that the web application runs continuously 24/7 without requiring your local PC.

---

## 1. System & Architecture Overview

StegoShield is fully containerized and cloud-ready for immediate PaaS deployment (Render, Railway, Fly.io):

| Component | Production Specification |
| :--- | :--- |
| **Framework** | Flask 3.1+ (Python 3.11.9) |
| **WSGI Server** | Gunicorn 21.2+ with `gthread` worker model |
| **Cryptography** | AES-256-GCM + PBKDF2-HMAC-SHA256 (600,000 rounds) |
| **Steganography** | Lossless LSB (Least Significant Bit) with 48-byte binary header |
| **Client Model** | Responsive PWA (Progressive Web App) with Service Worker & Manifest |
| **Storage Architecture** | Zero-retention ephemeral storage with automatic daemon shredder (300s max age) & client on-demand shredding |
| **Security Layer** | Strict CSP, HSTS, X-Content-Type nosniff, Decompression Bomb Mitigation (`MAX_IMAGE_PIXELS = 25M`) |
| **Health Monitoring** | Built-in `/health` and `/api/health` probes |

---

## 2. Pre-Deployment Verification

All 38 test suites pass with zero regressions:
```bash
python -m unittest discover -s tests -v
# Ran 38 tests in 2.218s -> OK
```

Verified Production Configuration Files:
- `render.yaml` - Render Blueprint infrastructure-as-code
- `Procfile` - Process entrypoint for cloud PaaS (`web: gunicorn --config gunicorn.conf.py app:app`)
- `gunicorn.conf.py` - High-performance Gunicorn configuration with 120s timeout and dynamic PORT binding
- `runtime.txt` - Fixed Python version (`python-3.11.9`)
- `requirements.txt` - Production dependencies with version pins

---

## 3. Step-by-Step Cloud Deployment to Render

### Step 1: Commit Local Code to Git

In your project directory (`C:\Users\tiven\Downloads\cineVault\Is project real`), run:

```bash
git add .
git commit -m "feat: complete production cloud readiness transformation"
```

### Step 2: Push to GitHub

1. Open your browser and go to [GitHub - New Repository](https://github.com/new).
2. Create a new repository named `stegoshield` (can be **Public** or **Private**).
3. Do **not** initialize with README or .gitignore (they already exist in your local project).
4. Run the following commands in your project terminal:

```bash
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/stegoshield.git
git branch -M main
git push -u origin main
```

*(Enter your GitHub credentials or Personal Access Token when prompted)*

---

### Step 3: Deploy on Render

#### Option A: Automated Blueprint Deployment (Recommended)
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click the **New +** button in the top navigation bar.
3. Select **Blueprint**.
4. Connect your GitHub account and select your `stegoshield` repository.
5. Render will automatically read the `render.yaml` file from the repository and configure:
   - **Service Name**: `stegoshield`
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn.conf.py app:app`
   - **Health Check Path**: `/health`
   - **Auto-generated SECRET_KEY**
6. Click **Apply**. Render will automatically provision the service, build dependencies, and launch your application.

#### Option B: Manual Web Service Setup
If you prefer manual configuration:
1. In Render Dashboard, click **New +** &rarr; **Web Service**.
2. Select your `stegoshield` repository.
3. Configure the settings:
   - **Name**: `stegoshield`
   - **Region**: Oregon (US West) or closest region
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn.conf.py app:app`
   - **Instance Type**: Free
4. Under **Advanced** &rarr; **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.11.9`
   - `FLASK_DEBUG`: `False`
   - `GUNICORN_TIMEOUT`: `120`
   - `SECRET_KEY`: *(Click "Generate" or enter a secure random string)*
5. Under **Health Check Path**, enter: `/health`
6. Click **Create Web Service**.

---

## 4. Live Verification Checklist

Once Render finishes deploying (typically 1–3 minutes), your service will be assigned a public URL (e.g. `https://stegoshield.onrender.com`).

Verify the live deployment:

1. **Health Check Probe**:
   Visit `https://<YOUR_APP>.onrender.com/health` in your browser.
   It should return:
   ```json
   {
     "service": "stegoshield",
     "status": "healthy",
     "storage": "operational",
     "version": "1.0.0"
   }
   ```

2. **Security Headers Validation**:
   Inspect response headers using browser DevTools or `curl -I https://<YOUR_APP>.onrender.com`.
   Confirm presence of:
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: SAMEORIGIN`
   - `Content-Security-Policy`

3. **End-to-End Steganography Test**:
   - Navigate to `/hide`
   - Upload any sample PNG or JPG cover image
   - Type a secret message and enable password protection
   - Click **Generate Stego Image**
   - Click **Download Stego PNG**
   - Click **Shred Server Copy** to verify immediate volatile deletion
   - Navigate to `/extract`
   - Upload the downloaded PNG and enter the password
   - Verify the recovered plaintext matches 100%

4. **PWA Standalone Installation**:
   - On Desktop (Chrome/Edge): Click the "Install App" button in the navigation bar.
   - On iOS (Safari): Tap Share &rarr; "Add to Home Screen".
   - Launch StegoShield from the home screen icon and verify full-screen standalone execution.

---

## 5. Keeping Free-Tier Cloud Services Warm (Optional)

On Render's Free tier, services spin down after 15 minutes of inactivity and take 30–50 seconds to wake on the next request.

To keep StegoShield warm 24/7 at no cost:
1. Register a free account at [UptimeRobot](https://uptimerobot.com) or [Cron-job.org](https://cron-job.org).
2. Create an **HTTP(s) Monitor** pointing to:
   ```
   https://<YOUR_APP>.onrender.com/health
   ```
3. Set the monitoring interval to **every 10 minutes**.
4. This keeps the application warm and provides automated downtime alerts.
