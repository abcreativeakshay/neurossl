import os
import glob
from PIL import Image
import numpy as np

def analyze_image(path):
    try:
        img = Image.open(path)
        img_np = np.array(img)
        
        # Color check
        if len(img_np.shape) < 3:
            is_grayscale = True
            channel_diff = 0
        else:
            # Check average difference between channels
            ch_diff = np.mean(np.abs(img_np[:, :, 0].astype(float) - img_np[:, :, 1].astype(float))) + \
                      np.mean(np.abs(img_np[:, :, 1].astype(float) - img_np[:, :, 2].astype(float)))
            is_grayscale = ch_diff < 5.0
            channel_diff = ch_diff
            
        # Convert to grayscale for further checks
        gray = img.convert('L')
        gray_np = np.array(gray)
        h, w = gray_np.shape
        
        # Border check (average intensity of the 5% border)
        border_h = max(1, int(h * 0.05))
        border_w = max(1, int(w * 0.05))
        
        top_border = gray_np[:border_h, :]
        bottom_border = gray_np[-border_h:, :]
        left_border = gray_np[:, :border_w]
        right_border = gray_np[:, -border_w:]
        
        border_mean = (np.mean(top_border) + np.mean(bottom_border) + np.mean(left_border) + np.mean(right_border)) / 4.0
        
        # Center check (average intensity of the middle 50%)
        center_h_start, center_h_end = int(h * 0.25), int(h * 0.75)
        center_w_start, center_w_end = int(w * 0.25), int(w * 0.75)
        center_region = gray_np[center_h_start:center_h_end, center_w_start:center_w_end]
        center_mean = np.mean(center_region)
        center_std = np.std(center_region)
        
        print(f"Path: {os.path.basename(path)}")
        print(f"  Shape: {img_np.shape}")
        print(f"  Is Grayscale: {is_grayscale} (diff: {channel_diff:.2f})")
        print(f"  Border Mean: {border_mean:.2f}")
        print(f"  Center Mean: {center_mean:.2f}")
        print(f"  Center Std: {center_std:.2f}")
        print("-" * 40)
    except Exception as e:
        print(f"Error reading {path}: {e}")

print("--- OASIS IMAGES ---")
oasis_files = glob.glob("Data/raw/neuro_ssl_outputs/data/raw/oasis_2d/**/*.jpg", recursive=True)[:5]
for f in oasis_files:
    analyze_image(f)

print("--- OTHER IMAGES ---")
other_files = ["1750576974109.png", "images (1).jpeg"]
for f in other_files:
    if os.path.exists(f):
        analyze_image(f)
