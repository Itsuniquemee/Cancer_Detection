# CancerDetect AI - Setup & Deployment Guide

## Quick Start (5 Minutes)

### Option 1: Frontend Only (No Backend Needed)
```bash
# Simply open in browser
cd /Users/manas/Maanas/BreastCancerDetectionWeb
open index.html

# Or use Python HTTP server
python3 -m http.server 8000
# Visit: http://localhost:8000
```

**Note**: Without backend, the detector will show simulated results.

### Option 2: Full Stack (With ML Backend)

#### Step 1: Install Python Dependencies
```bash
cd /Users/manas/Maanas/BreastCancerDetectionWeb
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Step 2: Start Backend Server
```bash
# Development
python app.py
# Server runs on http://localhost:5000

# Or production with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Step 3: Open in Browser
- Frontend: http://localhost:5000 (serves both frontend + API)
- API Health: http://localhost:5000/api/health

---

## Full Installation Instructions

### Prerequisites
- Python 3.9+
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Safari, Edge)
- 2GB RAM minimum
- 500MB disk space

### Windows Installation
```bash
# 1. Open Command Prompt or PowerShell

# 2. Navigate to project
cd C:\Users\YourName\Maanas\BreastCancerDetectionWeb

# 3. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run backend
python app.py

# 6. Open browser
# http://localhost:5000
```

### macOS Installation
```bash
# 1. Open Terminal

# 2. Navigate to project
cd /Users/manas/Maanas/BreastCancerDetectionWeb

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run backend
python app.py

# 6. Open browser
# http://localhost:5000
```

### Linux Installation
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-venv

# Navigate and install
cd /home/user/BreastCancerDetectionWeb
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

## Configuration

### Development vs Production

#### Development (.env)
```env
FLASK_ENV=development
DEBUG=True
MODEL_PATH=./breast_cancer_model.pkl
```

#### Production (.env)
```env
FLASK_ENV=production
DEBUG=False
MODEL_PATH=/opt/models/breast_cancer_model.pkl
```

### API Configuration
Edit `app.py` to:
- Change server port: Line 130 `port=5000`
- Enable debug mode: Line 129 `debug=True`
- Adjust CORS settings: Line 5 `CORS(app)`

---

## ML Model Integration

### Using Your Own Model

#### Step 1: Export from Jupyter Notebook
```python
import joblib

# Save trained model
joblib.dump(your_model, 'breast_cancer_model.pkl')
joblib.dump(your_scaler, 'scaler.pkl')
```

#### Step 2: Place in Project Root
```
BreastCancerDetectionWeb/
├── breast_cancer_model.pkl  <- Your model here
├── scaler.pkl               <- Your scaler here
└── app.py
```

#### Step 3: Restart Backend
```bash
python app.py
```

The system will automatically load your model instead of creating a demo one.

### Model Requirements
- Input: 30 features or image (for CNN-based models)
- Output: Probability scores [benign_prob, malignant_prob]
- Format: sklearn-compatible (pickle) or ONNX

---

## Docker Deployment

### Build Docker Image
```bash
cd /Users/manas/Maanas/BreastCancerDetectionWeb

# Build
docker build -t cancerdetect:latest .

# Run
docker run -p 5000:5000 cancerdetect:latest
```

### Docker Compose
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./breast_cancer_model.pkl:/app/breast_cancer_model.pkl
```

---

## Cloud Deployment

### Heroku
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
heroku login
heroku create cancerdetect-app
git push heroku main
heroku logs --tail
```

### AWS (Using Elastic Beanstalk)
```bash
eb init -p python-3.9 cancerdetect-app
eb create cancerdetect-env
eb deploy
```

### Google Cloud Run
```bash
gcloud run deploy cancerdetect --source .
```

### Azure App Service
```bash
az webapp up --name cancerdetect-app --runtime python:3.9
```

---

## Testing

### API Testing with curl

#### Health Check
```bash
curl http://localhost:5000/api/health
```

#### Prediction with Features
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": [1.2, 3.4, 2.1, 5.0, 0.8, 0.3, 0.2, 0.1, 0.9, 0.4,
                1.1, 2.5, 1.8, 4.5, 0.7, 0.2, 0.15, 0.08, 0.85, 0.35,
                1.3, 3.6, 2.3, 5.5, 0.9, 0.35, 0.25, 0.12, 0.95, 0.45]
  }'
```

#### Model Information
```bash
curl http://localhost:5000/api/model-info
```

#### Batch Prediction
```bash
curl -X POST http://localhost:5000/api/batch-predict \
  -H "Content-Type: application/json" \
  -d '{
    "cases": [
      {"id": "case_1", "features": [...]},
      {"id": "case_2", "features": [...]}
    ]
  }'
```

### Frontend Testing
1. Open http://localhost:5000 in browser
2. Test image upload (drag-drop or click)
3. Click "Analyze Image" button
4. Verify results display
5. Download report
6. Test responsive design (resize window)

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
python app.py --port 5001
```

### ModuleNotFoundError: No module named 'flask'
```bash
# Ensure venv is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Model Files Not Found
```bash
# Ensure files are in project root
ls -la breast_cancer_model.pkl scaler.pkl

# Create symbolic link if in different location
ln -s /path/to/model.pkl ./breast_cancer_model.pkl
```

### CORS Errors in Frontend
Edit app.py line 5:
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["localhost:5000", "yourdomain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

### Slow Predictions
1. Increase Gunicorn workers: `-w 8` instead of `-w 4`
2. Use GPU acceleration (if available): Set model to use CUDA
3. Implement caching for repeated predictions
4. Profile with: `python -m cProfile app.py`

---

## Performance Optimization

### Backend
- Gunicorn workers: 4-8 (match CPU cores)
- Model caching: Already implemented
- Request timeouts: 120s (adjust as needed)
- Batch prediction: Process multiple images in one request

### Frontend
- Image compression: Automatically done in JavaScript
- CSS animations: Use GPU with `will-change`
- Lazy loading: Images load on demand
- Minification: Production CSS/JS should be minified

---

## Security Best Practices

### Before Production
- [ ] Enable HTTPS (use Let's Encrypt)
- [ ] Set `DEBUG = False` in production
- [ ] Use environment variables for secrets
- [ ] Implement authentication for sensitive endpoints
- [ ] Add rate limiting to prevent abuse
- [ ] Validate all file uploads
- [ ] Sanitize user inputs
- [ ] Regular security updates: `pip list --outdated`

### HIPAA Compliance (Healthcare)
- [ ] Patient data encryption (in transit & at rest)
- [ ] Audit logging of all predictions
- [ ] Access control (role-based)
- [ ] Data retention policy
- [ ] Regular security audits
- [ ] Business Associate Agreement (BAA)

---

## Monitoring & Maintenance

### Logging
```python
# Check logs in production
tail -f logs/app.log

# Gunicorn access logs
gunicorn --access-logfile - app:app
```

### Metrics
- Track prediction accuracy against ground truth
- Monitor response times
- Log error rates
- Alert on high failure rates

### Updates
```bash
# Check for outdated packages
pip list --outdated

# Update all packages
pip install --upgrade -r requirements.txt
```

---

## Support & Documentation

- **API Docs**: http://localhost:5000/api/health
- **Model Info**: http://localhost:5000/api/model-info
- **GitHub Issues**: https://github.com/example/cancerdetect/issues
- **Email Support**: support@example.com

---

## License

Proprietary Medical AI Software © 2024
See LICENSE file for details

---

**Happy deploying! 🚀**
