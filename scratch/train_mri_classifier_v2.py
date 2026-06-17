"""
Retrain MRI classifier with:
  - Many more OASIS samples (500+)
  - Data augmentation: random crops (to simulate single-view MRIs), flips, contrast
  - Grayscale MRI-like augmentations
  - More diverse negative set
"""
import os
import glob
import urllib.request
import io
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
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

X = []
y = []

# ─────────────────────────────────────────────────────────────────────────────
# 2. Collect Positive Samples — Brain MRI scans (OASIS dataset)
# ─────────────────────────────────────────────────────────────────────────────
print("Collecting positive MRI samples...")
oasis_files = glob.glob("Data/raw/neuro_ssl_outputs/data/raw/oasis_2d/**/*.jpg", recursive=True)
np.random.seed(42)
selected_oasis = np.random.choice(oasis_files, min(500, len(oasis_files)), replace=False)

for f in selected_oasis:
    try:
        img = Image.open(f).convert('RGB')
        # Original full image
        X.append(extract_features(img))
        y.append(1)
        
        # Also extract LEFT HALF crop (simulates single-view brain MRI)
        w, h = img.size
        left_crop = img.crop((0, 0, w // 2, h))
        X.append(extract_features(left_crop))
        y.append(1)
        
        # Also extract RIGHT HALF crop
        right_crop = img.crop((w // 2, 0, w, h))
        X.append(extract_features(right_crop))
        y.append(1)
        
    except Exception as e:
        print(f"Error loading {f}: {e}")

# Augmented MRI samples — vary contrast, brightness, blur
print("Generating augmented MRI samples...")
aug_oasis = np.random.choice(oasis_files, min(200, len(oasis_files)), replace=False)
for f in aug_oasis:
    try:
        img = Image.open(f).convert('RGB')
        w, h = img.size
        
        # Grayscale version (many user-uploaded MRIs are pure grayscale)
        gray_img = ImageOps.grayscale(img).convert('RGB')
        X.append(extract_features(gray_img))
        y.append(1)
        
        # Single-view grayscale crop
        left_gray = ImageOps.grayscale(img.crop((0, 0, w // 2, h))).convert('RGB')
        X.append(extract_features(left_gray))
        y.append(1)
        
        # Contrast-adjusted version
        enhancer = ImageEnhance.Contrast(img)
        X.append(extract_features(enhancer.enhance(1.5)))
        y.append(1)
        
        # Brightness-adjusted version
        enhancer = ImageEnhance.Brightness(img)
        X.append(extract_features(enhancer.enhance(0.7)))
        y.append(1)
        
        # Slightly blurred (simulates lower quality upload)
        blurred = img.filter(ImageFilter.GaussianBlur(radius=2))
        X.append(extract_features(blurred))
        y.append(1)
        
        # Horizontally flipped
        flipped = ImageOps.mirror(img)
        X.append(extract_features(flipped))
        y.append(1)

        # Square center crop (simulates what many MRI viewers show)
        min_dim = min(w, h)
        left_edge = (w - min_dim) // 2
        top_edge = (h - min_dim) // 2
        center_sq = img.crop((left_edge, top_edge, left_edge + min_dim, top_edge + min_dim))
        X.append(extract_features(center_sq))
        y.append(1)
        
    except Exception as e:
        pass

print(f"Total MRI samples so far: {sum(y)}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Collect Negative Samples — Non-MRI images
# ─────────────────────────────────────────────────────────────────────────────
print("Collecting negative samples...")

# Add local charts and figures
local_non_mris = glob.glob("**/*.png", recursive=True) + glob.glob("**/*.jpeg", recursive=True)
local_non_mris = [f for f in local_non_mris if "oasis_2d" not in f and ".venv" not in f and "node_modules" not in f]

for f in local_non_mris:
    try:
        img = Image.open(f).convert('RGB')
        X.append(extract_features(img))
        y.append(0)
    except Exception as e:
        pass

# Generate synthetic negative samples
print("Generating synthetic negative samples...")
for i in range(80):
    # Solid colors
    img = Image.new('RGB', (224, 224), color=(np.random.randint(0, 256), np.random.randint(0, 256), np.random.randint(0, 256)))
    X.append(extract_features(img))
    y.append(0)
    
    # Random shapes
    img = Image.new('RGB', (224, 224), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    for _ in range(np.random.randint(3, 10)):
        x1, y1 = np.random.randint(0, 150), np.random.randint(0, 150)
        x2, y2 = np.random.randint(x1 + 20, 224), np.random.randint(y1 + 20, 224)
        draw.rectangle([x1, y1, x2, y2], fill=(np.random.randint(0, 256), np.random.randint(0, 256), np.random.randint(0, 256)))
    X.append(extract_features(img))
    y.append(0)
    
    # Random noise (grayscale) — to avoid confusing with MRI
    noise = np.random.randint(0, 256, (224, 224), dtype=np.uint8)
    img = Image.fromarray(noise, mode='L').convert('RGB')
    X.append(extract_features(img))
    y.append(0)

    # Gradient images
    gradient = np.tile(np.linspace(0, 255, 224, dtype=np.uint8), (224, 1))
    if i % 2 == 0:
        gradient = gradient.T  # vertical gradient
    img = Image.fromarray(gradient, mode='L').convert('RGB')
    X.append(extract_features(img))
    y.append(0)

# Download random natural images from Picsum
print("Downloading natural images for negative class...")
for i in range(120):
    try:
        url = f"https://picsum.photos/224?sig={i+1000}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            img_data = response.read()
        img = Image.open(io.BytesIO(img_data)).convert('RGB')
        X.append(extract_features(img))
        y.append(0)
    except Exception as e:
        pass

X = np.array(X)
y = np.array(y)

print(f"\nFinal Dataset shape: X={X.shape}, y={y.shape}")
print(f"Positive samples (MRI): {np.sum(y == 1)}")
print(f"Negative samples (Non-MRI): {np.sum(y == 0)}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Train and evaluate classifier
# ─────────────────────────────────────────────────────────────────────────────
print("\nTraining classifier...")
clf = LogisticRegression(max_iter=2000, C=0.5)
scores = cross_val_score(clf, X, y, cv=5)
print(f"5-fold Cross-Validation Accuracy: {scores.mean()*100:.2f}% (+/- {scores.std()*2*100:.2f}%)")

# Train final classifier on all data
clf.fit(X, y)

# Save to both locations
for path in ["backend/models/mri_classifier.pkl", "hf_space/models/mri_classifier.pkl"]:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(clf, path)
    print(f"Saved classifier to {path}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Test on specific files
# ─────────────────────────────────────────────────────────────────────────────
print("\n--- Testing on specific files ---")
test_files = ["1750576974109.png", "images (1).jpeg"] + list(selected_oasis[:3])

for f in test_files:
    if os.path.exists(f):
        img = Image.open(f).convert('RGB')
        feat = extract_features(img).reshape(1, -1)
        prob = clf.predict_proba(feat)[0, 1]
        pred = clf.predict(feat)[0]
        label = 'MRI' if pred == 1 else 'NON-MRI'
        print(f"  {os.path.basename(f)} -> {label} (MRI Prob: {prob:.4f})")

# Also test crops of OASIS images (simulating single-view uploads)
print("\n--- Testing single-view crops ---")
for f in list(selected_oasis[:3]):
    if os.path.exists(f):
        img = Image.open(f).convert('RGB')
        w, h = img.size
        
        # Left half
        left = img.crop((0, 0, w // 2, h))
        feat = extract_features(left).reshape(1, -1)
        prob = clf.predict_proba(feat)[0, 1]
        print(f"  {os.path.basename(f)} LEFT CROP -> MRI Prob: {prob:.4f}")
        
        # Grayscale
        gray = ImageOps.grayscale(img).convert('RGB')
        feat = extract_features(gray).reshape(1, -1)
        prob = clf.predict_proba(feat)[0, 1]
        print(f"  {os.path.basename(f)} GRAYSCALE -> MRI Prob: {prob:.4f}")
