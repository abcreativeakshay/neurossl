import os
import glob
import urllib.request
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image, ImageDraw
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
import joblib

# 1. Initialize feature extractor
print("Initializing MobileNetV3...")
mobilenet = models.mobilenet_v3_small(pretrained=True)
feature_extractor = mobilenet.features
feature_extractor.eval()

preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def extract_features(img):
    tensor = preprocess(img).unsqueeze(0)
    with torch.no_grad():
        feats = feature_extractor(tensor)
        feats = torch.nn.functional.adaptive_avg_pool2d(feats, 1)
        feats = feats.flatten().numpy()
    return feats

# 2. Collect Positive Samples (MRI Scans)
print("Collecting positive MRI samples...")
oasis_files = glob.glob("Data/raw/neuro_ssl_outputs/data/raw/oasis_2d/**/*.jpg", recursive=True)
np.random.seed(42)
selected_oasis = np.random.choice(oasis_files, 150, replace=False)

X = []
y = []

for f in selected_oasis:
    try:
        img = Image.open(f).convert('RGB')
        X.append(extract_features(img))
        y.append(1)  # 1 for MRI
    except Exception as e:
        print(f"Error loading {f}: {e}")

# 3. Collect Negative Samples (Non-MRI)
print("Collecting negative samples...")

# Add local charts and figures
local_non_mris = glob.glob("**/*.png", recursive=True) + glob.glob("**/*.jpeg", recursive=True)
local_non_mris = [f for f in local_non_mris if "oasis_2d" not in f and ".venv" not in f and "node_modules" not in f]

for f in local_non_mris:
    try:
        img = Image.open(f).convert('RGB')
        X.append(extract_features(img))
        y.append(0)  # 0 for non-MRI
    except Exception as e:
        pass

# Generate synthetic negative samples (noise, text, shapes)
print("Generating synthetic negative samples...")
for i in range(50):
    # Random solid colors and gradients
    img = Image.new('RGB', (224, 224), color=(np.random.randint(0, 256), np.random.randint(0, 256), np.random.randint(0, 256)))
    X.append(extract_features(img))
    y.append(0)
    
    # Random shapes (circles, rectangles)
    img = Image.new('RGB', (224, 224), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    for _ in range(5):
        x1, y1 = np.random.randint(0, 100), np.random.randint(0, 100)
        x2, y2 = np.random.randint(120, 224), np.random.randint(120, 224)
        draw.rectangle([x1, y1, x2, y2], fill=(np.random.randint(0, 256), np.random.randint(0, 256), np.random.randint(0, 256)))
    X.append(extract_features(img))
    y.append(0)

# Download random natural images from Picsum
print("Downloading natural images for negative class...")
for i in range(80):
    try:
        # Picsum has random images
        url = f"https://picsum.photos/224?sig={i}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            img_data = response.read()
        img = Image.open(urllib.request.io.BytesIO(img_data)).convert('RGB')
        X.append(extract_features(img))
        y.append(0)
    except Exception as e:
        print(f"Failed to download image {i}: {e}")

X = np.array(X)
y = np.array(y)

print(f"Dataset shape: X={X.shape}, y={y.shape}")
print(f"Positive samples (MRI): {np.sum(y == 1)}")
print(f"Negative samples (Non-MRI): {np.sum(y == 0)}")

# 4. Train and evaluate classifier
clf = LogisticRegression(max_iter=1000)
scores = cross_val_score(clf, X, y, cv=5)
print(f"5-fold Cross-Validation Accuracy: {scores.mean()*100:.2f}% (+/- {scores.std()*2*100:.2f}%)")

# Train final classifier
clf.fit(X, y)

# Save the trained classifier
os.makedirs("backend/models", exist_ok=True)
clf_path = "backend/models/mri_classifier.pkl"
joblib.dump(clf, clf_path)
print(f"Saved classifier to {clf_path}")

# Test on specific files
print("Testing classifier on sample files:")
for f in ["1750576974109.png", "images (1).jpeg"] + selected_oasis[:3].tolist():
    if os.path.exists(f):
        img = Image.open(f).convert('RGB')
        feat = extract_features(img).reshape(1, -1)
        prob = clf.predict_proba(feat)[0, 1]
        pred = clf.predict(feat)[0]
        print(f"  {os.path.basename(f)} -> Prediction: {'MRI' if pred == 1 else 'NON-MRI'} (MRI Prob: {prob:.4f})")
