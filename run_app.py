#!/usr/bin/env python3
"""
Simplified Flask app for CancerDetect Pro v2.0
"""
from flask import Flask, jsonify, request, send_from_directory
import os
import json
import pickle
import numpy as np
from datetime import datetime
import logging

# Setup
app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = '/tmp'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'cancer_detect.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load ML model
try:
    model = pickle.load(open(os.path.join(BASE_DIR, 'breast_cancer_model.pkl'), 'rb'))
    scaler = pickle.load(open(os.path.join(BASE_DIR, 'scaler.pkl'), 'rb'))
    logger.info("✓ ML model loaded")
except Exception as e:
    logger.error(f"✗ Failed to load model: {e}")
    model = scaler = None

# Routes
@app.route('/')
def serve_index():
    """Serve main HTML"""
    html_file = os.path.join(BASE_DIR, 'index_production.html')
    logger.info(f"=== SERVING ===")
    logger.info(f"File path: {html_file}")
    logger.info(f"File exists: {os.path.exists(html_file)}")
    logger.info(f"File size: {os.path.getsize(html_file) if os.path.exists(html_file) else 'N/A'}")
    
    if not os.path.exists(html_file):
        logger.error(f"HTML file not found: {html_file}")
        return "Error: HTML file not found", 404
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # Log first 200 chars and check for keywords
        logger.info(f"First 200 chars: {content[:200]}")
        logger.info(f"Contains 'CancerDetect': {'CancerDetect' in content}")
        logger.info(f"Contains 'GramCare': {'GramCare' in content}")
        return content

@app.route('/css/<filename>')
def serve_css(filename):
    """Serve CSS files"""
    css_dir = os.path.join(BASE_DIR, 'css')
    return send_from_directory(css_dir, filename)

@app.route('/js/<filename>')
def serve_js(filename):
    """Serve JS files"""
    js_dir = os.path.join(BASE_DIR, 'js')
    return send_from_directory(js_dir, filename)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model': 'LogisticRegression' if model else 'Not loaded'
    })

@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Get model information"""
    return jsonify({
        'name': 'Breast Cancer Detection Model',
        'version': '2.0.0',
        'algorithm': 'Logistic Regression',
        'accuracy': 0.9561,
        'features': 30,
        'classes': ['Benign', 'Malignant'],
        'training_samples': 569,
        'deployment_date': '2024-04-23'
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """Make a prediction"""
    try:
        data = request.get_json()
        if 'features' not in data:
            return jsonify({'error': 'Missing features'}), 400
        
        features = np.array(data['features']).reshape(1, -1)
        
        # Predict
        scaled = scaler.transform(features)
        prediction = model.predict(scaled)[0]
        probability = model.predict_proba(scaled)[0]
        
        return jsonify({
            'prediction': 'Malignant' if prediction == 1 else 'Benign',
            'confidence': float(probability[prediction]),
            'probability_benign': float(probability[0]),
            'probability_malignant': float(probability[1]),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404: {request.path}")
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500: {e}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting CancerDetect Pro API...")
    logger.info(f"Serving from: {BASE_DIR}")
    app.run(host='127.0.0.1', port=9000, debug=False, use_reloader=False)
