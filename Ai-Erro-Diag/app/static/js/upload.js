/**
 * Upload page JavaScript
 * Handles: drag-and-drop, file selection, preview, upload + diagnosis pipeline call.
 */

'use strict';

// ── DOM References ───────────────────────────────────────────
const dropZone       = document.getElementById('drop-zone');
const fileInput      = document.getElementById('file-input');
const dropContent    = document.getElementById('drop-zone-content');
const dropPreview    = document.getElementById('drop-zone-preview');
const previewImg     = document.getElementById('preview-img');
const previewName    = document.getElementById('preview-filename');
const previewSize    = document.getElementById('preview-filesize');
const removeBtn      = document.getElementById('remove-btn');
const diagnoseBtn    = document.getElementById('diagnose-btn');
const btnText        = document.getElementById('btn-text');
const btnSpinner     = document.getElementById('btn-spinner');
const errorAlert     = document.getElementById('error-alert');
const errorMsg       = document.getElementById('error-message');
const loadingOverlay = document.getElementById('loading-overlay');

// Loading step elements
const steps = {
  vision:    document.getElementById('step-vision'),
  embed:     document.getElementById('step-embed'),
  faiss:     document.getElementById('step-faiss'),
  diagnosis: document.getElementById('step-diagnosis'),
  pdf:       document.getElementById('step-pdf'),
};

// ── State ────────────────────────────────────────────────────
let selectedFile = null;

// ── Allowed types & max size ─────────────────────────────────
const ALLOWED_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);
const ALLOWED_EXTENSIONS = new Set(['.jpg', '.jpeg', '.png', '.webp']);
const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

// ── Utility ──────────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}

function getExtension(filename) {
  const idx = filename.lastIndexOf('.');
  return idx >= 0 ? filename.slice(idx).toLowerCase() : '';
}

// ── Validation ───────────────────────────────────────────────
function validateFile(file) {
  if (!file) return 'No file selected.';
  const ext = getExtension(file.name);
  if (!ALLOWED_EXTENSIONS.has(ext) && !ALLOWED_TYPES.has(file.type)) {
    return `Unsupported file type "${ext}". Please upload PNG, JPG, JPEG, or WEBP.`;
  }
  if (file.size > MAX_SIZE_BYTES) {
    return `File size ${formatBytes(file.size)} exceeds the 10 MB limit.`;
  }
  if (file.size === 0) return 'The selected file is empty.';
  return null;
}

// ── Show / Hide Error ─────────────────────────────────────────
function showError(message) {
  errorMsg.textContent = message;
  errorAlert.style.display = 'flex';
}
function hideError() {
  errorAlert.style.display = 'none';
}

// ── File Preview ──────────────────────────────────────────────
function showPreview(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewName.textContent = file.name.length > 30 ? file.name.slice(0, 27) + '...' : file.name;
    previewSize.textContent = formatBytes(file.size);
    dropContent.style.display = 'none';
    dropPreview.style.display = 'block';
  };
  reader.readAsDataURL(file);
}

function clearPreview() {
  previewImg.src = '';
  previewName.textContent = '';
  previewSize.textContent = '';
  dropContent.style.display = 'block';
  dropPreview.style.display = 'none';
  selectedFile = null;
  diagnoseBtn.disabled = true;
  fileInput.value = '';
  hideError();
}

// ── File Selection ────────────────────────────────────────────
function handleFileSelect(file) {
  if (!file) return;
  hideError();
  const err = validateFile(file);
  if (err) {
    showError(err);
    return;
  }
  selectedFile = file;
  showPreview(file);
  diagnoseBtn.disabled = false;
}

// ── Drop Zone Events ──────────────────────────────────────────
dropZone.addEventListener('click', (e) => {
  if (e.target === removeBtn || removeBtn.contains(e.target)) return;
  fileInput.click();
});
dropZone.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); }
});

dropZone.addEventListener('dragenter', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragover',  (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', (e) => {
  if (!dropZone.contains(e.relatedTarget)) dropZone.classList.remove('dragover');
});
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  handleFileSelect(file);
});

fileInput.addEventListener('change', () => {
  handleFileSelect(fileInput.files[0]);
});

removeBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  clearPreview();
});

// ── Loading Simulation ────────────────────────────────────────
const STEP_KEYS = ['vision', 'embed', 'faiss', 'diagnosis', 'pdf'];
const STEP_DELAYS = [0, 3500, 7000, 10500, 16000]; // approximate ms

let stepTimers = [];

function startLoadingSteps() {
  STEP_KEYS.forEach((key) => {
    steps[key].classList.remove('active', 'done');
  });

  stepTimers = STEP_KEYS.map((key, i) => {
    return setTimeout(() => {
      // Mark previous as done
      if (i > 0) {
        steps[STEP_KEYS[i - 1]].classList.remove('active');
        steps[STEP_KEYS[i - 1]].classList.add('done');
      }
      steps[key].classList.add('active');
    }, STEP_DELAYS[i]);
  });
}

function stopLoadingSteps() {
  stepTimers.forEach(clearTimeout);
  stepTimers = [];
}

// ── Diagnose ──────────────────────────────────────────────────
diagnoseBtn.addEventListener('click', async () => {
  if (!selectedFile) return;
  hideError();

  // Show loading
  btnText.style.display = 'none';
  btnSpinner.style.display = 'inline-flex';
  diagnoseBtn.disabled = true;
  loadingOverlay.style.display = 'flex';
  startLoadingSteps();

  try {
    const formData = new FormData();
    formData.append('file', selectedFile);

    const response = await fetch('/api/v1/diagnose', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();

    // Store in sessionStorage for results page
    sessionStorage.setItem('diagnosisResult', JSON.stringify(data));

    // Mark all steps done
    stopLoadingSteps();
    STEP_KEYS.forEach((key) => {
      steps[key].classList.remove('active');
      steps[key].classList.add('done');
    });

    // Brief pause then navigate
    await new Promise(r => setTimeout(r, 600));
    window.location.href = '/results';

  } catch (err) {
    stopLoadingSteps();
    loadingOverlay.style.display = 'none';
    btnText.style.display = 'inline-flex';
    btnSpinner.style.display = 'none';
    diagnoseBtn.disabled = false;
    showError(`Analysis failed: ${err.message}`);
  }
});

// ── Health Check ──────────────────────────────────────────────
(async function checkHealth() {
  try {
    const res = await fetch('/api/v1/health');
    const data = await res.json();
    const dot = document.querySelector('.health-dot');
    if (dot) {
      dot.style.background = data.status === 'ok' ? 'var(--c-success)' : 'var(--c-error)';
    }
  } catch {
    const dot = document.querySelector('.health-dot');
    if (dot) dot.style.background = 'var(--c-error)';
  }
})();
