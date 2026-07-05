/**
 * Results page JavaScript
 * Reads diagnosis data from sessionStorage and populates all result cards.
 */

'use strict';

// ── DOM References ───────────────────────────────────────────
const noResults          = document.getElementById('no-results');
const resultsMain        = document.getElementById('results-main');
const reportIdBadge      = document.getElementById('report-id-badge');
const errorTitleDisplay  = document.getElementById('error-title-display');
const confidenceBar      = document.getElementById('confidence-bar');
const confidenceLabel    = document.getElementById('confidence-label');
const confidenceDisplay  = document.getElementById('confidence-score-display');
const errorSummaryText   = document.getElementById('error-summary-text');
const rootCauseText      = document.getElementById('root-cause-text');
const recommendedFixText = document.getElementById('recommended-fix-text');
const visionMetaGrid     = document.getElementById('vision-meta-grid');
const stacktraceContainer = document.getElementById('stacktrace-container');
const stacktraceText     = document.getElementById('stacktrace-text');
const stepsList          = document.getElementById('steps-list');
const tipsList           = document.getElementById('tips-list');
const relatedErrorsTags  = document.getElementById('related-errors-tags');
const retrievedList      = document.getElementById('retrieved-list');
const downloadPdfBtn     = document.getElementById('download-pdf-btn');
const viewJsonBtn        = document.getElementById('view-json-btn');
const jsonModal          = document.getElementById('json-modal');
const jsonOutput         = document.getElementById('json-output');
const modalCloseBtn      = document.getElementById('modal-close-btn');
const copyJsonBtn        = document.getElementById('copy-json-btn');

// ── Load Data ────────────────────────────────────────────────
const rawData = sessionStorage.getItem('diagnosisResult');

if (!rawData) {
  noResults.style.display = 'block';
} else {
  try {
    const data = JSON.parse(rawData);
    populateResults(data);
    resultsMain.style.display = 'block';
  } catch (e) {
    noResults.style.display = 'block';
    console.error('Failed to parse diagnosis data:', e);
  }
}

// ── Populate ─────────────────────────────────────────────────
function populateResults(data) {
  const { report_id, vision_analysis, retrieved_errors, diagnosis, pdf_url } = data;

  // Report ID Badge
  reportIdBadge.textContent = `Report ID: ${report_id}`;

  // Title
  const title = vision_analysis?.error_title || 'Error Analysis';
  errorTitleDisplay.textContent = title;
  document.title = `${title} — ErrorScope AI`;

  // Confidence
  const score = diagnosis?.confidence_score ?? 0;
  const pct = Math.round(score * 100);
  setTimeout(() => {
    confidenceBar.style.width = `${pct}%`;
    if (score >= 0.8) {
      confidenceBar.style.background = 'linear-gradient(90deg, #34d399, #22d3ee)';
      confidenceLabel.textContent = 'High Confidence';
      confidenceLabel.style.color = 'var(--c-success)';
    } else if (score >= 0.5) {
      confidenceBar.style.background = 'linear-gradient(90deg, #fbbf24, #f59e0b)';
      confidenceLabel.textContent = 'Medium Confidence';
      confidenceLabel.style.color = 'var(--c-warning)';
    } else {
      confidenceBar.style.background = 'linear-gradient(90deg, #f87171, #ef4444)';
      confidenceLabel.textContent = 'Low Confidence';
      confidenceLabel.style.color = 'var(--c-error)';
    }
    confidenceDisplay.textContent = `${pct}%`;
  }, 300);

  // Error Summary
  errorSummaryText.textContent = diagnosis?.error_summary || '—';

  // Root Cause
  rootCauseText.textContent = diagnosis?.root_cause || '—';

  // Recommended Fix
  recommendedFixText.textContent = diagnosis?.recommended_fix || '—';

  // Vision Meta
  const vision = vision_analysis || {};
  const metaItems = [
    { label: 'Language',    value: vision.language    || '—' },
    { label: 'Framework',   value: vision.framework   || '—' },
    { label: 'Environment', value: vision.environment || '—' },
    { label: 'Error',       value: vision.error_title || '—' },
  ];
  visionMetaGrid.innerHTML = metaItems.map(m => `
    <div class="meta-item">
      <div class="meta-label">${escHtml(m.label)}</div>
      <div class="meta-value">${escHtml(m.value)}</div>
    </div>
  `).join('');

  if (vision.raw_stacktrace) {
    stacktraceContainer.style.display = 'block';
    stacktraceText.textContent = vision.raw_stacktrace;
  }

  // Step-by-step solution
  const steps = diagnosis?.step_by_step_solution || [];
  stepsList.innerHTML = steps.length
    ? steps.map(s => `<li>${escHtml(s)}</li>`).join('')
    : '<li>No steps provided.</li>';

  // Prevention tips
  const tips = diagnosis?.prevention_tips || [];
  tipsList.innerHTML = tips.length
    ? tips.map(t => `<li>${escHtml(t)}</li>`).join('')
    : '<li>No tips provided.</li>';

  // Related errors
  const related = diagnosis?.related_errors || [];
  relatedErrorsTags.innerHTML = related.length
    ? related.map(r => `<span class="error-tag">${escHtml(r)}</span>`).join('')
    : '<span style="color:var(--c-text-3);font-size:0.875rem;">None identified.</span>';

  // Retrieved KB entries
  const retrieved = retrieved_errors || [];
  retrievedList.innerHTML = retrieved.length
    ? retrieved.map(e => buildKBEntry(e)).join('')
    : '<p style="color:var(--c-text-3);font-size:0.875rem;">No similar errors retrieved — FAISS index may need rebuilding.</p>';

  // PDF Download
  if (pdf_url) {
    downloadPdfBtn.onclick = () => { window.open(pdf_url, '_blank'); };
    downloadPdfBtn.disabled = false;
  } else {
    downloadPdfBtn.disabled = true;
    downloadPdfBtn.title = 'PDF generation failed';
  }

  // JSON Viewer
  jsonOutput.textContent = JSON.stringify(data, null, 2);
}

function buildKBEntry(entry) {
  const simPct = Math.round((entry.similarity_score ?? 0) * 100);
  return `
    <div class="kb-entry">
      <div class="kb-entry-header">
        <span class="kb-entry-name">${escHtml(entry.error_name || 'Unknown')}</span>
        <span class="kb-similarity">${simPct}% match</span>
      </div>
      <div class="kb-entry-desc">${escHtml(entry.description || '')}</div>
      ${entry.solution ? `<div class="kb-entry-solution">💡 ${escHtml(entry.solution.slice(0, 120))}${entry.solution.length > 120 ? '…' : ''}</div>` : ''}
    </div>
  `;
}

// ── JSON Modal ────────────────────────────────────────────────
viewJsonBtn?.addEventListener('click', () => {
  jsonModal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
});
modalCloseBtn?.addEventListener('click', closeModal);
jsonModal?.addEventListener('click', (e) => {
  if (e.target === jsonModal) closeModal();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});

function closeModal() {
  jsonModal.style.display = 'none';
  document.body.style.overflow = '';
}

copyJsonBtn?.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(jsonOutput.textContent);
    copyJsonBtn.textContent = 'Copied!';
    setTimeout(() => { copyJsonBtn.textContent = 'Copy JSON'; }, 2000);
  } catch {
    copyJsonBtn.textContent = 'Failed';
  }
});

// ── HTML Escape ───────────────────────────────────────────────
function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
