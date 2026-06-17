import os
import glob
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np

# Load pretrained model and strip classification head to get features
mobilenet = models.mobilenet_v3_small(pretrained=True)
# We want features before the classifier
feature_extractor = mobilenet.features
feature_extractor.eval()

preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def extract_features(path):
    img = Image.open(path).convert('RGB')
    tensor = preprocess(img).unsqueeze(0)
    with torch.no_grad():
        # Pass through backbone
        feats = feature_extractor(tensor)
        # Global average pool to get a 1D vector
        feats = torch.nn.functional.adaptive_avg_pool2d(feats, 1)
        feats = feats.flatten().numpy()
    norm = np.linalg.norm(feats)
    if norm > 0:
        feats /= norm
    return feats

# Load 15 reference OASIS images
oasis_files = glob.glob("Data/raw/neuro_ssl_outputs/data/raw/oasis_2d/**/*.jpg", recursive=True)
reference_files = oasis_files[:20]

print("Extracting reference features...")
references = [extract_features(f) for f in reference_files]

def test_feature_similarity(path):
    try:
        feats = extract_features(path)
        similarities = [np.dot(feats, ref) for ref in references]
        max_sim = max(similarities)
        mean_sim = np.mean(similarities)
        print(f"Path: {os.path.basename(path)}")
        print(f"  Max Feature Sim: {max_sim:.4f}")
        print(f"  Mean Feature Sim: {mean_sim:.4f}")
        print("-" * 40)
    except Exception as e:
        print(f"Error {path}: {e}")

print("--- OASIS IMAGES (NOT USED AS REFERENCE) ---")
for f in oasis_files[20:25]:
    test_feature_similarity(f)

print("--- OTHER IMAGES ---")
other_files = ["1750576974109.png", "images (1).jpeg"]
for f in other_files:
    if os.path.exists(f):
        test_feature_similarity(f)
