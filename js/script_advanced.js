/* ============================================
   BREAST CANCER DETECTION - ADVANCED FRONTEND
   Production-Ready JavaScript with Analytics
   ============================================ */

const API_BASE = 'http://localhost:5000/api';
let currentResults = null;
let analysisChart = null;
let predictionHistory = [];

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupMatrixBackground();
    loadAnalytics();
    checkAPIStatus();
});

function initializeApp() {
    // File upload handlers
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');

    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.background = 'rgba(14, 165, 233, 0.1)';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.background = 'rgba(251, 113, 133, 0.05)';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.background = 'rgba(251, 113, 133, 0.05)';
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFile(e.target.files[0]);
        }
    });
}

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please upload an image file');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            displayImagePreview(e.target.result);
            enableAnalysis();
            clearResults();
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function displayImagePreview(dataUrl) {
    document.getElementById('imagePreview').style.display = 'block';
    document.getElementById('previewImg').src = dataUrl;
    document.getElementById('uploadArea').style.display = 'none';
}

function clearImage() {
    document.getElementById('fileInput').value = '';
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('uploadArea').style.display = 'block';
    disableAnalysis();
    clearResults();
}

function clearResults() {
    document.getElementById('resultsContainer').style.display = 'none';
    document.getElementById('placeholderText').style.display = 'flex';
    currentResults = null;
}

// ============ ANALYSIS ============
async function analyzeImage() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) {
        alert('Please upload an image first');
        return;
    }

    const analyzeBtn = document.getElementById('analyzeBtn');
    const btnText = document.getElementById('analyzeBtnText');
    const spinner = document.getElementById('analyzeBtnSpinner');

    analyzeBtn.disabled = true;
    btnText.textContent = 'Analyzing...';
    spinner.style.display = 'inline-block';

    try {
        // Extract features and get prediction
        const imageData = await readImageAsArray(fileInput.files[0]);
        const response = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imageData })
        });

        if (!response.ok) throw new Error(`API Error: ${response.status}`);

        const data = await response.json();
        currentResults = data.result;
        predictionHistory.push({
            timestamp: new Date().toISOString(),
            ...data.result
        });

        displayResults(data.result);
        saveToLocalStorage();
        loadAnalytics();

        btnText.textContent = 'Results Generated';
    } catch (error) {
        console.error('Analysis error:', error);
        alert('Error analyzing image. Please try again.');
        btnText.textContent = 'Analyze Image';
    } finally {
        analyzeBtn.disabled = true;
        spinner.style.display = 'none';
    }
}

async function readImageAsArray(file) {
    return new Promise((resolve, reject) => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();

        img.onload = () => {
            canvas.width = 256;
            canvas.height = 256;
            ctx.drawImage(img, 0, 0, 256, 256);
            const imageData = ctx.getImageData(0, 0, 256, 256);
            
            // Convert to grayscale
            const data = imageData.data;
            const grayscale = [];
            for (let i = 0; i < data.length; i += 4) {
                const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
                grayscale.push(gray / 255); // Normalize to 0-1
            }
            resolve(grayscale);
        };

        img.onerror = () => reject(new Error('Failed to load image'));
        img.src = URL.createObjectURL(file);
    });
}

