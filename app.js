// State Management
let state = {
    jobs: [],
    settings: {},
    currentTab: 'dashboard',
    selectedJobId: null,
    scanning: false
};

// API Endpoints
const API = {
    getJobs: async (status = '') => {
        const url = status ? `/api/jobs?status=${status}` : '/api/jobs';
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch jobs');
        return res.json();
    },
    getJob: async (id) => {
        const res = await fetch(`/api/jobs/${id}`);
        if (!res.ok) throw new Error('Failed to fetch job details');
        return res.json();
    },
    updateJobStatus: async (id, status) => {
        const res = await fetch(`/api/jobs/${id}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        if (!res.ok) throw new Error('Failed to update job status');
        return res.json();
    },
    updateCoverLetter: async (id, cover_letter) => {
        const res = await fetch(`/api/jobs/${id}/cover-letter`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cover_letter })
        });
        if (!res.ok) throw new Error('Failed to update cover letter');
        return res.json();
    },
    applyJob: async (id, recipient_email, subject, cover_letter) => {
        const res = await fetch(`/api/jobs/${id}/apply`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recipient_email, subject, cover_letter })
        });
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Failed to send application email');
        }
        return res.json();
    },
    getSettings: async () => {
        const res = await fetch('/api/settings');
        if (!res.ok) throw new Error('Failed to fetch settings');
        return res.json();
    },
    saveSettings: async (settingsData) => {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settingsData)
        });
        if (!res.ok) throw new Error('Failed to save settings');
        return res.json();
    },
    triggerScan: async () => {
        const res = await fetch('/api/scan', { method: 'POST' });
        if (!res.ok) throw new Error('Failed to start scanner');
        return res.json();
    }
};

// UI Elements & Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupTabNavigation();
    setupSettingsForm();
    setupScanActions();
    setupSlideOver();
    setupApplyModal();
});

// Initialise App
async function initApp() {
    try {
        showToast('Initializing application...', 'success');
        await loadSettings();
        await loadJobs();
    } catch (err) {
        showToast(`Initialization error: ${err.message}`, 'error');
        console.error(err);
    }
}

// Tab Navigation logic
function setupTabNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            
            navButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(t => t.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(`tab-${tabId}`).classList.add('active');
            
            state.currentTab = tabId;
            
            // Reload specific elements on tab switch if necessary
            if (tabId === 'jobs') {
                renderJobsGrid();
            } else if (tabId === 'cv-helper') {
                renderCvHelperLayout();
            }
        });
    });

    // See all jobs button on dashboard link to jobs feed
    document.getElementById('see-all-jobs').addEventListener('click', () => {
        const jobsNavBtn = document.querySelector('.nav-btn[data-tab="jobs"]');
        if (jobsNavBtn) jobsNavBtn.click();
    });
}

// Load and populate settings
async function loadSettings() {
    try {
        const settings = await API.getSettings();
        state.settings = settings;

        // Populate fields
        document.getElementById('settings-cv-text').value = settings.cv_text || '';
        document.getElementById('settings-keywords').value = settings.search_keywords || '';
        document.getElementById('settings-locations').value = settings.search_locations || '';
        document.getElementById('settings-provider').value = settings.ai_provider || 'gemini';
        document.getElementById('settings-api-key').value = settings.ai_api_key_masked || '';
        document.getElementById('settings-gmail-user').value = settings.gmail_user || '';
        document.getElementById('settings-gmail-password').value = settings.gmail_password_masked || '';

        // Site checkboxes
        const checkboxes = document.querySelectorAll('input[name="sites"]');
        checkboxes.forEach(cb => {
            cb.checked = settings.sites.includes(cb.value);
        });

        updateDashboardSummary();
    } catch (err) {
        showToast('Error loading configurations.', 'error');
    }
}

// Update dashboard overview with current settings criteria
function updateDashboardSummary() {
    // Keywords tags
    const keywordsContainer = document.getElementById('summary-keywords');
    keywordsContainer.innerHTML = '';
    if (state.settings.search_keywords) {
        state.settings.search_keywords.split(',').forEach(kw => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.textContent = kw.trim();
            keywordsContainer.appendChild(span);
        });
    }

    // Locations tags
    const locationsContainer = document.getElementById('summary-locations');
    locationsContainer.innerHTML = '';
    if (state.settings.search_locations) {
        state.settings.search_locations.split(',').forEach(loc => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.textContent = loc.trim();
            locationsContainer.appendChild(span);
        });
    }

    // Platforms tags
    const sitesContainer = document.getElementById('summary-sites');
    sitesContainer.innerHTML = '';
    if (state.settings.sites) {
        state.settings.sites.forEach(site => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.textContent = site;
            sitesContainer.appendChild(span);
        });
    }
}

// Settings submit
function setupSettingsForm() {
    const form = document.getElementById('settings-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Get sites checklist
        const checkedSites = [];
        document.querySelectorAll('input[name="sites"]:checked').forEach(cb => {
            checkedSites.push(cb.value);
        });

        const settingsData = {
            cv_text: document.getElementById('settings-cv-text').value,
            search_keywords: document.getElementById('settings-keywords').value,
            search_locations: document.getElementById('settings-locations').value,
            ai_provider: document.getElementById('settings-provider').value,
            ai_api_key: document.getElementById('settings-api-key').value,
            gmail_user: document.getElementById('settings-gmail-user').value,
            gmail_password: document.getElementById('settings-gmail-password').value,
            sites: checkedSites
        };

        try {
            const saveBtn = document.getElementById('save-settings-btn');
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
            
            await API.saveSettings(settingsData);
            
            showToast('Configuration updated successfully!', 'success');
            await loadSettings();
        } catch (err) {
            showToast('Failed to update configuration.', 'error');
        } finally {
            const saveBtn = document.getElementById('save-settings-btn');
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fa-solid fa-check"></i> Save Configuration';
        }
    });
}

// Load jobs and calculate stats
async function loadJobs() {
    try {
        const jobs = await API.getJobs();
        state.jobs = jobs;
        
        // Update job navigation count badge
        document.getElementById('job-count-badge').textContent = jobs.filter(j => j.status === 'Matched').length;

        updateStats();
        renderTopMatches();
        
        if (state.currentTab === 'jobs') {
            renderJobsGrid();
        } else if (state.currentTab === 'cv-helper') {
            renderCvHelperLayout();
        }
    } catch (err) {
        showToast('Error retrieving job matches.', 'error');
    }
}

// Compute counts for dashboard cards
function updateStats() {
    const totalScanned = state.jobs.length;
    const highMatches = state.jobs.filter(j => j.grade >= 8).length;
    const applicationsSent = state.jobs.filter(j => j.status === 'Applied').length;
    
    document.getElementById('stat-scanned').textContent = totalScanned;
    document.getElementById('stat-high-matches').textContent = highMatches;
    document.getElementById('stat-applied').textContent = applicationsSent;
    
    // Last scan timestamp
    if (state.jobs.length > 0) {
        const dates = state.jobs.map(j => new Date(j.created_at));
        const newest = new Date(Math.max(...dates));
        document.getElementById('last-scan-time').textContent = newest.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' ' + newest.toLocaleDateString();
    } else {
        document.getElementById('last-scan-time').textContent = 'Never';
    }
}

// Render top matches on Dashboard Tab
function renderTopMatches() {
    const listContainer = document.getElementById('top-matches-list');
    listContainer.innerHTML = '';
    
    // Sort matching by grade descending, limit to 3
    const topMatches = state.jobs
        .filter(j => j.status === 'Matched')
        .slice(0, 3);
        
    if (topMatches.length === 0) {
        listContainer.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-face-smile-wink"></i>
                <p>All scanned jobs reviewed! Perform a new scan to discover positions.</p>
            </div>
        `;
        return;
    }
    
    topMatches.forEach(job => {
        const div = document.createElement('div');
        div.className = 'job-card-compact';
        div.addEventListener('click', () => openJobDetail(job.id));
        
        let gradeClass = 'high';
        if (job.grade < 5) gradeClass = 'low';
        else if (job.grade < 8) gradeClass = 'mid';
        
        div.innerHTML = `
            <div class="grade-badge-circle ${gradeClass}">${job.grade}</div>
            <div class="job-info-compact">
                <h4>${job.title}</h4>
                <p>${job.company} • ${job.location}</p>
            </div>
            <div class="job-meta-compact">
                <span class="job-site-tag">${job.site}</span>
            </div>
        `;
        listContainer.appendChild(div);
    });
}

// Render Jobs Feed Grid based on active filters
let activeJobFilter = 'all';
function renderJobsGrid() {
    const grid = document.getElementById('all-jobs-grid');
    grid.innerHTML = '';
    
    // Filter click events hook (run once)
    const filterButtons = document.querySelectorAll('.filter-bar .filter-btn');
    filterButtons.forEach(btn => {
        btn.onclick = (e) => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeJobFilter = btn.getAttribute('data-filter');
            renderJobsGrid();
        };
    });
    
    // Filter job list
    let filteredJobs = state.jobs;
    if (activeJobFilter !== 'all') {
        filteredJobs = state.jobs.filter(j => j.status === activeJobFilter);
    }
    
    if (filteredJobs.length === 0) {
        grid.innerHTML = `
            <div class="col-span-2 empty-state">
                <i class="fa-solid fa-box-open"></i>
                <p>No job matches found matching filter: "${activeJobFilter}".</p>
            </div>
        `;
        return;
    }
    
    filteredJobs.forEach(job => {
        const card = document.createElement('article');
        card.className = 'job-card';
        
        let gradeClass = 'high';
        if (job.grade < 5) gradeClass = 'low';
        else if (job.grade < 8) gradeClass = 'mid';
        
        let statusBadge = '';
        if (job.status === 'Applied') {
            statusBadge = '<span class="status-indicator status-applied"><i class="fa-solid fa-paper-plane"></i> Applied</span>';
        } else if (job.status === 'Skipped') {
            statusBadge = '<span class="status-indicator status-skipped"><i class="fa-solid fa-ban"></i> Skipped</span>';
        } else {
            statusBadge = '<span class="status-indicator status-matched"><i class="fa-solid fa-envelope-open"></i> Matched</span>';
        }
        
        card.innerHTML = `
            <div>
                <div class="job-card-header">
                    <div class="job-title-sec">
                        <h3>${job.title}</h3>
                        <div class="job-company">${job.company}</div>
                    </div>
                    <div class="grade-badge-circle large ${gradeClass}">${job.grade}</div>
                </div>
                
                <div class="job-meta-row">
                    <span class="meta-pill"><i class="fa-solid fa-location-dot"></i> ${job.location}</span>
                    <span class="meta-pill site"><i class="fa-solid fa-globe"></i> ${job.site}</span>
                </div>
                
                <p class="job-desc-snippet">${job.description}</p>
            </div>
            
            <div class="job-card-footer">
                ${statusBadge}
                <div class="card-actions">
                    <button class="btn-secondary" onclick="event.stopPropagation(); quickSkipJob(${job.id})"><i class="fa-solid fa-eye-slash"></i> Hide</button>
                    <button class="btn-primary" onclick="event.stopPropagation(); openJobDetail(${job.id})">Review & Apply</button>
                </div>
            </div>
        `;
        
        card.onclick = () => openJobDetail(job.id);
        grid.appendChild(card);
    });
}

