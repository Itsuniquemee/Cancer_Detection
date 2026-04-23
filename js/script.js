// ============ CONFIGURATION ============
const API_BASE = window.location.origin;

// ============ MATRIX BACKGROUND ============
const codeSnippets = [
    'import torch',
    'def predict()',
    'accuracy 95.2%',
    'model.eval()',
    'tensor.shape',
    'sigmoid(x)',
    'loss.backward()',
    'CNN layers',
    'DICOM image',
    'classification',
    'conv2d(64)',
    'maxpool',
    'dropout(0.5)',
    'optimizer.step()',
    'return probs',
    'validation set',
    'breast cancer',
    'benign/malignant',
    'feature maps',
    'backprop'
];

const colors = ['#0d9488', '#f59e0b', '#9333ea', '#0ea5e9', '#fb7185'];

function initializeMatrix() {
    const container = document.getElementById('matrixContainer');
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const gridSize = 60;
    const cols = Math.ceil(width / gridSize) + 2;
    const rows = Math.ceil(height / gridSize) + 2;

    for (let i = 0; i < cols * rows * 0.3; i++) {
        const codeEl = document.createElement('div');
        codeEl.className = 'matrix-code';

        const x = Math.random() * (width + gridSize * 2) - gridSize;
        const y = Math.random() * (height + gridSize * 2) - gridSize;

        codeEl.textContent = codeSnippets[Math.floor(Math.random() * codeSnippets.length)];
        codeEl.style.left = x + 'px';
        codeEl.style.top = y + 'px';
        codeEl.style.color = colors[Math.floor(Math.random() * colors.length)];

        const duration = 20 + Math.random() * 20;
        const delay = Math.random() * 5;
        codeEl.style.animation = `float ${duration}s linear ${delay}s infinite`;

        container.appendChild(codeEl);
    }

    // Flicker effect
    setInterval(() => {
        const codeEls = container.querySelectorAll('.matrix-code');
        if (codeEls.length === 0) return;
        const randomEl = codeEls[Math.floor(Math.random() * codeEls.length)];
        if (randomEl) {
            randomEl.style.opacity = '0.1';
            setTimeout(() => {
                randomEl.style.opacity = '0.4';
            }, 100 + Math.random() * 200);
        }
    }, 500);
}

// ============ GLOBAL STATE ============
let selectedFile = null;        // The raw File object from input/drop
let imageDataURL = null;        // Data-URL of the currently previewed image
let lastAnalysisResult = null;  // Last analysis response from the backend

// ============ FILE UPLOAD ============
function setupUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    if (!uploadArea || !fileInput) return;

    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.background = 'rgba(251, 113, 133, 0.1)';
        uploadArea.style.borderColor = '#fb7185';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.background = 'rgba(251, 113, 133, 0.02)';
        uploadArea.style.borderColor = 'rgba(251, 113, 133, 0.3)';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.background = 'rgba(251, 113, 133, 0.02)';
        uploadArea.style.borderColor = 'rgba(251, 113, 133, 0.3)';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
}

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        showToast('Please upload an image file (PNG, JPG, DICOM)', 'error');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        showToast('File size must be less than 10MB', 'error');
        return;
    }

    selectedFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        imageDataURL = e.target.result;
        const previewImg = document.getElementById('previewImg');
        const imagePreview = document.getElementById('imagePreview');
        if (previewImg && imagePreview) {
            previewImg.src = imageDataURL;
            imagePreview.style.display = 'block';
        }
        onNewImageUploaded();
    };
    reader.readAsDataURL(file);
}

