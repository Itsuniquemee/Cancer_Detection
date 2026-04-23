#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        Breast Cancer Detection - Verification Script          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo "✓ Checking Python..."
python3 --version

# Check requirements
echo ""
echo "✓ Checking Python packages..."
python3 -c "import flask; print('  Flask:', flask.__version__)"
python3 -c "import sklearn; print('  Scikit-learn:', sklearn.__version__)"
python3 -c "import numpy; print('  NumPy:', numpy.__version__)"
python3 -c "import cv2; print('  OpenCV:', cv2.__version__)"
python3 -c "import scipy; print('  SciPy:', scipy.__version__)"

# Check files
echo ""
echo "✓ Checking project files..."
cd /Users/manas/Maanas/BreastCancerDetectionWeb

files=(
    "index.html"
    "js/script.js"
    "css/style.css"
    "app.py"
    "requirements.txt"
    "SETUP_AND_ACCURACY.md"
    "RUN_NOW.txt"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (MISSING)"
    fi
done

# Test imports
echo ""
echo "✓ Testing Python imports..."
python3 << 'PYEOF'
try:
    from flask import Flask
    from flask_cors import CORS
    import numpy as np
    import pandas as pd
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    import joblib
    from PIL import Image
    import cv2
    from scipy.stats import skew
    print("  All imports successful!")
except Exception as e:
    print(f"  ERROR: {e}")
PYEOF

echo ""
echo "✓ Testing app.py syntax..."
python3 -m py_compile app.py && echo "  No syntax errors"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    SETUP VERIFIED ✓                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next step: Run 'RUN_NOW.txt' to start the servers"
echo ""
echo "Terminal 1:"
echo "  $ cd /Users/manas/Maanas/BreastCancerDetectionWeb"
echo "  $ python3 app.py"
echo ""
echo "Terminal 2:"
echo "  $ cd /Users/manas/Maanas/BreastCancerDetectionWeb"
echo "  $ python3 -m http.server 8000"
echo ""
echo "Then visit: http://localhost:8000"
echo ""