// Render CV Tailoring Suggestions Split Layout
function renderCvHelperLayout() {
    const listContainer = document.getElementById('cv-jobs-list-container');
    const detailPane = document.getElementById('cv-suggestions-detail-pane');
    listContainer.innerHTML = '';
    
    // Sort matches: only active matched jobs with grade >= 5
    const eligibleJobs = state.jobs.filter(j => j.status === 'Matched');
    
    if (eligibleJobs.length === 0) {
        listContainer.innerHTML = '<div class="empty-state"><p>No unreviewed jobs.</p></div>';
        detailPane.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-lightbulb"></i>
                <p>Run a search scan or reset job filters to review CV advice.</p>
            </div>
        `;
        return;
    }
    
    eligibleJobs.forEach(job => {
        const item = document.createElement('div');
        item.className = 'cv-job-item';
        
        let gradeClass = 'high';
        if (job.grade < 5) gradeClass = 'low';
        else if (job.grade < 8) gradeClass = 'mid';
        
        item.innerHTML = `
            <div class="grade-mini ${gradeClass}">${job.grade}</div>
            <div class="cv-job-item-info">
                <h4>${job.title}</h4>
                <p>${job.company}</p>
            </div>
        `;
        
        item.onclick = () => {
            document.querySelectorAll('.cv-job-item').forEach(el => el.classList.remove('selected'));
            item.classList.add('selected');
            renderCvSuggestionsDetail(job);
        };
        
        listContainer.appendChild(item);
    });
    
    // Auto-select first item if list is populated
    if (eligibleJobs.length > 0) {
        listContainer.firstChild.click();
    }
}

// Fill right pane with CV tailoring data
function renderCvSuggestionsDetail(job) {
    const container = document.getElementById('cv-suggestions-detail-pane');
    
    const matchedPills = job.skills_matched.map(s => `<span class="skill-pill match"><i class="fa-solid fa-circle-check"></i> ${s}</span>`).join('');
    const missingPills = job.skills_missing.map(s => `<span class="skill-pill missing"><i class="fa-solid fa-circle-exclamation"></i> ${s}</span>`).join('');
    
    container.innerHTML = `
        <div class="suggestion-section">
            <h1 style="font-size: 24px; margin-bottom: 4px;">Tailoring CV for ${job.title}</h1>
            <p class="subtitle">${job.company} • Matches your profile at ${job.grade}/10</p>
        </div>
        
        <div class="suggestion-section">
            <h3><i class="fa-solid fa-diagram-project"></i> Skill Match Comparison</h3>
            <div class="skills-pill-group">
                ${matchedPills || '<span class="field-desc">None detected.</span>'}
                ${missingPills}
            </div>
        </div>
        
        <div class="suggestion-section">
            <h3><i class="fa-solid fa-wand-magic-sparkles"></i> AI CV Modification Instructions</h3>
            <div class="cv-instructions">${job.cv_suggestions || 'No instructions generated. Adjust Settings and API Keys to run AI parsing.'}</div>
        </div>
        
        <div class="suggestion-section" style="margin-top: 30px; display: flex; gap: 12px;">
            <a href="${job.url}" target="_blank" class="btn-secondary" style="text-decoration: none; display: inline-flex; align-items: center;"><i class="fa-solid fa-arrow-up-right-from-square"></i> Original Job Post</a>
            <button class="btn-primary" onclick="openJobDetail(${job.id})">Generate Tailored Cover Letter</button>
        </div>
    `;
}

// Quick hide/skip job from feed
async function quickSkipJob(id) {
    try {
        await API.updateJobStatus(id, 'Skipped');
        showToast('Job marked as skipped/hidden.', 'success');
        await loadJobs();
    } catch (err) {
        showToast('Error skipping job.', 'error');
    }
}

// Slide-Over detailed card panel
function setupSlideOver() {
    const backdrop = document.getElementById('job-detail-slideover');
    const closeBtn = document.getElementById('close-slideover-btn');
    
    closeBtn.addEventListener('click', () => {
        backdrop.classList.remove('active');
    });
    
    backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) backdrop.classList.remove('active');
    });
}

// Open detailed slide-over
async function openJobDetail(id) {
    state.selectedJobId = id;
    const backdrop = document.getElementById('job-detail-slideover');
    const container = document.getElementById('slideover-content-container');
    
    container.innerHTML = '<div class="empty-state"><i class="fa-solid fa-spinner fa-spin"></i><p>Loading application analysis...</p></div>';
    backdrop.classList.add('active');
    
    try {
        const job = await API.getJob(id);
        
        let gradeClass = 'high';
        if (job.grade < 5) gradeClass = 'low';
        else if (job.grade < 8) gradeClass = 'mid';
        
        container.innerHTML = `
            <div class="so-header">
                <h2>${job.title}</h2>
                <div class="so-company">${job.company} • ${job.location}</div>
            </div>
            
            <div class="so-grade-card">
                <div class="grade-badge-circle so-grade-circle ${gradeClass}">${job.grade}</div>
                <div class="so-grade-info">
                    <h3>Compatibility Score: ${job.grade}/10</h3>
                    <p>${job.explanation}</p>
                </div>
            </div>
            
            <div class="so-section-title">Job Description</div>
            <div class="so-paragraph">${job.description}</div>
            
            <div class="so-section-title">Skills Analysis</div>
            <div class="skills-pill-group" style="margin-bottom: 24px;">
                ${job.skills_matched.map(s => `<span class="skill-pill match"><i class="fa-solid fa-circle-check"></i> ${s}</span>`).join('')}
                ${job.skills_missing.map(s => `<span class="skill-pill missing"><i class="fa-solid fa-circle-exclamation"></i> ${s}</span>`).join('')}
            </div>
            
            <div class="so-section-title">CV Suggestions</div>
            <div class="so-paragraph" style="background: var(--primary-light); padding: 14px; border-radius: var(--border-radius-md); font-size: 13.5px; border-left: 3px solid var(--primary);">${job.cv_suggestions || 'No recommendations.'}</div>
            
            <div class="so-section-title">AI Custom Cover Letter</div>
            <div class="so-cover-letter-wrapper">
                <textarea class="so-cover-letter-area" id="so-cl-textarea" rows="12">${job.cover_letter}</textarea>
                <div class="edit-cl-indicator"><i class="fa-solid fa-pen-to-square"></i> You can edit this cover letter inline before sending.</div>
            </div>
            
            <div class="so-actions-bar">
                <button class="btn-secondary" onclick="changeStatusFromSlideOver(${job.id}, 'Skipped')"><i class="fa-solid fa-ban"></i> Skip Job</button>
                <button class="btn-primary" onclick="triggerEmailModal()"><i class="fa-solid fa-envelope"></i> Send Application</button>
            </div>
        `;
        
        // Listen to manual changes in the cover letter text area and save them in state/DB
        const textarea = document.getElementById('so-cl-textarea');
        textarea.onblur = async () => {
            try {
                await API.updateCoverLetter(job.id, textarea.value);
                state.jobs = state.jobs.map(j => j.id === job.id ? { ...j, cover_letter: textarea.value } : j);
                showToast('Cover letter changes saved.', 'success');
            } catch (err) {
                showToast('Failed to save cover letter updates.', 'error');
            }
        };
        
    } catch (err) {
        container.innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i><p>Failed to load job details.</p></div>`;
    }
}

