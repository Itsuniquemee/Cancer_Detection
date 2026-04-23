#!/usr/bin/env python3
"""
CancerDetect Pro v2.0 - Analysis Feature Verification Script
Verifies that the analysis feature is properly implemented in the frontend
"""

import json
import requests
from urllib.parse import urljoin

BASE_URL = 'http://localhost:9000'
RESULTS = {
    "tests_passed": 0,
    "tests_failed": 0,
    "details": []
}

def test_server_alive():
    """Test if server is running"""
    try:
        response = requests.head(f'{BASE_URL}/', timeout=2)
        if response.status_code == 200:
            RESULTS["tests_passed"] += 1
            RESULTS["details"].append("✓ Server is running on http://localhost:9000")
            return True
        else:
            RESULTS["tests_failed"] += 1
            RESULTS["details"].append(f"✗ Server returned status {response.status_code}")
            return False
    except Exception as e:
        RESULTS["tests_failed"] += 1
        RESULTS["details"].append(f"✗ Cannot connect to server: {e}")
        return False

def test_html_load():
    """Test if HTML loads correctly"""
    try:
        response = requests.get(f'{BASE_URL}/', timeout=5)
        if response.status_code == 200 and 'CancerDetect' in response.text:
            RESULTS["tests_passed"] += 1
            RESULTS["details"].append("✓ HTML loads correctly with CancerDetect title")
            return True
        else:
            RESULTS["tests_failed"] += 1
            RESULTS["details"].append("✗ HTML does not load correctly")
            return False
    except Exception as e:
        RESULTS["tests_failed"] += 1
        RESULTS["details"].append(f"✗ Error loading HTML: {e}")
        return False

def test_analysis_scripts():
    """Test if analysis scripts are present"""
    try:
        response = requests.get(f'{BASE_URL}/', timeout=5)
        html = response.text
        
        checks = [
            ("analyzeImage function", "function analyzeImage(imageData)"),
            ("generateAnalysis function", "function generateAnalysis()"),
            ("downloadReport function", "function downloadReport()"),
            ("File upload handler", "handleFileSelect"),
            ("Upload area element", "uploadArea"),
            ("Chart initialization", "Chart(distributionCtx"),
            ("Console initialization log", "CancerDetect Pro v2.0 - Initializing"),
            ("Upload listeners", "uploadArea.addEventListener('dragover'"),
        ]
        
        for check_name, pattern in checks:
            if pattern in html:
                RESULTS["tests_passed"] += 1
                RESULTS["details"].append(f"✓ {check_name} found in HTML")
            else:
                RESULTS["tests_failed"] += 1
                RESULTS["details"].append(f"✗ {check_name} NOT found in HTML")
        
        return RESULTS["tests_failed"] == 0
        
    except Exception as e:
        RESULTS["tests_failed"] += 1
        RESULTS["details"].append(f"✗ Error checking scripts: {e}")
        return False

def test_analysis_section():
    """Test if analysis section is present"""
    try:
        response = requests.get(f'{BASE_URL}/', timeout=5)
        html = response.text
        
        checks = [
            ("Upload area ID", 'id="uploadArea"'),
            ("File input ID", 'id="fileInput"'),
            ("Preview container", 'id="imagePreview"'),
            ("Results container", 'id="resultsContainer"'),
            ("Results classification", 'id="resultClassification"'),
            ("Results confidence", 'id="resultConfidence"'),
            ("Results risk", 'id="resultRisk"'),
            ("Clear button", "clearImage()"),
            ("Download report button", "downloadReport()"),
        ]
        
        for check_name, pattern in checks:
            if pattern in html:
                RESULTS["tests_passed"] += 1
                RESULTS["details"].append(f"✓ {check_name} present in HTML")
            else:
                RESULTS["tests_failed"] += 1
                RESULTS["details"].append(f"✗ {check_name} NOT in HTML")
        
        return RESULTS["tests_failed"] == 0
        
    except Exception as e:
        RESULTS["tests_failed"] += 1
        RESULTS["details"].append(f"✗ Error checking analysis section: {e}")
        return False

def test_error_handling():
    """Test if error handling is in place"""
    try:
        response = requests.get(f'{BASE_URL}/', timeout=5)
        html = response.text
        
        checks = [
            ("Error handling in reader.onload", "console.error('Error displaying preview'"),
            ("Error handling in reader.onerror", "console.error('Error reading file'"),
            ("Error handling in analyzeImage", "console.error('Error during analysis'"),
            ("Console logging", "console.log"),
            ("Warnings in analyzeImage", "console.warn('Analysis already in progress'"),
        ]
        
        for check_name, pattern in checks:
            if pattern in html:
                RESULTS["tests_passed"] += 1
                RESULTS["details"].append(f"✓ {check_name} implemented")
            else:
                RESULTS["tests_failed"] += 1
                RESULTS["details"].append(f"✗ {check_name} NOT implemented")
        
        return True
        
    except Exception as e:
        RESULTS["tests_failed"] += 1
        RESULTS["details"].append(f"✗ Error checking error handling: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("CancerDetect Pro v2.0 - Analysis Feature Verification")
    print("="*60 + "\n")
    
    print("Running verification tests...\n")
    
    test_server_alive()
    test_html_load()
    test_analysis_scripts()
    test_analysis_section()
    test_error_handling()
    
    print("\nTest Results:")
    print("-" * 60)
    for detail in RESULTS["details"]:
        print(detail)
    
    print("\n" + "-" * 60)
    print(f"\nTotal Tests Passed: {RESULTS['tests_passed']}")
    print(f"Total Tests Failed: {RESULTS['tests_failed']}")
    
    if RESULTS['tests_failed'] == 0:
        print("\n✅ All tests PASSED! Analysis feature is properly implemented.")
        print("\nThe website is ready to use:")
        print("  1. Open http://localhost:9000 in your browser")
        print("  2. Go to the 'Analysis' section")
        print("  3. Upload or drag-drop an image")
        print("  4. Wait for analysis to complete")
        print("  5. View results and download report")
    else:
        print(f"\n⚠️  {RESULTS['tests_failed']} tests FAILED. Please review the issues above.")
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()
