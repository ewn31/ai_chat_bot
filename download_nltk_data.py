#!/usr/bin/env python3
"""
Download required NLTK data packages for the chatbot.
This script should be run during deployment to pre-download NLTK data.
"""

import os
import nltk
import sys

def download_nltk_data():
    """Download all required NLTK packages."""

    # Set NLTK data path to application directory
    nltk_data_dir = os.path.join(os.path.dirname(__file__), 'nltk_data')
    os.makedirs(nltk_data_dir, exist_ok=True)

    # Add to NLTK's data path
    if nltk_data_dir not in nltk.data.path:
        nltk.data.path.insert(0, nltk_data_dir)

    print(f"Downloading NLTK data to: {nltk_data_dir}")

    # List of required packages
    packages = [
        'punkt',
        'punkt_tab',
        'averaged_perceptron_tagger',
        'averaged_perceptron_tagger_eng',
    ]

    success = True
    for package in packages:
        try:
            print(f"Downloading {package}...", end=' ')
            nltk.download(package, download_dir=nltk_data_dir, quiet=True)
            print("✓")
        except Exception as e:
            print(f"✗ Failed: {e}")
            success = False

    if success:
        print("\n✓ All NLTK packages downloaded successfully")
        return 0
    else:
        print("\n✗ Some packages failed to download")
        return 1

if __name__ == "__main__":
    sys.exit(download_nltk_data())
