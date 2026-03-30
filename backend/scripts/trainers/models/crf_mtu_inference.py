"""
CRF-based MTU Segmentation Inference
Use the trained CRF model to segment Thai text into MTUs
"""

import pickle
from typing import List, Dict
import os
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from nlp_utils.features.mtu_features import format_mtus, segment_text_to_mtus, load_model
from nlp_utils.features.char_utils import get_char_type
# Example usage
if __name__ == "__main__":
    # MODEL_PATH = r"D:\project\word_wrapping\script\data\text_dataset\train_silver\mtu_crf_model.pkl"
   
    # Get the directory where this script is located
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Build path relative to script location
    # Go up one level from scripts/models to backend/, then into models/
    MODEL_PATH = os.path.join(SCRIPT_DIR, "..", "..", "models", "mtu_crf_model.pkl")

    # Or normalize the path
    MODEL_PATH = os.path.normpath(MODEL_PATH)

    # Load model
    print("Loading CRF model...")
    crf = load_model(MODEL_PATH)
    print("Model loaded successfully!")
    