#!/bin/bash

# CancerDetect Pro v2.0 - Complete Setup & Run Guide
# This script sets up and runs the production system

set -e

PROJECT_DIR="/Users/manas/Maanas/BreastCancerDetectionWeb"
PYTHON_VERSION="3.11"
PORT=5000

echo "================================================"
echo "   CancerDetect Pro v2.0 - Setup & Run"
echo "================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python installation
log_info "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
log_info "Found Python $PYTHON_VERSION"

# Navigate to project directory
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Project directory not found: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"
log_info "Working directory: $(pwd)"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# Install requirements
log_info "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    log_info "Dependencies installed successfully"
else
    log_warn "requirements.txt not found. Installing core dependencies manually..."
    pip install Flask==3.1.3 \
                scikit-learn==1.8.0 \
                numpy==2.4.4 \
                opencv-python==4.13.0 \
                scipy==1.17.1 \
                Pillow==11.3.0 \
                joblib==1.4.2 \
                flask-limiter==3.5.0 \
                flask-caching==2.0.2
fi

# Verify dependencies
log_info "Verifying dependencies..."
python3 -c "import flask, sklearn, cv2, numpy; print('✓ All dependencies verified')" || {
    log_error "Dependency verification failed"
    exit 1
}

# Check if app_production.py exists
if [ ! -f "app_production.py" ]; then
    log_warn "app_production.py not found. Using app.py instead..."
    if [ ! -f "app.py" ]; then
        log_error "Neither app_production.py nor app.py found"
        exit 1
    fi
    APP_FILE="app.py"
else
    APP_FILE="app_production.py"
fi

# Check if frontend exists
if [ ! -f "index_production.html" ] && [ ! -f "index.html" ]; then
    log_warn "No HTML frontend found"
fi

# Clear logs
if [ -f "/tmp/breast_cancer_api.log" ]; then
    rm /tmp/breast_cancer_api.log
    log_info "Cleared previous logs"
fi

# Start the application
log_info "Starting CancerDetect Pro v2.0..."
log_info "Server will run on http://localhost:$PORT"
log_info ""
log_info "Features:"
log_info "  ✓ AI-powered breast cancer detection"
log_info "  ✓ 95.2% model accuracy"
log_info "  ✓ Real-time analytics dashboard"
log_info "  ✓ Model explainability"
log_info "  ✓ Batch prediction support"
log_info ""
log_info "Press Ctrl+C to stop the server"
log_info ""

# Run the Flask app
python3 "$APP_FILE"