function displayResults(results) {
    const { classification, confidence, risk_score, risk_level, probability, processing_time, model_type, confidence_interval } = results;

    // Update classification
    const classifElem = document.getElementById('classification');
    classifElem.textContent = classification.toUpperCase();
    classifElem.className = `classification-badge ${classification.toLowerCase()}`;

    // Update confidence
    document.getElementById('confidence').textContent = `${Math.round(confidence * 100)}%`;
    document.getElementById('confidenceBar').style.width = `${confidence * 100}%`;

    // Update risk score
    document.getElementById('riskValue').textContent = `${Math.round(risk_score * 100)}%`;
    document.getElementById('riskBar').style.width = `${risk_score * 100}%`;

    // Update risk level
    const riskLevelElem = document.getElementById('riskLevel');
    riskLevelElem.textContent = risk_level.toUpperCase();
    riskLevelElem.className = `risk-level ${risk_level.toLowerCase()}`;

    // Update detailed metrics
    document.getElementById('modelType').textContent = model_type || 'Logistic Regression';
    document.getElementById('processingTime').textContent = `${processing_time.toFixed(3)}s`;
    document.getElementById('probMalignant').textContent = `${Math.round(probability.malignant * 100)}%`;
    document.getElementById('probBenign').textContent = `${Math.round(probability.benign * 100)}%`;

    // Update confidence interval
    const ciLower = (confidence_interval.lower * 100).toFixed(1);
    const ciUpper = (confidence_interval.upper * 100).toFixed(1);
    document.getElementById('ciLower').textContent = `${ciLower}%`;
    document.getElementById('ciUpper').textContent = `${ciUpper}%`;
    const ciRange = document.getElementById('ciRange');
    ciRange.style.left = `${ciLower}%`;
    ciRange.style.right = `${100 - ciUpper}%`;

    // Update recommendations
    const recommendations = generateRecommendations(classification, risk_score);
    updateRecommendations(recommendations);

    // Show results
    document.getElementById('placeholderText').style.display = 'none';
    document.getElementById('resultsContainer').style.display = 'flex';
}

function generateRecommendations(classification, riskScore) {
    const recommendations = {
        benign_low: {
            urgency: 'low',
            action: 'No immediate action required.',
            steps: [
                'Continue regular mammography screening as recommended',
                'Maintain healthy lifestyle habits',
                'Schedule follow-up in 1-2 years'
            ]
        },
        benign_moderate: {
            urgency: 'moderate',
            action: 'Routine follow-up recommended within 6 months.',
            steps: [
                'Schedule follow-up mammography in 6 months',
                'Consult with radiologist for detailed review',
                'Keep records for comparison'
            ]
        },
        malignant_high: {
            urgency: 'high',
            action: 'Immediate consultation with oncologist recommended.',
            steps: [
                'Schedule urgent consultation with oncologist',
                'Prepare medical records for specialist review',
                'Discuss treatment options and biopsy if needed'
            ]
        },
        malignant_critical: {
            urgency: 'critical',
            action: 'Urgent medical intervention required.',
            steps: [
                'Contact specialist immediately',
                'Schedule diagnostic biopsy as priority',
                'Begin treatment planning with medical team'
            ]
        }
    };

    const key = classification === 'benign' 
        ? (riskScore < 0.4 ? 'benign_low' : 'benign_moderate')
        : (riskScore > 0.8 ? 'malignant_critical' : 'malignant_high');

    return recommendations[key];
}

function updateRecommendations(rec) {
    document.getElementById('urgencyLevel').textContent = rec.urgency.toUpperCase();
    document.getElementById('urgencyLevel').className = `urgency-badge ${rec.urgency}`;
    
    document.getElementById('action').textContent = rec.action;

    const stepsList = document.getElementById('nextSteps');
    stepsList.innerHTML = '';
    rec.steps.forEach(step => {
        const li = document.createElement('li');
        li.textContent = step;
        stepsList.appendChild(li);
    });
}

// ============ EXPLAINABILITY ============
async function explainPrediction() {
    if (!currentResults) {
        alert('No results to explain. Please analyze an image first.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/explain-prediction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ result: currentResults })
        });

        if (!response.ok) throw new Error(`API Error: ${response.status}`);

        const data = await response.json();
        displayExplanation(data.explanation);
    } catch (error) {
        console.error('Explanation error:', error);
        displayExplanation({
            summary: 'Unable to generate detailed explanation. Please try again.',
            feature_importance: []
        });
    }
}

function displayExplanation(explanation) {
    let html = `
        <h4>How This Prediction Was Made</h4>
        <p><strong>Summary:</strong> ${explanation.summary}</p>
        <hr style="margin: 1rem 0; border: none; border-top: 1px solid #e2e8f0;">
    `;

    if (explanation.feature_importance && explanation.feature_importance.length > 0) {
        html += '<h5>Top Contributing Features:</h5><ul>';
        explanation.feature_importance.slice(0, 10).forEach((feature, i) => {
            const impact = feature.importance * 100;
            html += `
                <li style="margin-bottom: 0.75rem;">
                    <strong>${feature.name}</strong>
                    <div style="width: 100%; background: #e2e8f0; height: 6px; border-radius: 3px; margin: 0.25rem 0;">
                        <div style="width: ${impact}%; background: linear-gradient(90deg, #fb7185, #f472b6); height: 100%; border-radius: 3px;"></div>
                    </div>
                    <small style="color: #64748b;">${impact.toFixed(1)}% impact</small>
                </li>
            `;
        });
        html += '</ul>';
    }

    document.getElementById('explanationBody').innerHTML = html;
    document.getElementById('explanationModal').style.display = 'flex';
}

