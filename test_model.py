import torch
import numpy as np
from PIL import Image
import os
import sys
import glob

sys.path.append("/Users/akshaybiradar/Downloads/neuro_ssl/backend")
from model import get_model, preprocess_image, predict_with_uncertainty

checkpoint_path = "/Users/akshaybiradar/Downloads/neuro_ssl/Data/raw/neuro_ssl_outputs/outputs/checkpoints/finetune/fold_0/checkpoint_best.pt"
if not os.path.exists(checkpoint_path):
    print("Checkpoint not found!")
    sys.exit(1)

device = torch.device('cpu')
model = get_model(checkpoint_path, device)

base_dir = "/Users/akshaybiradar/Downloads/neuro_ssl/hf_space/data/demo_images"
mild = glob.glob(os.path.join(base_dir, "Mild Dementia", "*.jpg"))[:5]
non = glob.glob(os.path.join(base_dir, "Non Demented", "*.jpg"))[:5]

test_images = mild + non

for img_path in test_images:
    with open(img_path, 'rb') as f:
        image_bytes = f.read()
    
    tensor, _ = preprocess_image(image_bytes)
    res = predict_with_uncertainty(model, tensor, device, temperature=1.6995, mc_samples=0)
    print(f"File: {os.path.basename(os.path.dirname(img_path))}/{os.path.basename(img_path)}")
    print(f"  Raw Prob [1]: {res['raw_probability']:.4f}, Cal Prob [1]: {res['calibrated_probability']:.4f}")