async function changeStatusFromSlideOver(id, status) {
    try {
        await API.updateJobStatus(id, status);
        document.getElementById('job-detail-slideover').classList.remove('active');
        showToast(`Job marked as ${status}.`, 'success');
        await loadJobs();
    } catch (err) {
        showToast('Failed to update status.', 'error');
    }
}

// Gmail Sending Modal Layout hooks
function setupApplyModal() {
    const modal = document.getElementById('apply-email-modal');
    const closeBtns = modal.querySelectorAll('#close-modal-btn, #cancel-apply-btn');
    
    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => modal.classList.remove('active'));
    });
    
    // Handle form submit
    const form = document.getElementById('apply-email-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const recipient = document.getElementById('apply-recipient').value;
        const subject = document.getElementById('apply-subject').value;
        const body = document.getElementById('apply-body').value;
        
        const sendBtn = document.getElementById('send-apply-btn');
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Dispatching...';
        
        try {
            await API.applyJob(state.selectedJobId, recipient, subject, body);
            
            showToast('Application email sent via Gmail successfully!', 'success');
            modal.classList.remove('active');
            document.getElementById('job-detail-slideover').classList.remove('active');
            
            await loadJobs();
        } catch (err) {
            showToast(`Mail error: ${err.message}`, 'error');
        } finally {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Send via Gmail';
        }
    });
}

