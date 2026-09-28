/**
 * StegoShield Extract Message Module
 * Upload, header detection, password modal prompt, decryption, and verified message reveal.
 */

document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('extract-dropzone');
  const fileInput = document.getElementById('extract-file-input');
  const browseBtn = document.getElementById('extract-browse-btn');
  const uploadPlaceholder = document.getElementById('extract-placeholder');
  const previewContainer = document.getElementById('extract-preview-container');
  const previewImage = document.getElementById('extract-preview-image');
  const previewName = document.getElementById('extract-preview-name');
  const previewSize = document.getElementById('extract-preview-size');
  const previewDimensions = document.getElementById('extract-preview-dimensions');
  const removeBtn = document.getElementById('extract-remove-btn');

  const extractBtn = document.getElementById('extract-submit-btn');
  const progressContainer = document.getElementById('extract-progress-container');
  const progressStage = document.getElementById('extract-progress-stage');

  const passwordModal = document.getElementById('password-modal');
  const modalPasswordInput = document.getElementById('modal-password-input');
  const modalSubmitBtn = document.getElementById('modal-submit-btn');
  const modalCancelBtn = document.getElementById('modal-cancel-btn');

  const resultContainer = document.getElementById('extract-result-container');
  const terminalMessage = document.getElementById('terminal-message');
  const copyBtn = document.getElementById('copy-message-btn');
  const clearBtn = document.getElementById('clear-message-btn');
  const extractAnotherBtn = document.getElementById('extract-another-btn');

  const metaSecurity = document.getElementById('meta-security');
  const metaChecksum = document.getElementById('meta-checksum');
  const metaSize = document.getElementById('meta-size');

  let currentFile = null;

  // Browse trigger
  if (browseBtn && fileInput) {
    browseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  // Drag & drop handlers
  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

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

  function handleFileSelection(file) {
    if (!file.name.match(/\.(png|bmp|jpg|jpeg|webp)$/i)) {
      showToast('Please upload a supported image file (PNG strongly recommended).', 'error');
      return;
    }

    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        previewImage.src = e.target.result;
        previewName.textContent = file.name;
        previewSize.textContent = formatBytes(file.size);
        previewDimensions.textContent = `${img.naturalWidth} × ${img.naturalHeight} px`;

        uploadPlaceholder.style.display = 'none';
        previewContainer.style.display = 'flex';
        extractBtn.disabled = false;
        resultContainer.style.display = 'none';
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  }

  // Remove image
  if (removeBtn) {
    removeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      resetExtraction();
    });
  }

  function resetExtraction() {
    currentFile = null;
    fileInput.value = '';
    previewImage.src = '';
    uploadPlaceholder.style.display = 'block';
    previewContainer.style.display = 'none';
    extractBtn.disabled = true;
    resultContainer.style.display = 'none';
    progressContainer.style.display = 'none';
  }

  // Extract button click
  if (extractBtn) {
    extractBtn.addEventListener('click', () => {
      if (!currentFile) return;
      executeExtraction();
    });
  }

  async function executeExtraction(password = null) {
    extractBtn.disabled = true;
    progressContainer.style.display = 'block';
    resultContainer.style.display = 'none';

    const stages = [
      "Reading image channels...",
      "Inspecting 48-byte StegoShield binary header...",
      "Validating magic bytes and version...",
      "Verifying SHA-256 integrity checksum...",
      password ? "Decrypting AES-256-GCM authenticated payload..." : "Decoding UTF-8 plaintext payload...",
      "Finalizing message verification..."
    ];

    let stageIdx = 0;
    const stageInterval = setInterval(() => {
      if (stageIdx < stages.length) {
        progressStage.textContent = stages[stageIdx++];
      }
    }, 280);

    const formData = new FormData();
    formData.append('image', currentFile);
    if (password) {
      formData.append('password', password);
    }

    try {
      const response = await fetch('/api/extract', {
        method: 'POST',
        body: formData
      });

      clearInterval(stageInterval);
      const data = await response.json();

      progressContainer.style.display = 'none';
      extractBtn.disabled = false;

      if (response.status === 401 && data.password_required) {
        // Password required modal
        openPasswordModal();
        return;
      }

      if (response.ok && data.success) {
        displayMessage(data);
      } else {
        showToast(data.error || 'Extraction failed.', 'error');
      }
    } catch (err) {
      clearInterval(stageInterval);
      progressContainer.style.display = 'none';
      extractBtn.disabled = false;
      showToast('An unexpected network or server error occurred.', 'error');
    }
  }

  // Display extracted message
  function displayMessage(data) {
    terminalMessage.textContent = data.message;
    metaSize.textContent = formatBytes(data.metadata.payload_bytes);
    metaSecurity.textContent = data.metadata.is_encrypted ? 'AES-256-GCM Encrypted' : 'Plaintext (SHA-256 Verified)';
    metaChecksum.textContent = data.metadata.checksum.substring(0, 16) + '...';

    resultContainer.style.display = 'block';
    showToast('Hidden message successfully extracted and verified!', 'success');
  }

  // Password modal management
  function openPasswordModal() {
    modalPasswordInput.value = '';
    passwordModal.style.display = 'flex';
    modalPasswordInput.focus();
  }

  function closePasswordModal() {
    passwordModal.style.display = 'none';
  }

  if (modalCancelBtn) {
    modalCancelBtn.addEventListener('click', closePasswordModal);
  }

  if (modalSubmitBtn) {
    modalSubmitBtn.addEventListener('click', () => {
      const pwd = modalPasswordInput.value.trim();
      if (!pwd) {
        showToast('Please enter the decryption password.', 'error');
        return;
      }
      closePasswordModal();
      executeExtraction(pwd);
    });
  }

  if (modalPasswordInput) {
    modalPasswordInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        modalSubmitBtn.click();
      } else if (e.key === 'Escape') {
        closePasswordModal();
      }
    });
  }

  // Copy message
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      copyToClipboard(terminalMessage.textContent, copyBtn);
    });
  }

  // Clear message
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      terminalMessage.textContent = '';
      resultContainer.style.display = 'none';
      showToast('Message cleared from screen.', 'info');
    });
  }

  // Extract another
  if (extractAnotherBtn) {
    extractAnotherBtn.addEventListener('click', () => {
      resetExtraction();
    });
  }
});
