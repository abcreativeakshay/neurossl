import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import os
import glob
import json
import urllib.request

# Download ImageNet class labels if not present
labels_url = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
labels_path = "scratch/imagenet_classes.txt"
if not os.path.exists(labels_path):
    os.makedirs("scratch", exist_ok=True)
    urllib.request.urlretrieve(labels_url, labels_path)

with open(labels_path, "r") as f:
    categories = [s.strip() for s in f.readlines()]

# Load a lightweight pretrained model
model = models.mobilenet_v3_small(pretrained=True)
model.eval()

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def predict_imagenet(path):
    try:
        img = Image.open(path).convert('RGB')
        input_tensor = preprocess(img)
        input_batch = input_tensor.unsqueeze(0)
        
        with torch.no_grad():
            output = model(input_batch)
        
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top5_prob, top5_catid = torch.topk(probabilities, 5)
        
        print(f"Path: {os.path.basename(path)}")
        for i in range(top5_prob.size(0)):
            print(f"  {categories[top5_catid[i]]}: {top5_prob[i].item()*100:.2f}%")
        print("-" * 40)
    except Exception as e:
        print(f"Error for {path}: {e}")

print("--- OASIS IMAGES ---")
oasis_files = glob.glob("Data/raw/neuro_ssl_outputs/data/raw/oasis_2d/**/*.jpg", recursive=True)[:3]
for f in oasis_files:
    predict_imagenet(f)

print("--- OTHER IMAGES ---")
other_files = ["1750576974109.png", "images (1).jpeg"]
for f in other_files:
    if os.path.exists(f):
        predict_imagenet(f)