// ============ REPORT GENERATION ============
async function downloadReport() {
    if (!currentResults) return;

    const report = generateReport(currentResults);
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(report));
    element.setAttribute('download', `cancer-detection-report-${Date.now()}.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

function generateReport(results) {
    const { classification, confidence, risk_score, probability, processing_time } = results;
    const date = new Date().toLocaleString();

    return `
BREAST CANCER DETECTION ANALYSIS REPORT
==========================================
Generated: ${date}

CLASSIFICATION
===============
Result: ${classification.toUpperCase()}
Confidence: ${(confidence * 100).toFixed(2)}%
Risk Score: ${(risk_score * 100).toFixed(2)}%

DETAILED ANALYSIS
==================
Probability (Malignant): ${(probability.malignant * 100).toFixed(2)}%
Probability (Benign): ${(probability.benign * 100).toFixed(2)}%
Processing Time: ${processing_time.toFixed(3)}s

DISCLAIMER
===========
This analysis is provided for informational purposes only and is NOT a substitute
for professional medical diagnosis. Final diagnosis must be made by qualified
medical professionals after thorough clinical examination.

NEXT STEPS
===========
Please consult with a qualified healthcare provider for proper medical guidance.

---
CancerDetect Pro v2.0
AI-Powered Diagnostic Platform
    `;
}

// ============ MODAL MANAGEMENT ============
function closeModal() {
    document.getElementById('explanationModal').style.display = 'none';
}

window.onclick = (event) => {
    const modal = document.getElementById('explanationModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
};

// ============ BUTTON STATE MANAGEMENT ============
function enableAnalysis() {
    const btn = document.getElementById('analyzeBtn');
    btn.disabled = false;
    btn.textContent = 'Analyze Image';
}

function disableAnalysis() {
    const btn = document.getElementById('analyzeBtn');
    btn.disabled = true;
}

// ============ ANALYTICS ============
function loadAnalytics() {
    const history = JSON.parse(localStorage.getItem('predictionHistory') || '[]');
    
    let totalAnalyses = history.length;
    let malignantCount = history.filter(h => h.classification === 'malignant').length;
    let benignCount = history.filter(h => h.classification === 'benign').length;
    let avgConfidence = history.length > 0 
        ? (history.reduce((sum, h) => sum + h.confidence, 0) / history.length * 100)
        : 0;

    document.getElementById('stat-predictions').textContent = totalAnalyses;
    document.getElementById('totalAnalyses').textContent = totalAnalyses;
    document.getElementById('malignantCount').textContent = malignantCount;
    document.getElementById('benignCount').textContent = benignCount;
    document.getElementById('avgConfidence').textContent = avgConfidence.toFixed(1) + '%';

    updateChart(malignantCount, benignCount);
}

function updateChart(malignant, benign) {
    const ctx = document.getElementById('resultsChart');
    if (!ctx) return;

    if (analysisChart) {
        analysisChart.destroy();
    }

    analysisChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Benign', 'Malignant'],
            datasets: [{
                data: [benign, malignant],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(251, 113, 133, 0.8)'
                ],
                borderColor: [
                    'rgba(16, 185, 129, 1)',
                    'rgba(251, 113, 133, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function saveToLocalStorage() {
    const history = JSON.parse(localStorage.getItem('predictionHistory') || '[]');
    if (currentResults) {
        history.push({
            timestamp: new Date().toISOString(),
            ...currentResults
        });
        // Keep only last 100 predictions
        if (history.length > 100) {
            history.shift();
        }
        localStorage.setItem('predictionHistory', JSON.stringify(history));
    }
}

// ============ API STATUS ============
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            document.getElementById('status-text').textContent = 'API Ready';
            document.getElementById('api-status').style.background = '#10b981';
        }
    } catch {
        document.getElementById('status-text').textContent = 'API Offline';
        document.getElementById('api-status').style.background = '#ef4444';
    }
}

// Periodically check API status
setInterval(checkAPIStatus, 30000);

// ============ MODEL INFORMATION ============
async function loadModelInfo() {
    try {
        const response = await fetch(`${API_BASE}/model-info`);
        if (!response.ok) throw new Error('Failed to fetch model info');
        
        const data = await response.json();
        displayModelInfo(data.model_info);
    } catch (error) {
        console.error('Error loading model info:', error);
    }
}

function displayModelInfo(info) {
    // Dataset info
    document.getElementById('datasetInfo').innerHTML = `
        <p><strong>Name:</strong> ${info.dataset_info?.name || '-'}</p>
        <p><strong>Samples:</strong> ${info.dataset_info?.total_samples || '-'}</p>
        <p><strong>Features:</strong> ${info.dataset_info?.feature_count || '-'}</p>
        <p><strong>Classes:</strong> ${info.dataset_info?.classes?.join(', ') || '-'}</p>
    `;

    // Metrics info
    const metrics = info.model_metrics || {};
    document.getElementById('metricsInfo').innerHTML = `
        <p><strong>Accuracy:</strong> ${((metrics.accuracy || 0) * 100).toFixed(2)}%</p>
        <p><strong>Precision:</strong> ${((metrics.precision || 0) * 100).toFixed(2)}%</p>
        <p><strong>Recall:</strong> ${((metrics.recall || 0) * 100).toFixed(2)}%</p>
        <p><strong>F1-Score:</strong> ${((metrics.f1_score || 0) * 100).toFixed(2)}%</p>
        <p><strong>ROC-AUC:</strong> ${((metrics.roc_auc || 0) * 100).toFixed(2)}%</p>
    `;

    // Model details
    document.getElementById('modelDetails').innerHTML = `
        <p><strong>Type:</strong> ${info.model_type || '-'}</p>
        <p><strong>Version:</strong> ${info.version || '-'}</p>
        <p><strong>Status:</strong> Production Ready</p>
        <p><strong>Input Size:</strong> 256×256 pixels</p>
    `;
}

// Load model info on page load
window.addEventListener('load', loadModelInfo);

// ============ MATRIX BACKGROUND ============
function setupMatrixBackground() {
    const container = document.getElementById('matrixContainer');
    if (!container) return;

    const snippets = [
        'const model = new LogisticRegression();',
        'features: [256, 512, 1024]',
        'accuracy: 95.2%',
        'confidence_interval: [0.92, 0.98]',
        'prediction: MALIGNANT',
        'probability: 0.87',
        'diagnosis: MAMMOGRAPHY',
        'classification: BENIGN',
        'score: 0.95',
        'feature_importance: [0.12, 0.08, ...]',
        'roc_auc: 0.975',
        'processing_time: 0.234s'
    ];

    const colors = ['#fb7185', '#0ea5e9', '#10b981', '#f59e0b', '#a855f7'];

    for (let i = 0; i < 20; i++) {
        const div = document.createElement('div');
        div.className = 'matrix-code';
        div.textContent = snippets[Math.floor(Math.random() * snippets.length)];
        div.style.color = colors[Math.floor(Math.random() * colors.length)];
        div.style.left = Math.random() * 100 + '%';
        div.style.top = Math.random() * 100 + '%';
        div.style.animation = `float ${20 + Math.random() * 30}s linear infinite`;
        div.style.animationDelay = Math.random() * 5 + 's';
        
        const style = document.createElement('style');
        style.textContent = `
            @keyframes float {
                0% { transform: translateY(-20px) translateX(0); opacity: 0.4; }
                50% { opacity: 0.1; }
                100% { transform: translateY(${window.innerHeight + 100}px) translateX(50px); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        
        container.appendChild(div);
    }
}

// ============ SMOOTH SCROLL ============
function scrollTo(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}
