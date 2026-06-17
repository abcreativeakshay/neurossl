import sys
import os
import torch

# Add backend directory to path
sys.path.append(os.path.abspath("backend"))

from model import get_model, preprocess_image, predict_with_uncertainty

WORKSPACE_DIR = "/Users/akshaybiradar/Downloads/neuro_ssl"
CHECKPOINT_PATH = os.path.join(WORKSPACE_DIR, "Data/raw/neuro_ssl_outputs/outputs/checkpoints/finetune/fold_0/checkpoint_best.pt")
DEVICE = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')

model = get_model(CHECKPOINT_PATH, DEVICE)

def test_image(path):
    print(f"Testing {os.path.basename(path)}:")
    try:
        with open(path, 'rb') as f:
            image_bytes = f.read()
        tensor, _ = preprocess_image(image_bytes)
        result = predict_with_uncertainty(model, tensor, DEVICE, temperature=1.6995, mc_samples=10)
        print(f"  Raw Prob: {result['raw_probability']:.4f}")
        print(f"  Calibrated Prob: {result['calibrated_probability']:.4f}")
        print(f"  Uncertainty (MC Std): {result['uncertainty']:.4f}")
    except Exception as e:
        print(f"  Error: {e}")
    print("-" * 40)

import glob
print("--- OASIS IMAGES ---")
oasis_files = glob.glob("Data/raw/neuro_ssl_outputs/data/raw/oasis_2d/**/*.jpg", recursive=True)[:3]
for f in oasis_files:
    test_image(f)

print("--- OTHER IMAGES ---")
other_files = ["1750576974109.png", "images (1).jpeg"]
for f in other_files:
    if os.path.exists(f):
        test_image(f)
