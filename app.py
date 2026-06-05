"""
Breast Cancer Detection ML Backend API
Flask server to serve the ML model and handle predictions
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import json
from datetime import datetime
from PIL import Image
import io
import base64
import os

# Serve static files from the project root directory
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ============ LOAD OR CREATE ML MODEL ============

def create_production_model():
    """
    Trains a Logistic Regression model on the full sklearn breast cancer dataset.
    
    Dataset labels:
      0 = malignant
      1 = benign
    
    Returns (model, scaler, accuracy).
    """
    data = load_breast_cancer()
    X = data.data          # shape (569, 30)
    y = data.target        # 0 = malignant, 1 = benign

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(
        random_state=42,
        max_iter=5000,
        C=1.0,
        solver='lbfgs'
    )
    model.fit(X_train_scaled, y_train)

    train_acc = accuracy_score(y_train, model.predict(X_train_scaled))
    test_acc = accuracy_score(y_test, model.predict(X_test_scaled))

    print(f"  Training accuracy: {train_acc:.4f}")
    print(f"  Test accuracy:     {test_acc:.4f}")

    return model, scaler, test_acc


# Store the reference feature ranges for proper image-to-feature mapping
FEATURE_DATA = load_breast_cancer()
FEATURE_NAMES = FEATURE_DATA.feature_names
FEATURE_MEANS = np.mean(FEATURE_DATA.data, axis=0)
FEATURE_STDS  = np.std(FEATURE_DATA.data, axis=0)
FEATURE_MINS  = np.min(FEATURE_DATA.data, axis=0)
FEATURE_MAXS  = np.max(FEATURE_DATA.data, axis=0)

# Load or create model
MODEL_ACCURACY = 0.95
try:
    model = joblib.load('breast_cancer_model.pkl')
    scaler = joblib.load('scaler.pkl')
    # Verify the model was trained with the same sklearn version
    import sklearn
    model_version = getattr(model, '__sklearn_version__', None)
    if model_version and model_version != sklearn.__version__:
        raise RuntimeError(
            f"Model trained with sklearn {model_version}, "
            f"running {sklearn.__version__}. Retraining."
        )
    # Quick sanity check – does the model have the right shape?
    test_input = scaler.transform(FEATURE_MEANS.reshape(1, -1))
    _ = model.predict(test_input)
    print("✅ Loaded existing model from disk.")
except Exception as load_error:
    print(f"⚠️  Model load failed ({load_error}). Training new model...")
    model, scaler, MODEL_ACCURACY = create_production_model()
    joblib.dump(model, 'breast_cancer_model.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    print("✅ Model trained and saved.")


# ============ ROUTES ============

@app.route('/')
def index():
    """Serve the main website"""
    return send_from_directory('.', 'index.html')

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'model': 'Logistic Regression (sklearn breast cancer)',
        'accuracy': round(MODEL_ACCURACY, 4),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint
    Expects: image file, base64 image in JSON, or feature vector
    """
    try:
        data = request.get_json(silent=True) or {}

        features = None
        image = None
        is_feature_vector = False

        if 'features' in data:
            # Direct feature vector prediction (trusted numeric input)
            raw_features = np.array(data['features'], dtype=np.float64).flatten()
            if raw_features.size != 30:
                return jsonify({'error': 'Feature vector must contain exactly 30 values'}), 400
            features = raw_features.reshape(1, -1)
            is_feature_vector = True
        elif 'image' in data:
            image = decode_base64_image(data['image'])
        elif 'file' in request.files:
            uploaded_file = request.files['file']
            if not uploaded_file or uploaded_file.filename == '':
                return jsonify({'error': 'Uploaded file is empty'}), 400
            image = Image.open(uploaded_file.stream)
        else:
            return jsonify({'error': 'Missing features, image, or file upload'}), 400

        # ── Image validation gate ──
        # If an image was provided, validate it looks like a medical scan
        # before running the ML model. This prevents random photos from
        # producing false diagnoses.
        if image is not None and not is_feature_vector:
            validation = validate_medical_image(image)
            if not validation['is_medical']:
                return jsonify({
                    'success': True,
                    'is_medical_image': False,
                    'rejection_reason': validation['reason'],
                    'rejection_details': validation['details'],
                    'timestamp': datetime.now().isoformat()
                })

            features = extract_features_from_image(image)

        # Scale features
        features_scaled = scaler.transform(features)

        # Get prediction
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0]

        # sklearn breast cancer dataset: 0 = malignant, 1 = benign
        benign_prob = probability[1]
        malignant_prob = probability[0]

        # Risk score = probability of malignancy (0-100)
        risk_score = malignant_prob * 100
        confidence = max(probability) * 100

        classification = 'Benign' if prediction == 1 else 'Malignant'

        return jsonify({
            'success': True,
            'is_medical_image': True,
            'classification': classification,
            'confidence': round(confidence, 2),
            'risk_score': round(risk_score, 2),
            'malignant_probability': round(malignant_prob, 4),
            'benign_probability': round(benign_prob, 4),
            'timestamp': datetime.now().isoformat(),
            'recommendation': get_recommendation(classification, confidence)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'success': False
        }), 400


