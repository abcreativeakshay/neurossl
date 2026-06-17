import sys
import os
import torch
import numpy as np

# Add backend directory to path
sys.path.append(os.path.abspath("backend"))

from model import get_model, preprocess_image

WORKSPACE_DIR = "/Users/akshaybiradar/Downloads/neuro_ssl"
CHECKPOINT_PATH = os.path.join(WORKSPACE_DIR, "Data/raw/neuro_ssl_outputs/outputs/checkpoints/finetune/fold_0/checkpoint_best.pt")
DEVICE = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')

model = get_model(CHECKPOINT_PATH, DEVICE)

def extract_custom_features(path):
    with open(path, 'rb') as f:
        image_bytes = f.read()
    tensor, _ = preprocess_image(image_bytes)
    tensor = tensor.to(DEVICE)
    with torch.no_grad():
        logits, features, cls = model(tensor, return_features=True)
        feat_vec = features.squeeze(0).cpu().numpy()
        cls_vec = cls.squeeze(0).cpu().numpy()
    
    # Normalize
    feat_norm = np.linalg.norm(feat_vec)
    if feat_norm > 0:
        feat_vec /= feat_norm
        
    cls_norm = np.linalg.norm(cls_vec)
    if cls_norm > 0:
        cls_vec /= cls_norm
        
    return feat_vec, cls_vec

import glob
oasis_files = glob.glob("Data/raw/neuro_ssl_outputs/data/raw/oasis_2d/**/*.jpg", recursive=True)
reference_files = oasis_files[:20]

print("Extracting custom references...")
references = [extract_custom_features(f) for f in reference_files]
ref_feats = [r[0] for r in references]
ref_clss = [r[1] for r in references]

def test_custom_similarity(path):
    try:
        feat, cls = extract_custom_features(path)
        
        sim_feat = [np.dot(feat, ref) for ref in ref_feats]
        sim_cls = [np.dot(cls, ref) for ref in ref_clss]
        
        print(f"Path: {os.path.basename(path)}")
        print(f"  Max Feature Sim: {max(sim_feat):.4f} (mean: {np.mean(sim_feat):.4f})")
        print(f"  Max CLS Sim: {max(sim_cls):.4f} (mean: {np.mean(sim_cls):.4f})")
        print("-" * 40)
    except Exception as e:
        print(f"Error {path}: {e}")

print("--- OASIS IMAGES (NOT USED AS REFERENCE) ---")
for f in oasis_files[20:25]:
    test_custom_similarity(f)

print("--- OTHER IMAGES ---")
other_files = ["1750576974109.png", "images (1).jpeg"]
for f in other_files:
    if os.path.exists(f):
        test_custom_similarity(f)
