import os
import glob
from PIL import Image
import numpy as np

# Load 10 reference OASIS images and downsample them to 32x32
oasis_files = glob.glob("Data/raw/neuro_ssl_outputs/data/raw/oasis_2d/**/*.jpg", recursive=True)
reference_files = oasis_files[:20]

references = []
for f in reference_files:
    img = Image.open(f).convert('L').resize((32, 32), Image.BILINEAR)
    vec = np.array(img, dtype=float).flatten()
    # Normalize vector to unit length
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    references.append(vec)

def test_similarity(path):
    try:
        img = Image.open(path).convert('L').resize((32, 32), Image.BILINEAR)
        vec = np.array(img, dtype=float).flatten()
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        
        # Calculate cosine similarities to all references
        similarities = [np.dot(vec, ref) for ref in references]
        max_sim = max(similarities)
        mean_sim = np.mean(similarities)
        
        print(f"Path: {os.path.basename(path)}")
        print(f"  Max Similarity: {max_sim:.4f}")
        print(f"  Mean Similarity: {mean_sim:.4f}")
        print("-" * 40)
    except Exception as e:
        print(f"Error {path}: {e}")

print("--- OASIS IMAGES (NOT USED AS REFERENCE) ---")
for f in oasis_files[20:25]:
    test_similarity(f)

print("--- OTHER IMAGES ---")
other_files = ["1750576974109.png", "images (1).jpeg"]
for f in other_files:
    if os.path.exists(f):
        test_similarity(f)
