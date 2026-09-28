/**
 * StegoShield Hide Message Module
 * Multi-step wizard, live capacity calculation, password strength meter, generation pipeline.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const browseBtn = document.getElementById('browse-btn');
  const uploadPlaceholder = document.getElementById('upload-placeholder');
  const previewContainer = document.getElementById('preview-container');
  const previewImage = document.getElementById('preview-image');
  const previewName = document.getElementById('preview-name');
  const previewSize = document.getElementById('preview-size');
  const previewDimensions = document.getElementById('preview-dimensions');
  const removeImageBtn = document.getElementById('remove-image-btn');

  const messageInput = document.getElementById('message-input');
  const charCounter = document.getElementById('char-counter');
  const capacityProgress = document.getElementById('capacity-progress');
  const capacityUsedText = document.getElementById('capacity-used');
  const capacityAvailableText = document.getElementById('capacity-available');
  const capacityStatusText = document.getElementById('capacity-status');

  const passwordToggle = document.getElementById('password-toggle');
  const passwordFields = document.getElementById('password-fields');
  const passwordInput = document.getElementById('password-input');
  const confirmPasswordInput = document.getElementById('confirm-password-input');
  const strengthBars = document.querySelectorAll('.strength-bar');
  const strengthLabel = document.getElementById('strength-label');

  const submitBtn = document.getElementById('submit-btn');
  const progressContainer = document.getElementById('progress-container');
  const progressStage = document.getElementById('progress-stage');

  const resultContainer = document.getElementById('result-container');
  const resultPreview = document.getElementById('result-preview');
  const downloadBtn = document.getElementById('download-btn');
  const hideAnotherBtn = document.getElementById('hide-another-btn');
  const resultMetaDim = document.getElementById('result-meta-dim');
  const resultMetaPayload = document.getElementById('result-meta-payload');
  const resultMetaSecurity = document.getElementById('result-meta-security');
  const resultMetaUsed = document.getElementById('result-meta-used');

  const stepIndicators = document.querySelectorAll('.wizard-step');

  // State
  let currentFile = null;
  let imageWidth = 0;
  let imageHeight = 0;
  let usableCapacityBytes = 0;
  const HEADER_SIZE = 48; // 48 bytes StegoShield header

  // Browse button trigger
  if (browseBtn && fileInput) {
    browseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    // Drag & drop handlers
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFileSelection(files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        handleFileSelection(fileInput.files[0]);
      }
    });
  }

  // Handle uploaded file
  function handleFileSelection(file) {
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp', 'image/webp'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(png|jpg|jpeg|bmp|webp)$/i)) {
      showToast('Please upload a supported image (PNG, JPG, JPEG, BMP).', 'error');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      showToast('Image exceeds 10 MB maximum upload limit.', 'error');
      return;
    }

    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        imageWidth = img.naturalWidth;
        imageHeight = img.naturalHeight;

        previewImage.src = e.target.result;
        previewName.textContent = file.name;
        previewSize.textContent = formatBytes(file.size);
        previewDimensions.textContent = `${imageWidth} × ${imageHeight} px`;

        // Calculate usable capacity (3 bits per pixel)
        const totalCapacityBytes = Math.floor((imageWidth * imageHeight * 3) / 8);
        usableCapacityBytes = Math.max(0, totalCapacityBytes - HEADER_SIZE);

        capacityAvailableText.textContent = formatBytes(usableCapacityBytes);
        updateCapacityMetrics();

        uploadPlaceholder.style.display = 'none';
        previewContainer.style.display = 'flex';
        updateStepState(1, true);
        checkFormReadiness();
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  }

  // Remove uploaded image
  if (removeImageBtn) {
    removeImageBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      resetUpload();
    });
  }

  function resetUpload() {
    currentFile = null;
    imageWidth = 0;
    imageHeight = 0;
    usableCapacityBytes = 0;
    fileInput.value = '';
    previewImage.src = '';
    uploadPlaceholder.style.display = 'block';
    previewContainer.style.display = 'none';
    updateStepState(1, false);
    updateCapacityMetrics();
    checkFormReadiness();
  }

  // Message input & capacity updates
  if (messageInput) {
    messageInput.addEventListener('input', () => {
      const text = messageInput.value;
      const count = text.length;
      charCounter.textContent = `${count} / 50000`;
      updateStepState(2, count > 0);
      updateCapacityMetrics();
      checkFormReadiness();
    });
  }

  // Calculate payload size and update gauge
  function updateCapacityMetrics() {
    if (!messageInput) return;
    const text = messageInput.value;
    const encoder = new TextEncoder();
    let rawPayloadBytes = encoder.encode(text).length;

    // If password enabled, add PBKDF2/AES-GCM envelope overhead: 16 salt + 12 nonce + 16 tag = 44 bytes
    const isEncrypted = passwordToggle && passwordToggle.checked;
    if (isEncrypted && rawPayloadBytes > 0) {
      rawPayloadBytes += 44;
    }

    capacityUsedText.textContent = formatBytes(rawPayloadBytes);

    if (usableCapacityBytes === 0) {
      capacityProgress.style.width = '0%';
      capacityStatusText.textContent = 'Upload an image first';
      capacityStatusText.style.color = 'var(--text-dim)';
      return;
    }

    const percentage = Math.min(100, (rawPayloadBytes / usableCapacityBytes) * 100);
    capacityProgress.style.width = `${percentage}%`;

    if (rawPayloadBytes > usableCapacityBytes) {
      capacityProgress.classList.add('danger');
      capacityStatusText.textContent = '✕ Payload too large for image';
      capacityStatusText.style.color = 'var(--accent-rose)';
    } else if (rawPayloadBytes > 0) {
      capacityProgress.classList.remove('danger');
      capacityStatusText.textContent = '✓ Fits safely';
      capacityStatusText.style.color = 'var(--accent-emerald)';
    } else {
      capacityProgress.classList.remove('danger');
      capacityStatusText.textContent = 'Awaiting message';
      capacityStatusText.style.color = 'var(--text-dim)';
    }
  }

  // Password toggle
  if (passwordToggle) {
    passwordToggle.addEventListener('change', () => {
      passwordFields.style.display = passwordToggle.checked ? 'block' : 'none';
      updateCapacityMetrics();
      checkFormReadiness();
    });
  }

  // Password strength checker
  if (passwordInput) {
    passwordInput.addEventListener('input', () => {
      evaluatePasswordStrength(passwordInput.value);
      checkFormReadiness();
    });
  }

  if (confirmPasswordInput) {
    confirmPasswordInput.addEventListener('input', () => {
      checkFormReadiness();
    });
  }

  function evaluatePasswordStrength(password) {
    let score = 0;
    if (!password) {
      resetStrengthBars();
      return;
    }

    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
    if (/[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password)) score++;

    strengthBars.forEach((bar, idx) => {
      bar.className = 'strength-bar';
      if (idx < score) {
        if (score === 1) bar.classList.add('weak');
        else if (score === 2) bar.classList.add('fair');
        else if (score === 3) bar.classList.add('strong');
        else if (score >= 4) bar.classList.add('very-strong');
      }
    });

    const labels = ['Too Short', 'Weak', 'Fair', 'Strong', 'Very Strong (Recommended)'];
    strengthLabel.textContent = labels[score] || 'Too Short';
  }

  function resetStrengthBars() {
    strengthBars.forEach(bar => bar.className = 'strength-bar');
    strengthLabel.textContent = 'Enter password to check strength';
  }

  // Form validity check
  function checkFormReadiness() {
    let isValid = true;

    // Check image
    if (!currentFile || usableCapacityBytes <= 0) isValid = false;

    // Check message
    const msg = messageInput ? messageInput.value.trim() : '';
    if (!msg) isValid = false;

    // Check capacity
    const encoder = new TextEncoder();
    let totalBytes = encoder.encode(msg).length + (passwordToggle.checked ? 44 : 0);
    if (totalBytes > usableCapacityBytes) isValid = false;

    // Check password if enabled
    if (passwordToggle && passwordToggle.checked) {
      const p1 = passwordInput.value;
      const p2 = confirmPasswordInput.value;
      if (!p1 || p1 !== p2) {
        isValid = false;
      }
      updateStepState(3, p1.length > 0 && p1 === p2);
    } else {
      updateStepState(3, true);
    }

    if (submitBtn) {
      submitBtn.disabled = !isValid;
    }
  }

  function updateStepState(stepNumber, isCompleted) {
    const stepEl = document.querySelector(`.wizard-step[data-step="${stepNumber}"]`);
    if (stepEl) {
      if (isCompleted) {
        stepEl.classList.add('completed');
      } else {
        stepEl.classList.remove('completed');
      }
    }
  }

  // Form Submission / Generation
  const form = document.getElementById('hide-form');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (!currentFile) {
        showToast('Please upload an image.', 'error');
        return;
      }

      const message = messageInput.value.trim();
      if (!message) {
        showToast('Please enter a message.', 'error');
        return;
      }

      const usePassword = passwordToggle.checked;
      const password = passwordInput.value;
      const confirmPassword = confirmPasswordInput.value;

      if (usePassword) {
        if (!password) {
          showToast('Please enter an encryption password.', 'error');
          return;
        }
        if (password !== confirmPassword) {
          showToast('Passwords do not match. Please verify.', 'error');
          return;
        }
      }

      // UI state transition
      form.style.display = 'none';
      progressContainer.style.display = 'block';
      updateStepState(4, false);

      const stages = [
        "Preparing image buffer...",
        usePassword ? "Deriving 256-bit encryption key (PBKDF2)..." : "Encoding UTF-8 payload...",
        usePassword ? "Encrypting message with AES-256-GCM..." : "Computing SHA-256 integrity checksum...",
        "Embedding structured binary header into RGB LSBs...",
        "Verifying output pixel checksum...",
        "Generating lossless PNG..."
      ];

      let stageIdx = 0;
      const stageInterval = setInterval(() => {
        if (stageIdx < stages.length) {
          progressStage.textContent = stages[stageIdx++];
        }
      }, 350);

      const formData = new FormData();
      formData.append('image', currentFile);
      formData.append('message', message);
      formData.append('use_password', usePassword);
      if (usePassword) {
        formData.append('password', password);
      }

      try {
        const response = await fetch('/api/hide', {
          method: 'POST',
          body: formData
        });

        clearInterval(stageInterval);
        const data = await response.json();

        if (response.ok && data.success) {
          progressStage.textContent = "✓ Stego image successfully generated!";
          setTimeout(() => {
            progressContainer.style.display = 'none';
            displayResult(data);
          }, 600);
        } else {
          progressContainer.style.display = 'none';
          form.style.display = 'block';
          showToast(data.error || 'Failed to hide message in image.', 'error');
        }
      } catch (err) {
        clearInterval(stageInterval);
        progressContainer.style.display = 'none';
        form.style.display = 'block';
        showToast('Network or server error during image generation.', 'error');
      }
    });
  }

  const wipeServerBtn = document.getElementById('wipe-server-btn');
  let currentOutputFilename = null;

  // Display result
  function displayResult(data) {
    currentOutputFilename = data.filename;
    resultPreview.src = data.preview_url;
    downloadBtn.href = data.download_url;

    if (wipeServerBtn) {
      wipeServerBtn.disabled = false;
      wipeServerBtn.innerHTML = '<span>🗑️ Shred Server Copy</span>';
      wipeServerBtn.classList.remove('btn-emerald');
    }

    resultMetaDim.textContent = `${data.metadata.width} × ${data.metadata.height} px`;
    resultMetaPayload.textContent = formatBytes(data.metadata.payload_bytes);
    resultMetaSecurity.textContent = data.metadata.is_encrypted ? 'AES-256-GCM Encrypted' : 'Plaintext + SHA-256';
    resultMetaUsed.textContent = `${data.metadata.capacity_used_percent}%`;

    resultContainer.style.display = 'block';
    updateStepState(4, true);
    showToast('Stego image generated successfully!', 'success');
  }

  // Secure Server Shred Handler
  if (wipeServerBtn) {
    wipeServerBtn.addEventListener('click', async () => {
      if (!currentOutputFilename) return;
      try {
        const resp = await fetch(`/api/wipe/${currentOutputFilename}`, { method: 'POST' });
        const res = await resp.json();
        if (res.success) {
          wipeServerBtn.disabled = true;
          wipeServerBtn.innerHTML = '<span>✓ Server Copy Shredded</span>';
          wipeServerBtn.classList.add('btn-emerald');
          showToast('Image permanently shredded from server storage.', 'success');
        } else {
          showToast(res.error || 'Failed to shred file.', 'error');
        }
      } catch (e) {
        showToast('Unable to contact server to shred file.', 'error');
      }
    });
  }

  // Hide another message reset
  if (hideAnotherBtn) {
    hideAnotherBtn.addEventListener('click', () => {
      currentOutputFilename = null;
      resultContainer.style.display = 'none';
      form.style.display = 'block';
      resetUpload();
      messageInput.value = '';
      charCounter.textContent = '0 / 50000';
      if (passwordToggle) passwordToggle.checked = false;
      if (passwordFields) passwordFields.style.display = 'none';
      if (passwordInput) passwordInput.value = '';
      if (confirmPasswordInput) confirmPasswordInput.value = '';
      resetStrengthBars();
      stepIndicators.forEach(step => step.classList.remove('completed'));
    });
  }
});

