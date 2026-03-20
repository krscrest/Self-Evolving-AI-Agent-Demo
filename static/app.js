// ===== State =====
let documentLoaded = false;
let isRunning = false;
const cycleData = {};
const promptVersions = [];

// ===== DOM Elements =====
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ===== Login =====
$('#login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = $('#username').value;
    const password = $('#password').value;
    const errorEl = $('#login-error');
    errorEl.classList.add('hidden');

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            $('#login-screen').classList.remove('active');
            $('#login-screen').classList.add('hidden');
            $('#dashboard-screen').classList.remove('hidden');
            $('#dashboard-screen').classList.add('active');
        } else {
            errorEl.textContent = data.detail || 'Invalid credentials';
            errorEl.classList.remove('hidden');
        }
    } catch (err) {
        errorEl.textContent = 'Connection error. Please try again.';
        errorEl.classList.remove('hidden');
    }
});

// ===== Logout =====
$('#logout-btn').addEventListener('click', async () => {
    await fetch('/api/logout', { method: 'POST' });
    location.reload();
});

// ===== Use Sample Document =====
$('#use-sample-btn').addEventListener('click', async () => {
    const btn = $('#use-sample-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Parsing with Azure Document Intelligence...';

    try {
        const res = await fetch('/api/use-sample', { method: 'POST' });
        const data = await res.json();
        if (res.ok && data.success) {
            documentLoaded = true;
            showDocumentStatus(data.message);
            $('#start-btn').disabled = false;
        } else {
            alert(data.detail || 'Failed to parse document');
        }
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>📋</span> Use Sample Certificate of Insurance';
    }
});

// ===== Upload Document =====
$('#file-upload').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    const btn = $('.upload-label');
    btn.style.opacity = '0.5';

    try {
        const res = await fetch('/api/upload-document', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (res.ok && data.success) {
            documentLoaded = true;
            showDocumentStatus(data.message);
            $('#start-btn').disabled = false;
        } else {
            alert(data.detail || 'Failed to parse document');
        }
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        btn.style.opacity = '1';
    }
});

function showDocumentStatus(message) {
    const statusBar = $('#document-status');
    statusBar.classList.remove('hidden');
    statusBar.querySelector('.status-text').textContent = message;
}

// ===== Start Optimization =====
$('#start-btn').addEventListener('click', () => {
    if (!documentLoaded || isRunning) return;
    startOptimization();
});

async function startOptimization() {
    isRunning = true;
    $('#start-btn').disabled = true;
    $('#start-btn').innerHTML = '<span class="spinner"></span> Optimizing...';

    // Show sections
    $('#progress-section').classList.remove('hidden');
    $('#cycles-section').classList.remove('hidden');
    $('#log-section').classList.remove('hidden');
    $('#prompt-evolution-section').classList.remove('hidden');

    // Reset
    for (let i = 0; i < 3; i++) {
        $(`#cycle-${i}`).classList.remove('active', 'completed');
        $(`#score-${i}`).textContent = '--';
        $(`#bar-${i}`).style.width = '0%';
        $(`#details-${i}`).classList.add('hidden');
    }
    $('#activity-log').innerHTML = '';
    $('#prompt-evolution').innerHTML = '';
    $('#progress-bar').style.width = '0%';
    $('#progress-label').textContent = 'Initializing...';
    $('#progress-score').textContent = '--/100';

    // Connect to SSE
    const eventSource = new EventSource('/api/run-optimization');

    eventSource.addEventListener('start', (e) => {
        const data = JSON.parse(e.data);
        addLog(data.message, 'info');
        addPromptVersion('v0 (Generic)', data.initial_prompt, null);
    });

    eventSource.addEventListener('cycle_start', (e) => {
        const data = JSON.parse(e.data);
        const cycle = data.cycle;
        $(`#cycle-${cycle}`).classList.add('active');
        $(`#prompt-${cycle}`).textContent = data.prompt;
        addLog(data.message, 'info');
        updateProgress(cycle, 'Running...');
    });

    eventSource.addEventListener('log', (e) => {
        const data = JSON.parse(e.data);
        const cls = data.step === 'optimize' ? 'optimize' : 'info';
        addLog(data.message, cls);
    });

    eventSource.addEventListener('summary', (e) => {
        const data = JSON.parse(e.data);
        const cycle = data.cycle;
        $(`#summary-${cycle}`).textContent = data.summary;
        cycleData[cycle] = cycleData[cycle] || {};
        cycleData[cycle].summary = data.summary;
        addLog(data.message, 'info');
    });

    eventSource.addEventListener('score', (e) => {
        const data = JSON.parse(e.data);
        const cycle = data.cycle;
        const scores = data.scores;
        const total = scores.total;

        // Update score display
        $(`#score-${cycle}`).textContent = total;
        $(`#score-${cycle}`).style.color = getScoreColor(total);

        // Animate score bar
        const bar = $(`#bar-${cycle}`);
        bar.style.width = `${total}%`;
        bar.className = 'score-bar ' + getScoreClass(total);

        // Update breakdown
        renderBreakdown(cycle, scores);

        // Update progress
        updateProgress(cycle, `Cycle ${cycle} scored ${total}/100`);
        $('#progress-score').textContent = `${total}/100`;
        $('#progress-score').style.color = getScoreColor(total);

        // Store data
        cycleData[cycle] = cycleData[cycle] || {};
        cycleData[cycle].scores = scores;

        addLog(data.message, 'success');

        // Mark card completed
        $(`#cycle-${cycle}`).classList.remove('active');
        $(`#cycle-${cycle}`).classList.add('completed');
    });

    eventSource.addEventListener('prompt_update', (e) => {
        const data = JSON.parse(e.data);
        const nextCycle = data.cycle + 1;
        addPromptVersion(`v${nextCycle} (After Cycle ${data.cycle} feedback)`, data.new_prompt, data.old_prompt);
        addLog(data.message, 'optimize');
    });

    eventSource.addEventListener('complete', (e) => {
        const data = JSON.parse(e.data);
        eventSource.close();
        isRunning = false;

        // Update progress bar to 100%
        $('#progress-bar').style.width = '100%';
        $('#progress-label').textContent = 'Optimization Complete!';

        // Show completion banner
        const banner = document.createElement('div');
        banner.className = 'completion-banner';
        banner.innerHTML = `
            <h2>✅ Self-Optimization Complete</h2>
            <div class="improvement">+${data.total_improvement} points</div>
            <p>${data.message}</p>
            <p style="margin-top: 8px; color: var(--accent-blue);">Score progression: ${data.score_progression.join(' → ')}</p>
        `;
        $('#progress-section').insertAdjacentElement('afterend', banner);

        addLog(data.message, 'success');

        // Reset start button
        $('#start-btn').innerHTML = '<span class="play-icon">▶</span> Run Again';
        $('#start-btn').disabled = false;
    });

    eventSource.onerror = () => {
        eventSource.close();
        isRunning = false;
        addLog('Connection lost. Please try again.', 'error');
        $('#start-btn').innerHTML = '<span class="play-icon">▶</span> Retry';
        $('#start-btn').disabled = false;
    };
}