// ============ ML MODEL ANALYSIS ============
async function analyzeImage() {
    if (!imageDataURL) {
        showToast('Please upload an image first', 'error');
        return;
    }

    const analyzeBtn = document.getElementById('analyzeBtn');
    const uploadArea = document.getElementById('uploadArea');
    const placeholderText = document.getElementById('placeholderText');
    const resultsContainer = document.getElementById('resultsContainer');
    const rejectionContainer = document.getElementById('rejectionContainer');

    // Show loading state
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<span class="spinner"></span> Analyzing...';
    uploadArea.style.pointerEvents = 'none';
    uploadArea.style.opacity = '0.6';
    if (placeholderText) placeholderText.style.display = 'none';

    // Hide both result containers
    if (resultsContainer) resultsContainer.style.display = 'none';
    if (rejectionContainer) rejectionContainer.style.display = 'none';

    try {
        const result = await sendImageToBackend(imageDataURL);
        lastAnalysisResult = result;

        if (result.is_medical_image === false) {
            // ── Image was REJECTED by backend ──
            displayRejection(result);
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = '⚠ Not a Medical Image';
        } else {
            // ── Valid medical image — show results ──
            displayResults(result);
            resultsContainer.style.display = 'block';
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = '✓ Results Generated';
        }

        uploadArea.style.pointerEvents = 'auto';
        uploadArea.style.opacity = '1';
    } catch (error) {
        console.error('Analysis error:', error);
        showToast('Analysis failed: ' + error.message, 'error');
        analyzeBtn.innerHTML = 'Analyze Image';
        analyzeBtn.disabled = false;
        uploadArea.style.pointerEvents = 'auto';
        uploadArea.style.opacity = '1';
    }
}

// Called when a new image is uploaded
function onNewImageUploaded() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = 'Analyze Image';
    }

    // Clear previous results
    const resultsContainer = document.getElementById('resultsContainer');
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
    }
    const rejectionContainer = document.getElementById('rejectionContainer');
    if (rejectionContainer) {
        rejectionContainer.style.display = 'none';
    }
    lastAnalysisResult = null;
}

