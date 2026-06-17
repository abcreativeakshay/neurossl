import os
import glob
from PIL import Image
import numpy as np

def evaluate_mri_heuristic(path):
    try:
        img = Image.open(path).convert('L')
        w, h = img.size
        img_np = np.array(img)
        
        # Divide into 3x3 grid
        h_third = h // 3
        w_third = w // 3
        
        # Calculate mean intensities of the 9 cells
        grid = {}
        for r in range(3):
            for c in range(3):
                cell = img_np[r*h_third:(r+1)*h_third, c*w_third:(c+1)*w_third]
                grid[(r, c)] = {
                    'mean': float(np.mean(cell)),
                    'std': float(np.std(cell))
                }
                
        # Corner cells: (0,0), (0,2), (2,0), (2,2)
        corner_means = [grid[(0,0)]['mean'], grid[(0,2)]['mean'], grid[(2,0)]['mean'], grid[(2,2)]['mean']]
        max_corner_mean = max(corner_means)
        
        # Center cell: (1,1)
        center_mean = grid[(1,1)]['mean']
        center_std = grid[(1,1)]['std']
        
        # Left/Right middle: (1,0), (1,2)
        # Top/Bottom middle: (0,1), (2,1)
        edge_means = [grid[(0,1)]['mean'], grid[(1,0)]['mean'], grid[(1,2)]['mean'], grid[(2,1)]['mean']]
        max_edge_mean = max(edge_means)
        
        # Let's print metrics
        print(f"Path: {os.path.basename(path)}")
        print(f"  Max Corner Mean: {max_corner_mean:.2f}")
        print(f"  Max Edge Mean: {max_edge_mean:.2f}")
        print(f"  Center Mean: {center_mean:.2f} (std: {center_std:.2f})")
        
        # Rule: Corners must be dark, center must have structure
        is_mri = (max_corner_mean < 15.0) and (center_mean > 25.0) and (center_std > 15.0)
        print(f"  Is Brain MRI: {is_mri}")
        print("-" * 40)
    except Exception as e:
        print(f"Error {path}: {e}")

print("--- OASIS IMAGES ---")
oasis_files = glob.glob("Data/raw/neuro_ssl_outputs/data/raw/oasis_2d/**/*.jpg", recursive=True)[:5]
for f in oasis_files:
    evaluate_mri_heuristic(f)

print("--- OTHER IMAGES ---")
other_files = ["1750576974109.png", "images (1).jpeg"]
for f in other_files:
    if os.path.exists(f):
        evaluate_mri_heuristic(f)