// ===== Helpers =====

function addLog(message, type = '') {
    const log = $('#activity-log');
    const time = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.innerHTML = `<span class="log-time">[${time}]</span> ${escapeHtml(message)}`;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
}

function updateProgress(cycle, label) {
    const pct = ((cycle + 1) / 3 * 100).toFixed(0);
    $('#progress-bar').style.width = `${pct}%`;
    $('#progress-label').textContent = label;
}

function getScoreColor(score) {
    if (score >= 75) return 'var(--accent-green)';
    if (score >= 50) return 'var(--accent-yellow)';
    return 'var(--accent-red)';
}

function getScoreClass(score) {
    if (score >= 75) return 'high';
    if (score >= 50) return 'medium';
    return 'low';
}

function renderBreakdown(cycle, scores) {
    const categories = [
        { key: 'named_insured', label: 'Named Insured', max: 10 },
        { key: 'policy_numbers', label: 'Policy Numbers', max: 10 },
        { key: 'insurance_carrier', label: 'Insurance Carrier', max: 10 },
        { key: 'coverage_types', label: 'Coverage Types', max: 10 },
        { key: 'coverage_limits', label: 'Coverage Limits', max: 15 },
        { key: 'effective_expiration_dates', label: 'Dates', max: 10 },
        { key: 'certificate_holder', label: 'Certificate Holder', max: 10 },
        { key: 'additional_insured', label: 'Additional Insured', max: 10 },
        { key: 'subrogation_waiver', label: 'Subrogation Waiver', max: 5 },
        { key: 'special_conditions', label: 'Special Conditions', max: 10 },
    ];

    const container = $(`#breakdown-${cycle}`);
    container.innerHTML = categories.map(cat => {
        const val = scores[cat.key] || 0;
        const pct = (val / cat.max * 100).toFixed(0);
        const color = getScoreColor(val / cat.max * 100);
        return `
            <div class="breakdown-row">
                <span class="breakdown-label">${cat.label}</span>
                <div class="breakdown-bar-container">
                    <div class="breakdown-bar" style="width: ${pct}%; background: ${color}"></div>
                </div>
                <span class="breakdown-value">${val}/${cat.max}</span>
            </div>
        `;
    }).join('');

    // Add feedback
    if (scores.feedback) {
        container.innerHTML += `<p style="margin-top: 8px; font-size: 12px; color: var(--text-secondary); font-style: italic;">${escapeHtml(scores.feedback)}</p>`;
    }
}

function addPromptVersion(label, prompt, oldPrompt) {
    const container = $('#prompt-evolution');

    if (container.children.length > 0) {
        const arrow = document.createElement('div');
        arrow.className = 'prompt-arrow';
        arrow.textContent = '⬇ Optimizer rewrote the prompt';
        container.appendChild(arrow);
    }

    const version = document.createElement('div');
    version.className = 'prompt-version';
    version.innerHTML = `
        <div class="prompt-version-header">
            <span class="prompt-version-label">${escapeHtml(label)}</span>
        </div>
        <pre class="prompt-text">${escapeHtml(prompt)}</pre>
    `;
    container.appendChild(version);

    // Scroll to show latest
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== Toggle Details =====
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('toggle-details')) {
        const cycle = e.target.dataset.cycle;
        const details = $(`#details-${cycle}`);
        if (details.classList.contains('hidden')) {
            details.classList.remove('hidden');
            e.target.textContent = 'Hide Details ▲';
        } else {
            details.classList.add('hidden');
            e.target.textContent = 'View Details ▼';
        }
    }
});
