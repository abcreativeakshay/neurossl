---
title: NeuroSSL Dementia Classifier
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: true
license: mit
short_description: Self-Supervised ViT for MRI-based Dementia Classification
---

# NeuroSSL — Dementia Classifier

A deep learning clinical diagnostics app built with a **Self-Supervised Vision Transformer (ViT)** trained on OASIS & IXI brain MRI datasets.

## Features
- **Real-time Inference** on brain MRI slices with attention rollout visualization
- **Platt-calibrated probabilities** with MC Dropout uncertainty quantification
- **Interactive MRI Viewer** with pan, zoom, and multiple scientific colormaps
- **Diagnostic Report Generator** with PDF/print export
- **Model Analytics Dashboard** with cross-validation metrics and training curves

## Architecture
- **Encoder:** MultiScaleViT2D (384-dim, 12 blocks, 6 heads)
- **Classifier:** Second-Order Covariance Pooling
- **Calibration:** Platt Temperature Scaling (T = 1.6995)
- **Uncertainty:** Monte Carlo Dropout
