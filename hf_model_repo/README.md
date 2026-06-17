---
license: mit
tags:
  - pytorch
  - vision-transformer
  - medical-imaging
  - brain-mri
  - dementia-classification
  - self-supervised-learning
  - neuroscience
datasets:
  - OASIS
  - IXI
language:
  - en
pipeline_tag: image-classification
library_name: pytorch
---

# 🧠 NeuroSSL — Self-Supervised Vision Transformer for MRI-Based Dementia Classification

A **Multi-Scale Vision Transformer (ViT)** with **Second-Order Covariance Pooling**, pre-trained via self-supervised learning on brain MRI datasets (OASIS & IXI) and fine-tuned for binary dementia classification.

## Model Description

NeuroSSL is a deep learning model designed for **clinical-grade brain MRI analysis**. It classifies 2D MRI slices as showing dementia-related changes or not, with calibrated probabilities and uncertainty quantification.

### Architecture

| Component | Details |
|---|---|
| **Encoder** | MultiScaleViT2D — 384-dim, 12 transformer blocks, 6 attention heads |
| **Patch Embedding** | 2D Conv projection, patch size 16×16, input 224×224 grayscale |
| **Multi-Scale Fusion** | Intermediate features from layers [2, 5, 8, 11] fused via linear projection |
| **Classifier** | Second-Order Covariance Pooling + MLP head |
| **Calibration** | Platt Temperature Scaling (T = 1.6995) |
| **Uncertainty** | Monte Carlo Dropout (10 forward passes) |
| **Parameters** | ~25M |

### Key Features

- **Self-supervised pre-training** on unlabeled brain MRI data (OASIS + IXI)
- **Multi-scale feature extraction** from 4 intermediate transformer layers
- **Second-order statistics** via covariance pooling for richer representations
- **Attention rollout** visualization for interpretable predictions
- **Calibrated probabilities** with Platt scaling
- **Uncertainty estimation** via MC Dropout

## Training

### Pre-training
- **Method**: Self-supervised (masked image modeling)
- **Data**: OASIS + IXI brain MRI datasets (unlabeled 2D slices)
- **Epochs**: 20
- **Input**: 224×224 grayscale MRI slices, Z-score normalized

### Fine-tuning
- **Task**: Binary classification (Dementia vs Non-Demented)
- **Data**: OASIS labeled dataset
- **Strategy**: 5-fold cross-validation
- **Epochs**: 20 per fold
- **Calibration**: Post-hoc Platt temperature scaling

## Usage

### Loading the Model

```python
import torch
from model import MultiScaleViT2DEncoder, SecondOrderClassifier

# Build architecture
encoder = MultiScaleViT2DEncoder(
    img_size=(224, 224),
    patch_size=(16, 16),
    embed_dim=384,
    depth=12,
    num_heads=6,
    drop_path_rate=0.0
)
model = SecondOrderClassifier(encoder, num_classes=2, dropout=0.3, use_second_order=True)

# Load weights
ckpt = torch.load("checkpoint_best.pt", map_location="cpu", weights_only=False)
model.load_state_dict(ckpt["model_state"])
model.eval()
```

### Running Inference

```python
from PIL import Image
import numpy as np

# Preprocess
img = Image.open("brain_mri.jpg").convert("L").resize((224, 224))
tensor = torch.from_numpy(np.array(img, dtype=np.float32)).unsqueeze(0) / 255.0
mu, std = tensor.mean(), tensor.std() + 1e-8
tensor = ((tensor - mu) / std).unsqueeze(0)  # Shape: (1, 1, 224, 224)

# Predict
with torch.no_grad():
    logits = model(tensor)
    probs = torch.softmax(logits / 1.6995, dim=1)  # Platt-calibrated
    print(f"Dementia probability: {probs[0, 1]:.4f}")
```

### Downloading from Hugging Face Hub

```python
from huggingface_hub import hf_hub_download

checkpoint_path = hf_hub_download(
    repo_id="ABCREATIVEAKSHAY/neuro-ssl-dementia-classifier",
    filename="checkpoint_best.pt"
)
ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
```

## Checkpoint Contents

The `checkpoint_best.pt` file contains:

```python
{
    "model_state": OrderedDict,  # Model weights (state_dict)
    # May also contain optimizer state, epoch info, metrics, etc.
}
```

## Intended Use

- **Primary use**: Research and clinical decision support for brain MRI analysis
- **Input**: 2D grayscale brain MRI slices (axial/sagittal/coronal)
- **Output**: Binary classification with calibrated probability and uncertainty

## Limitations & Ethical Considerations

> ⚠️ **This model is intended for research purposes and clinical decision support only.**
> It should NOT be used as a standalone diagnostic tool. All predictions should be reviewed by qualified medical professionals.

- Trained on OASIS dataset which may not generalize to all populations
- Performance may vary across different MRI scanners and protocols
- 2D slice-level analysis does not capture full 3D volumetric information

## Citation

If you use this model, please cite:

```bibtex
@misc{neurossl2025,
  title={NeuroSSL: Self-Supervised Vision Transformer for MRI-Based Dementia Classification},
  author={Akshay Biradar},
  year={2025},
  url={https://huggingface.co/ABCREATIVEAKSHAY/neuro-ssl-dementia-classifier}
}
```