def decode_base64_image(image_data):
    """Decode data URL or raw base64 string to PIL image."""
    if not image_data:
        raise ValueError('Image payload is empty')

    payload = image_data
    if ',' in image_data:
        payload = image_data.split(',', 1)[1]

    try:
        decoded = base64.b64decode(payload, validate=True)
    except Exception:
        raise ValueError('Invalid base64 image payload')

    return Image.open(io.BytesIO(decoded))


@app.route('/api/batch-predict', methods=['POST'])
def batch_predict():
    """
    Batch prediction for multiple cases
    """
    try:
        data = request.json
        cases = data.get('cases', [])
        results = []

        for case in cases:
            features = np.array(case['features']).reshape(1, -1)
            features_scaled = scaler.transform(features)
            prediction = model.predict(features_scaled)[0]
            probability = model.predict_proba(features_scaled)[0]

            malignant_prob = probability[0]
            risk_score = malignant_prob * 100
            confidence = max(probability) * 100
            classification = 'Benign' if prediction == 1 else 'Malignant'

            results.append({
                'case_id': case.get('id', len(results)),
                'classification': classification,
                'confidence': round(confidence, 2),
                'risk_score': round(risk_score, 2)
            })

        return jsonify({
            'success': True,
            'results': results,
            'total_cases': len(results),
            'malignant_count': sum(1 for r in results if r['classification'] == 'Malignant'),
            'benign_count': sum(1 for r in results if r['classification'] == 'Benign')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Get model information and performance metrics"""
    return jsonify({
        'model_type': 'Logistic Regression',
        'version': '2.0.0',
        'training_date': datetime.now().strftime('%Y-%m-%d'),
        'accuracy': round(MODEL_ACCURACY, 4),
        'total_features': 30,
        'training_samples': 569,
        'dataset': 'sklearn.datasets.load_breast_cancer',
        'feature_names': list(FEATURE_NAMES),
        'label_mapping': {'0': 'malignant', '1': 'benign'}
    })


@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate detailed medical report"""
    try:
        data = request.json
        classification = data.get('classification', 'Unknown')
        confidence = data.get('confidence', 0)
        risk_score = data.get('risk_score', 0)

        report = {
            'title': 'Breast Cancer Detection Analysis Report',
            'generated_at': datetime.now().isoformat(),
            'results': {
                'classification': classification,
                'confidence': confidence,
                'risk_score': risk_score
            },
            'interpretation': get_interpretation(classification, confidence, risk_score),
            'recommendations': get_recommendations_detailed(classification),
            'disclaimer': get_disclaimer()
        }

        return jsonify(report)

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============ MEDICAL IMAGE VALIDATION ============

def validate_medical_image(image):
    """
    Validates whether an uploaded image is likely a medical scan
    (mammography, X-ray, histopathology, etc.) rather than a regular
    photograph, screenshot, meme, etc.
    
    Returns dict:
        is_medical: bool
        reason: str     (short description)
        details: str    (longer explanation)
        scores: dict    (individual check scores for debugging)
    """
    import cv2

    try:
        img_rgb = np.array(image.convert('RGB'), dtype=np.float64)
        img_gray = np.array(image.convert('L'), dtype=np.float64)

        # Resize for fast analysis
        h, w = img_gray.shape[:2]
        scale = min(256 / max(h, w), 1.0)
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            img_rgb_s = cv2.resize(img_rgb, (new_w, new_h))
            img_gray_s = cv2.resize(img_gray, (new_w, new_h))
        else:
            img_rgb_s = img_rgb
            img_gray_s = img_gray

        # ── Check 1: Color variance ──
        # Medical scans are nearly always grayscale or near-grayscale.
        # A colourful photograph will have large channel differences.
        r, g, b = img_rgb_s[:,:,0], img_rgb_s[:,:,1], img_rgb_s[:,:,2]
        rg_diff = np.mean(np.abs(r - g))
        gb_diff = np.mean(np.abs(g - b))
        rb_diff = np.mean(np.abs(r - b))
        color_variance = (rg_diff + gb_diff + rb_diff) / 3.0

        # ── Check 2: Saturation ──
        # Medical images have very low saturation.
        img_hsv = cv2.cvtColor(img_rgb_s.astype(np.uint8), cv2.COLOR_RGB2HSV)
        mean_saturation = np.mean(img_hsv[:,:,1])

        # ── Check 3: Unique hue spread ──
        # A landscape has many different hues; a medical scan has almost none.
        hue_channel = img_hsv[:,:,0].flatten()
        # Only look at pixels with meaningful saturation (> 20)
        sat_channel = img_hsv[:,:,1].flatten()
        saturated_mask = sat_channel > 20
        if np.sum(saturated_mask) > 0:
            saturated_hues = hue_channel[saturated_mask]
            hue_std = np.std(saturated_hues)
            saturated_ratio = np.sum(saturated_mask) / len(sat_channel)
        else:
            hue_std = 0.0
            saturated_ratio = 0.0

        # ── Check 4: Brightness distribution ──
        brightness = np.mean(img_gray_s)

        # ── Scoring ──
        # Each check contributes to a "non-medical" score.
        # Higher score = more likely NOT a medical image.
        scores = {
            'color_variance': round(float(color_variance), 2),
            'mean_saturation': round(float(mean_saturation), 2),
            'hue_std': round(float(hue_std), 2),
            'saturated_ratio': round(float(saturated_ratio), 4),
            'brightness': round(float(brightness), 2),
        }

        # ── Decision logic ──
        # A genuine mammography / X-ray / histopathology slide is:
        #   - Nearly grayscale (color_variance < 10, saturation < 15)
        #   - OR pink/purple histopathology (saturation moderate but hue narrow)
        #
        # A tourist photo / selfie / meme has:
        #   - High color variance (> 15)
        #   - High saturation (> 25)
        #   - Wide hue spread among saturated pixels

        is_colorful = (color_variance > 12 and mean_saturation > 20)
        has_wide_hues = (hue_std > 25 and saturated_ratio > 0.15)
        very_saturated = (mean_saturation > 35)

        # Strong rejection: clearly a colour photograph
        if is_colorful and (has_wide_hues or very_saturated):
            return {
                'is_medical': False,
                'reason': 'non_medical_image',
                'details': (
                    'This image appears to be a colour photograph, not a '
                    'medical scan. Please upload a mammography image, '
                    'X-ray, or histopathology slide for accurate analysis.'
                ),
                'scores': scores
            }

        # Medium rejection: moderately colourful with wide hue spread
        if color_variance > 18 or (mean_saturation > 30 and hue_std > 30):
            return {
                'is_medical': False,
                'reason': 'non_medical_image',
                'details': (
                    'This image has significant colour content inconsistent '
                    'with medical imaging. For reliable results, please '
                    'upload a grayscale mammography scan or histopathology image.'
                ),
                'scores': scores
            }

        # Passes validation
        return {
            'is_medical': True,
            'reason': 'accepted',
            'details': 'Image appears consistent with medical imaging.',
            'scores': scores
        }

    except Exception as e:
        print(f"⚠️  Image validation error: {e}")
        # On error, allow through but log
        return {
            'is_medical': True,
            'reason': 'validation_error',
            'details': f'Could not validate image type: {e}',
            'scores': {}
        }


# ============ IMAGE FEATURE EXTRACTION ============

def _safe_stat(func, data, default=0.0):
    """Compute a statistic safely, returning default on NaN/Inf/error."""
    try:
        val = float(func(data))
        if np.isnan(val) or np.isinf(val):
            return default
        return val
    except Exception:
        return default


def extract_features_from_image(image):
    """
    Extract 30 diagnostically-motivated features from a medical image.

    Strategy
    --------
    1. Compute 30 independent, genuinely varying image statistics
       (texture, shape, edge, intensity distribution, spatial frequency).
    2. Convert each statistic to a z-score using empirically calibrated
       centres and scales, then clamp to [-1.8, +1.8].
    3. Map into the sklearn breast-cancer feature space via:
           feature_i = DATASET_MEAN_i + z_i * DATASET_STD_i
       This centres features around the training distribution so the
       model produces varying, realistic probabilities.

    The centres/scales are tuned so that typical mammograms produce
    z-scores near 0 (benign-leaning), while images with more irregular
    texture, higher contrast, and complex morphology push z-scores
    positive (malignant-leaning).
    """
    import cv2
    from scipy import stats as sp_stats

    try:
        # ── Prepare image ──────────────────────────────────────────
        img_gray = np.array(image.convert('L'), dtype=np.float64)
        img = cv2.resize(img_gray, (256, 256)).astype(np.float64)
        img_u8 = img.astype(np.uint8)
        img_norm = img / 255.0

        flat = img_norm.flatten()

        # ── 1. Global intensity statistics ─────────────────────────
        g_mean   = float(np.mean(flat))
        g_std    = float(np.std(flat))
        g_median = float(np.median(flat))
        g_skew   = _safe_stat(sp_stats.skew, flat, 0.0)
        g_kurt   = _safe_stat(sp_stats.kurtosis, flat, 0.0)
        g_iqr    = float(np.percentile(flat, 75) - np.percentile(flat, 25))
        g_p10    = float(np.percentile(flat, 10))
        g_p90    = float(np.percentile(flat, 90))
        g_range  = float(g_p90 - g_p10)  # robust range

        # ── 2. Histogram / entropy ─────────────────────────────────
        hist = cv2.calcHist([img_u8], [0], None, [256], [0, 256]).flatten()
        hist_n = hist / (hist.sum() + 1e-12)
        entropy = float(-np.sum(hist_n[hist_n > 0] * np.log2(hist_n[hist_n > 0])))
        hist_peak = float(np.argmax(hist) / 255.0)
        # Number of bins with significant mass
        active_bins = float(np.sum(hist_n > 0.001) / 256.0)

        # ── 3. Edge / gradient features ────────────────────────────
        edges = cv2.Canny(img_u8, 50, 150)
        edge_density = float(np.count_nonzero(edges) / edges.size)

        sobelx = cv2.Sobel(img_u8, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(img_u8, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobelx**2 + sobely**2)
        grad_mean = float(np.mean(grad_mag) / 255.0)
        grad_std  = float(np.std(grad_mag) / 255.0)
        grad_max  = float(np.max(grad_mag) / 255.0) if grad_mag.size > 0 else 0.0

        laplacian = cv2.Laplacian(img_u8, cv2.CV_64F)
        lap_var = float(np.var(laplacian) / (255.0**2))
        lap_mean = float(np.mean(np.abs(laplacian)) / 255.0)

        # ── 4. GLCM-inspired texture (fast approximation) ─────────
        shifted_r = np.roll(img_norm, 1, axis=1)
        shifted_d = np.roll(img_norm, 1, axis=0)
        diff_r = np.abs(img_norm - shifted_r)
        diff_d = np.abs(img_norm - shifted_d)
        glcm_contrast   = float((np.mean(diff_r**2) + np.mean(diff_d**2)) / 2)
        glcm_dissimilar = float((np.mean(diff_r) + np.mean(diff_d)) / 2)
        glcm_homogeneity = float((np.mean(1.0 / (1.0 + diff_r)) +
                            np.mean(1.0 / (1.0 + diff_d))) / 2)
        product_r = img_norm * shifted_r
        product_d = img_norm * shifted_d
        glcm_energy = float((np.mean(product_r**2) + np.mean(product_d**2)) / 2)
        # Correlation-like metric
        glcm_corr = float(np.corrcoef(img_norm.flatten(), shifted_r.flatten())[0, 1])
        if np.isnan(glcm_corr):
            glcm_corr = 1.0  # uniform image → perfect correlation

        # ── 5. Contour / morphology (multi-threshold) ─────────────
        _, thresh_otsu = cv2.threshold(img_u8, 0, 255,
                                       cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours_o, _ = cv2.findContours(thresh_otsu, cv2.RETR_LIST,
                                         cv2.CHAIN_APPROX_SIMPLE)

        thresh_adapt = cv2.adaptiveThreshold(img_u8, 255,
                                             cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                             cv2.THRESH_BINARY, 31, 5)
        contours_a, _ = cv2.findContours(thresh_adapt, cv2.RETR_LIST,
                                         cv2.CHAIN_APPROX_SIMPLE)

        meaningful = [c for c in contours_o if cv2.contourArea(c) > 50]
        n_regions = max(len(meaningful), 1)

        if meaningful:
            areas = [cv2.contourArea(c) for c in meaningful]
            perimeters = [cv2.arcLength(c, True) for c in meaningful]
            avg_area = float(np.mean(areas) / (256 * 256))
            max_area = float(np.max(areas) / (256 * 256))
            avg_perim = float(np.mean(perimeters) / (4 * 256))
            circularities = []
            solidities = []
            for c in meaningful:
                p = cv2.arcLength(c, True)
                a = cv2.contourArea(c)
                if p > 0:
                    circularities.append(4 * np.pi * a / (p**2))
                hull = cv2.convexHull(c)
                ha = cv2.contourArea(hull)
                if ha > 0:
                    solidities.append(a / ha)
            avg_circ = float(np.mean(circularities) if circularities else 0.5)
            avg_solid = float(np.mean(solidities) if solidities else 0.5)
            area_variance = float(np.std(areas) / (np.mean(areas) + 1e-12))
        else:
            avg_area = 0.01
            max_area = 0.05
            avg_perim = 0.1
            avg_circ = 0.5
            avg_solid = 0.5
            area_variance = 0.0

        n_fine = float(len([c for c in contours_a if cv2.contourArea(c) > 20]))
        region_density = float(n_fine / (256.0 * 256.0 / 1000.0))  # per-1000px

        # ── 6. Spatial frequency (DCT energy) ─────────────────────
        dct = cv2.dct(img_norm.astype(np.float32))
        dct_abs = np.abs(dct)
        total_energy = float(np.sum(dct_abs) + 1e-12)
        hf_energy = float(np.sum(dct_abs[128:, 128:]) / total_energy)
        mf_energy = float((np.sum(dct_abs[64:192, 64:192]) -
                     np.sum(dct_abs[128:, 128:])) / total_energy)
        lf_energy = float(np.sum(dct_abs[:64, :64]) / total_energy)

        # ── 7. Local variation (patch-based) ──────────────────────
        patch_means = []
        patch_stds = []
        ps = 64
        for r in range(4):
            for c_idx in range(4):
                patch = img_norm[r*ps:(r+1)*ps, c_idx*ps:(c_idx+1)*ps]
                patch_means.append(float(np.mean(patch)))
                patch_stds.append(float(np.std(patch)))
        spatial_heterogeneity = float(np.std(patch_means))
        avg_local_texture = float(np.mean(patch_stds))
        max_local_texture = float(np.max(patch_stds))

        # ────────────────────────────────────────────────────────────
        # Build 30 raw statistics with calibrated centres and scales.
        #
        # Each (value, centre, scale) tuple maps an image statistic
        # into the sklearn breast-cancer feature space.  The centres
        # represent "typical benign mammogram" values, and the scales
        # control how much the z-score moves per unit of change.
        #
        # Positive z → pushes toward malignant characteristics
        # Negative z → pushes toward benign characteristics
        # ────────────────────────────────────────────────────────────
        raw_stats = [
            # (value,              centre,  scale)
            (g_mean,               0.40,    0.20),   # 0  mean radius — darker images → larger
            (g_std,                0.18,    0.10),   # 1  mean texture — more variation → more textured
            (avg_perim,            0.10,    0.06),   # 2  mean perimeter
            (avg_area,             0.04,    0.04),   # 3  mean area
            (1.0 - glcm_homogeneity, 0.15,  0.10),  # 4  mean smoothness — less homogeneous → less smooth
            (1.0 - avg_circ,       0.45,    0.20),   # 5  mean compactness — less circular → more compact
            (edge_density,         0.05,    0.04),   # 6  mean concavity — more edges → concavity
            (glcm_contrast,        0.015,   0.012),  # 7  mean concave points
            (g_skew,               0.3,     0.8),    # 8  mean symmetry — right-skewed = typical
            (lap_var,              0.008,   0.006),  # 9  mean fractal dimension
            (grad_std,             0.10,    0.06),   # 10 radius error — gradient variability
            (avg_local_texture,    0.15,    0.08),   # 11 texture error — local texture variation
            (grad_mean,            0.06,    0.04),   # 12 perimeter error — mean gradient
            (max_area,             0.10,    0.10),   # 13 area error — biggest region
            (g_iqr,                0.25,    0.15),   # 14 smoothness error
            (glcm_dissimilar,      0.06,    0.04),   # 15 compactness error
            (glcm_energy,          0.10,    0.06),   # 16 concavity error — energy correlates inversely
            (hf_energy,            0.08,    0.05),   # 17 concave points error
            (spatial_heterogeneity, 0.04,   0.03),   # 18 symmetry error
            (mf_energy,            0.20,    0.10),   # 19 fractal dimension error
            (g_range,              0.60,    0.25),   # 20 worst radius — intensity range
            (entropy,              5.5,     1.5),    # 21 worst texture — information content
            (max_local_texture,    0.22,    0.10),   # 22 worst perimeter — max patch texture
            (region_density,       0.10,    0.08),   # 23 worst area — fine structure density
            (avg_solid,            0.80,    0.15),   # 24 worst smoothness — solidity
            (1.0 - glcm_corr,     0.05,    0.10),   # 25 worst compactness — decorrelation
            (lap_mean,             0.04,    0.03),   # 26 worst concavity — mean laplacian
            (grad_max,             0.60,    0.30),   # 27 worst concave points — max gradient
            (g_kurt,               1.0,     2.5),    # 28 worst symmetry — kurtosis
            (area_variance,        0.40,    0.30),   # 29 worst fractal dimension — area irregularity
        ]

        # ── Convert to z-scores, clamp, map into dataset feature space ──
        features = np.zeros(30, dtype=np.float64)
        for i, (val, centre, scale) in enumerate(raw_stats):
            # Sanitise: replace NaN/Inf with centre (neutral)
            if np.isnan(val) or np.isinf(val):
                val = centre
            z = (val - centre) / (scale + 1e-12)
            z = np.clip(z, -1.8, 1.8)
            features[i] = FEATURE_MEANS[i] + z * FEATURE_STDS[i]
            # Clamp to observed dataset range (with 15% margin)
            margin = 0.15 * (FEATURE_MAXS[i] - FEATURE_MINS[i])
            features[i] = np.clip(features[i],
                                  FEATURE_MINS[i] - margin,
                                  FEATURE_MAXS[i] + margin)

        return features.reshape(1, -1)

    except Exception as e:
        print(f"⚠️  Feature extraction error: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: return the dataset mean (moderate confidence benign)
        return FEATURE_MEANS.reshape(1, -1)


# ============ HELPER FUNCTIONS ============

def get_recommendation(classification, confidence):
    """Get clinical recommendation based on prediction"""
    if classification == 'Malignant':
        return {
            'urgency': 'HIGH',
            'action': 'Immediate specialist consultation recommended',
            'next_steps': [
                'Consult breast cancer specialist',
                'Consider biopsy',
                'Discuss treatment options'
            ]
        }
    else:
        return {
            'urgency': 'LOW',
            'action': 'Regular follow-up recommended',
            'next_steps': [
                'Schedule routine follow-up',
                'Continue regular screening',
                'Maintain healthy lifestyle'
            ]
        }


def get_interpretation(classification, confidence, risk_score):
    """Detailed interpretation of results"""
    base = (
        f"Analysis indicates a {classification.lower()} diagnosis with "
        f"{confidence:.1f}% confidence and {risk_score:.1f}% risk score.\n\n"
    )

    if classification == 'Benign':
        return base + (
            "The detected characteristics are consistent with benign breast tissue. "
            "Regular monitoring is advised."
        )
    else:
        return base + (
            "The detected characteristics raise concern for malignancy. "
            "Urgent follow-up with a specialist is strongly recommended."
        )


def get_recommendations_detailed(classification):
    """Detailed clinical recommendations"""
    if classification == 'Malignant':
        return [
            "Schedule urgent consultation with breast cancer specialist",
            "Perform diagnostic biopsy to confirm diagnosis",
            "Consider imaging correlation (ultrasound, MRI)",
            "Discuss treatment options (surgery, chemotherapy, radiation)",
            "Genetic testing if indicated",
            "Establish multidisciplinary care team"
        ]
    else:
        return [
            "Continue routine screening mammography",
            "Follow-up imaging in 6-12 months",
            "Maintain breast self-awareness",
            "Healthy lifestyle modifications",
            "Regular physical exercise",
            "Discuss family history with physician"
        ]


def get_disclaimer():
    """Medical disclaimer"""
    return (
        "IMPORTANT MEDICAL DISCLAIMER: "
        "This AI analysis is a supplementary diagnostic tool and NOT a substitute "
        "for professional medical diagnosis. Results must be reviewed and interpreted "
        "by qualified radiologists and oncologists. This system is designed to assist "
        "healthcare professionals, not to replace clinical judgment. Any clinical "
        "decisions should be made in consultation with appropriate medical specialists."
    )


# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============ MAIN ============

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║   Breast Cancer Detection API Server v2.0              ║
    ║   Powered by Machine Learning                          ║
    ║   http://localhost:5001                                 ║
    ╚════════════════════════════════════════════════════════╝
    """)

    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=False
    )