function triggerEmailModal() {
    // Read current cover letter from slide-over textarea (which might have edits)
    const currentCoverLetter = document.getElementById('so-cl-textarea').value;
    
    // Find job details
    const job = state.jobs.find(j => j.id === state.selectedJobId);
    
    document.getElementById('apply-recipient').value = '';
    document.getElementById('apply-subject').value = `Application for ${job.title} - Nour`;
    document.getElementById('apply-body').value = currentCoverLetter;
    
    document.getElementById('apply-email-modal').classList.add('active');
}

// Scraper Trigger Actions
function setupScanActions() {
    const btn = document.getElementById('trigger-scan-btn');
    const statusText = document.getElementById('scan-status-text');
    
    btn.addEventListener('click', async () => {
        if (state.scanning) return;
        
        try {
            state.scanning = true;
            btn.disabled = true;
            btn.querySelector('i').classList.add('spinning');
            statusText.textContent = 'Searching job sites...';
            statusText.classList.add('running');
            
            showToast('Starting background job scanner...', 'success');
            await API.triggerScan();
            
            // Poll for jobs periodically
            let attempts = 0;
            const interval = setInterval(async () => {
                attempts++;
                statusText.textContent = `Analyzing matches (attempt ${attempts})...`;
                await loadJobs();
                
                // End polling after 15 seconds (the backend runs asynchronously)
                if (attempts >= 5) {
                    clearInterval(interval);
                    state.scanning = false;
                    btn.disabled = false;
                    btn.querySelector('i').classList.remove('spinning');
                    statusText.textContent = 'Ready to hunt';
                    statusText.classList.remove('running');
                    showToast('Scan complete! Check matches tab.', 'success');
                }
            }, 3000);
            
        } catch (err) {
            showToast('Error launching scraper scan.', 'error');
            state.scanning = false;
            btn.disabled = false;
            btn.querySelector('i').classList.remove('spinning');
            statusText.textContent = 'Ready to hunt';
            statusText.classList.remove('running');
        }
    });
}

// Helper: Toast Notifications
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type === 'error' ? 'error' : 'success'}`;
    
    const icon = type === 'error' ? 'fa-solid fa-triangle-exclamation' : 'fa-solid fa-circle-check';
    
    toast.innerHTML = `
        <i class="${icon}"></i>
        <div class="toast-msg">${message}</div>
    `;
    
    container.appendChild(toast);
    
    // Remove toast after 4s
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse forwards';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}