// ============ BACKEND COMMUNICATION ============
async function sendImageToBackend(base64Image) {
    try {
        const response = await fetch(`${API_BASE}/api/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: base64Image })
        });

        if (!response.ok) {
            const errBody = await response.json().catch(() => ({}));
            throw new Error(errBody.error || `Server error ${response.status}`);
        }

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error || 'Unknown prediction error');
        }

        return data;
    } catch (err) {
        if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
            throw new Error(
                'Backend server is not running. Start it with: python app.py'
            );
        }
        throw err;
    }
}

// ============ DISPLAY RESULTS ============
function displayResults(data) {
    const classification = data.classification;
    const confidence = data.confidence;
    const riskScore = data.risk_score;

    const isMalignant = classification === 'Malignant';
    const classColor = isMalignant ? '#fb7185' : '#10b981';

    // Classification
    const classEl = document.getElementById('classification');
    if (classEl) {
        classEl.textContent = classification;
        classEl.style.color = classColor;
    }

    // Confidence
    const confEl = document.getElementById('confidence');
    if (confEl) {
        confEl.textContent = confidence.toFixed(1) + '%';
        confEl.style.color = classColor;
    }

    // Risk bar
    const riskBar = document.getElementById('riskBar');
    if (riskBar) {
        riskBar.style.width = riskScore + '%';
        riskBar.style.background = riskScore > 50
            ? 'linear-gradient(90deg, #fb7185, #f472b6)'
            : 'linear-gradient(90deg, #10b981, #34d399)';
    }

    // Risk value
    const riskEl = document.getElementById('riskValue');
    if (riskEl) {
        riskEl.textContent = riskScore.toFixed(1) + '%';
    }
}

// ============ DISPLAY REJECTION ============
function displayRejection(data) {
    const rejectionContainer = document.getElementById('rejectionContainer');
    if (!rejectionContainer) return;

    const details = data.rejection_details ||
        'This image does not appear to be a medical scan.';

    rejectionContainer.innerHTML = `
        <div class="rejection-card">
            <div class="rejection-icon">🚫</div>
            <h4 class="rejection-title">Not a Medical Image</h4>
            <p class="rejection-text">${details}</p>
            <div class="rejection-tips">
                <p><strong>Accepted image types:</strong></p>
                <ul>
                    <li>Mammography scans (grayscale)</li>
                    <li>X-ray images</li>
                    <li>Histopathology slides</li>
                    <li>DICOM medical images</li>
                </ul>
            </div>
        </div>
    `;
    rejectionContainer.style.display = 'block';
}

// ============ TOAST NOTIFICATIONS ============
function showToast(message, type = 'info') {
    // Remove existing toasts
    document.querySelectorAll('.toast-notification').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ============ REPORT DOWNLOAD ============
function downloadReport() {
    const classification = document.getElementById('classification')?.textContent || '-';
    const confidence = document.getElementById('confidence')?.textContent || '-';
    const riskValue = document.getElementById('riskValue')?.textContent || '-';
    const timestamp = new Date().toLocaleString();

    const rec = lastAnalysisResult?.recommendation;
    const nextSteps = rec?.next_steps?.map(s => `  • ${s}`).join('\n') || '  • Consult your physician';

    const reportContent = `
╔═══════════════════════════════════════════════════════╗
║         BREAST CANCER DETECTION REPORT                ║
║         CancerDetect AI System v2.0                   ║
╚═══════════════════════════════════════════════════════╝

ANALYSIS RESULTS
════════════════════════════════════════════════════════

Classification:  ${classification}
Confidence:      ${confidence}
Risk Score:      ${riskValue}
Urgency:         ${rec?.urgency || 'N/A'}

Analysis Time:   ${timestamp}

RECOMMENDED NEXT STEPS
════════════════════════════════════════════════════════

${nextSteps}

INTERPRETATION GUIDE
════════════════════════════════════════════════════════

Benign (Risk < 50%):
  • No malignant features detected
  • Regular follow-up recommended
  • Clinical correlation advised

Malignant (Risk > 50%):
  • Suspicious features identified
  • Urgent specialist consultation recommended
  • Further diagnostic procedures may be needed

IMPORTANT DISCLAIMER
════════════════════════════════════════════════════════

This AI analysis is a supplementary tool and should NOT
be used as the sole basis for clinical diagnosis. Results
must be interpreted by qualified medical professionals in
conjunction with clinical examination and other diagnostic
modalities.

For medical advice, please consult with a healthcare
provider.

════════════════════════════════════════════════════════
Generated by CancerDetect AI v2.0
    `.trim();

    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cancer-detection-report-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    showToast('Report downloaded successfully', 'success');
}

// ============ SCROLL ANIMATIONS ============
const observerOptions = {
    threshold: 0.05,
    rootMargin: '0px 0px -80px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animation = 'revealOnScroll 1s cubic-bezier(0.16, 1, 0.3, 1) forwards';
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// ============ SMOOTH SCROLL ============
function scrollToDetector() {
    const detector = document.getElementById('detector');
    if (detector) {
        detector.scrollIntoView({ behavior: 'smooth' });
    }
}

function scrollToFeatures() {
    const features = document.getElementById('features');
    if (features) {
        features.scrollIntoView({ behavior: 'smooth' });
    }
}

// ============ NAV LINK SMOOTH SCROLL ============
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && document.querySelector(href)) {
                e.preventDefault();
                document.querySelector(href).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

// ============ MOBILE MENU ============
function setupMobileMenu() {
    const hamburger = document.getElementById('hamburgerBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    if (!hamburger || !mobileMenu) return;

    hamburger.addEventListener('click', () => {
        mobileMenu.classList.toggle('open');
        hamburger.classList.toggle('active');
    });

    // Close on link click
    mobileMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            mobileMenu.classList.remove('open');
            hamburger.classList.remove('active');
        });
    });
}

// ============ BACKEND HEALTH CHECK ============
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`, { method: 'GET' });
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Backend healthy:', data);
            return true;
        }
    } catch (e) {
        console.warn('⚠️ Backend not reachable:', e.message);
    }
    return false;
}

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
    initializeMatrix();
    setupUpload();
    setupSmoothScroll();
    setupMobileMenu();

    // Backend health check
    checkBackendHealth().then(healthy => {
        if (!healthy) {
            console.warn('Backend server is not running. Start with: python app.py');
        }
    });

    // Initialize scroll animations
    const elementsToAnimate = document.querySelectorAll(
        '.stat-block, .feature-section, .step-item, .model-card, .detector-left, .detector-right'
    );

    elementsToAnimate.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(60px)';
        observer.observe(el);
    });

    // Animate nav on scroll
    const navbar = document.querySelector('.navbar');

    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > 100) {
            navbar.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.12)';
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        } else {
            navbar.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.04)';
            navbar.style.background = 'rgba(255, 255, 255, 0.8)';
        }
    });
});

// ============ KEYBOARD SHORTCUTS ============
document.addEventListener('keydown', (e) => {
    // Don't fire shortcuts when typing in inputs
    const tag = e.target.tagName.toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable) {
        return;
    }

    if (e.key === '?') {
        showToast('Shortcuts: D → Detector, F → Features, ? → Help', 'info');
    }
    if (e.key === 'd' || e.key === 'D') {
        scrollToDetector();
    }
    if (e.key === 'f' || e.key === 'F') {
        scrollToFeatures();
    }
});
