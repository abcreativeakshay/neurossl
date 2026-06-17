# NeuroSSL 🧠

A complete end-to-end deep learning pipeline for dementia screening using Self-Supervised Learning (SSL) on brain MRI scans.

NeuroSSL leverages state-of-the-art Vision Transformers (ViT) to classify MRI scans, provide uncertainty estimation, and generate attention heatmaps for explainable AI in medical imaging.

## 🚀 Features

- **Self-Supervised Pretraining**: Utilizes Masked Autoencoders (MAE) and DINO on over 100,000 unlabelled MRI slices to learn fundamental brain anatomy.
- **Vision Transformer (ViT) Encoder**: 82 million parameter multi-scale ViT architecture customized for 2D medical imaging.
- **Uncertainty Estimation**: Monte Carlo (MC) Dropout provides a measure of confidence and uncertainty for every prediction.
- **Explainable AI**: Attention Rollout generates heatmaps highlighting the exact regions of the brain the model is focusing on.
- **Full-Stack Application**: A premium React frontend paired with a Flask API, deployed on Hugging Face Spaces and served globally via Cloudflare edge workers.

## 📊 Datasets

The model was trained on high-quality medical imaging datasets:
- **OASIS Dataset**: The primary labeled dataset containing MRI scans categorized by clinical dementia rating. Grouped for binary classification (Dementia-related vs. Non-Demented).
- **IXI Dataset**: A supplementary dataset of healthy brain MRI scans used to increase the volume of data for self-supervised pretraining.

## 🧠 Model Architecture

- **Encoder (MultiScaleViT2DEncoder)**: Custom Vision Transformer with `img_size=(224, 224)`, `patch_size=(16, 16)`, `embed_dim=384`, `depth=12`, `num_heads=6`.
- **Classifier (SecondOrderClassifier)**: Calculates covariance across patches to capture complex spatial relationships, moving beyond the standard `[CLS]` token approach.
- **Calibration**: Empirically calibrated decision threshold (`0.70`) and optimal temperature coefficient (`1.6995`) to smooth softmax outputs.

## ⚙️ Project Structure

- `backend/`: Flask API wrapping the PyTorch model for inference, uncertainty calculation, and attention mapping.
- `frontend/`: Modern, dark-themed React UI (Vite) with drag-and-drop file uploads and interactive sliders.
- `cloudflare_worker/`: Edge network deployment proxy for fast, global serving.
- `hf_space/` & `deploy/`: Dockerized Hugging Face Spaces configuration.
- `Data/`: Datasets and raw outputs (ignored in git to save space).

## 📈 Performance

Evaluated against a held-out test set:
- **AUC-ROC**: 0.893 (High discriminative power)
- **Sensitivity**: 97.8% (Excellent at catching almost all dementia cases)
- **Specificity**: 57.6%

## 💻 Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/abcreativeakshay/neurossl.git
   cd neurossl
   ```
2. **Install dependencies**:
   *(Requires Python 3.8+)*
   ```bash
   pip install -r deploy/requirements.txt
   ```
3. **Run the Backend/Frontend API**:
   ```bash
   cd hf_space
   python app.py
   ```
   *Note: Ensure you have the model checkpoints downloaded to run inference locally.*

---
*Disclaimer: This project is for educational and research purposes only and is not intended for clinical diagnosis.*
