/**
 * StegoShield Shared Application JavaScript
 * Global notifications, mobile menu toggle, clipboard helper.
 */

// Toast notification helper
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type === 'error' ? 'toast-error' : (type === 'success' ? 'toast-success' : '')}`;
  
  const icon = type === 'error' ? '✕' : (type === 'success' ? '✓' : 'ℹ');
  toast.innerHTML = `<span style="font-weight: bold;">${icon}</span> <span>${escapeHtml(message)}</span>`;
  
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// Format byte sizes into readable string (e.g. 1.8 KB)
function formatBytes(bytes, decimals = 1) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// HTML escape helper
function escapeHtml(text) {
  if (!text) return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.toString().replace(/[&<>"']/g, m => map[m]);
}

// Copy to clipboard utility
async function copyToClipboard(text, btnElement) {
  try {
    await navigator.clipboard.writeText(text);
    if (btnElement) {
      const originalHtml = btnElement.innerHTML;
      btnElement.innerHTML = '✓ Copied!';
      btnElement.classList.add('btn-emerald');
      setTimeout(() => {
        btnElement.innerHTML = originalHtml;
        btnElement.classList.remove('btn-emerald');
      }, 2000);
    }
    showToast('Message copied to clipboard', 'success');
  } catch (err) {
    showToast('Failed to copy to clipboard', 'error');
  }
}

// Initialize UI, PWA installation, and connectivity listeners
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.mobile-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
    });
  }

  // PWA Install Event Management
  let deferredPrompt = null;
  const installBtn = document.getElementById('pwa-install-btn');
  const heroInstallBtn = document.getElementById('pwa-hero-install-btn');
  const iosModal = document.getElementById('ios-install-modal');
  const iosCloseBtn = document.getElementById('ios-modal-close-btn');

  function showInstallButtons() {
    if (installBtn) installBtn.style.display = 'inline-flex';
    if (heroInstallBtn) heroInstallBtn.style.display = 'inline-flex';
  }

  function hideInstallButtons() {
    if (installBtn) installBtn.style.display = 'none';
    if (heroInstallBtn) heroInstallBtn.style.display = 'none';
  }

  // Check if running in standalone mode (already installed)
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                       window.navigator.standalone === true;

  // Check if user is on iOS
  const isIos = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

  if (!isStandalone) {
    // 1. Android / Chromium Desktop
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      showInstallButtons();
    });

    // 2. iOS Safari (Show install button to trigger instructions)
    if (isIos) {
      showInstallButtons();
    }
  }

  async function triggerInstallFlow() {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        hideInstallButtons();
      }
      deferredPrompt = null;
    } else if (isIos && iosModal) {
      iosModal.style.display = 'flex';
    } else {
      showToast('To install, use your browser menu and choose "Add to Home Screen" or "Install".', 'info');
    }
  }

  if (installBtn) installBtn.addEventListener('click', triggerInstallFlow);
  if (heroInstallBtn) heroInstallBtn.addEventListener('click', triggerInstallFlow);

  if (iosCloseBtn && iosModal) {
    iosCloseBtn.addEventListener('click', () => {
      iosModal.style.display = 'none';
    });
  }

  // App Installed Event
  window.addEventListener('appinstalled', () => {
    hideInstallButtons();
    deferredPrompt = null;
    showToast('StegoShield installed successfully!', 'success');
  });

  // Online / Offline Connectivity Detection
  const offlineBanner = document.getElementById('offline-banner');

  function updateOnlineStatus() {
    if (navigator.onLine) {
      if (offlineBanner) offlineBanner.style.display = 'none';
    } else {
      if (offlineBanner) offlineBanner.style.display = 'block';
      showToast('You are currently offline. Cached pages remain accessible.', 'info');
    }
  }

  window.addEventListener('online', () => {
    updateOnlineStatus();
    showToast('Network connection restored.', 'success');
  });

  window.addEventListener('offline', updateOnlineStatus);
  updateOnlineStatus();
});
