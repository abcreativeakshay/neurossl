# NeuroSSL - Complete End-to-End Project Pipeline

This document outlines the entire lifecycle of the NeuroSSL project, from initial dataset selection through model training, and all the way to full-stack web deployment. It includes specific architectural and training hyperparameters.

---

## 1. Dataset Selection
The foundation of the project relied on high-quality medical imaging datasets to teach the model both general brain anatomy and specific dementia markers.
*   **OASIS Dataset**: The primary labeled dataset containing MRI scans categorized by clinical dementia rating. The dataset consists of 4 distinct classes: **Mild Dementia**, **Very Mild Dementia**, **Moderate Demented**, and **Non Demented**. For this specific screening model, these were grouped to train a binary classifier (Dementia-related changes vs. Non-Demented).
*   **IXI Dataset**: A supplementary dataset of healthy brain MRI scans used purely to increase the volume of data for the self-supervised pretraining phase.

## 2. Preprocessing
Before any training could occur, the raw 3D MRI scans had to be standardized.
*   **Slicing & Conversion**: The 3D MRI volumes were sliced into 2D images. 
*   **Caching**: To optimize training speed, over 100,000 slices were converted into PyTorch tensors and cached locally as `.pt` files.
*   **Normalization Hyperparameters**: During inference, images are automatically converted to grayscale, resized to `224x224` using bilinear interpolation, and Z-score normalized (zero mean, unit variance) to stabilize the attention mechanism.

## 3. Model Building
The architecture was built from the ground up to handle the complexities of medical imaging, focusing on accuracy, uncertainty estimation, and explainability.
*   **Encoder (MultiScaleViT2DEncoder)**: A Vision Transformer containing approximately 82 million parameters.
    *   *Hyperparameters*: `img_size=(224, 224)`, `patch_size=(16, 16)`, `embed_dim=384`, `depth=12`, `num_heads=6`, `mlp_ratio=4.0`, `drop_path_rate=0.1` (during training).
*   **Classifier (SecondOrderClassifier)**: A custom head that calculates the covariance across patches to capture complex spatial relationships, rather than just using the standard `[CLS]` token.
    *   *Hyperparameters*: `dropout=0.3`, `num_classes=2`, `use_second_order=True`.
*   **Special Features**: 
    *   **MC Dropout**: Injected into the classifier (rate `0.3`) to run multiple forward passes, allowing the model to calculate its own "uncertainty" (Standard Deviation) on a prediction. Default samples set to `mc_samples=10`.
    *   **Attention Rollout**: Extracts the self-attention weights from the ViT layers to generate visual heatmaps showing exactly which parts of the brain the model is looking at.

## 4. Model Training
Training was split into two distinct phases to maximize performance, even with limited labeled data.
*   **Phase 1 - Self-Supervised Pretraining (MAE + DINO)**: The model was trained on a combined, unlabelled pool of **108,232 slices** (from both OASIS and IXI). It learned the fundamental anatomy and structure of the human brain without knowing anything about dementia. 
*   **Phase 2 - Supervised Fine-Tuning**: The pretrained encoder was then attached to the classification head and fine-tuned on a smaller subset of **18,151 labeled OASIS samples** (approx. 30%). Using Cross-Entropy loss, it learned to map the structural features it already knew to specific dementia diagnoses.

## 5. Model Evaluation & Calibration
The fine-tuned model was evaluated against a held-out test set (`final_report.json`), and its decision boundaries were manually calibrated using temperature scaling and custom thresholding.
*   **Raw Metrics**: 
    *   **AUC-ROC**: 0.893 (High discriminative power)
    *   **Sensitivity**: 97.8% (Excellent at catching almost all dementia cases)
    *   **Specificity**: 57.6% (Struggles to confidently rule out dementia, resulting in false positives)
*   **Temperature Calibration**: Post-training Platt scaling resulted in an optimal temperature coefficient of `temperature=1.6995` to smooth overconfident softmax outputs.
*   **Threshold Tuning**: During testing, we discovered the model's output probabilities were tightly clustered between `0.60` and `0.80`. A standard decision threshold of `0.50` flagged everything as dementia. We empirically calibrated the optimal decision threshold to **`threshold=0.70`**, perfectly splitting the model's natural output distribution between healthy and demented scans.

## 6. Hugging Face Deployment
To make the PyTorch model accessible, we deployed it as a cloud API.
*   **Flask API (`app.py`)**: We wrapped the PyTorch inference code inside a Python Flask server. This API accepts image uploads, runs the ViT inference, calculates uncertainty, and returns the probabilities and attention maps.
*   **Hugging Face Spaces**: The Flask API, along with the 82M parameter checkpoint, was packaged into a Docker container and deployed to a Hugging Face Space. This provides free, scalable GPU/CPU hosting for the backend engine.

## 7. App Building (Frontend & Edge)
To allow end-users and doctors to interact with the model, a premium full-stack web application was built around the API.
*   **React Frontend (Vite)**: A modern, dark-themed UI was built using React. It features drag-and-drop file uploads, interactive parameter sliders (to adjust the `0.70` threshold and `10` MC Samples), and dynamic visual rendering of the Attention Heatmaps over the MRI scans.
*   **Static Serving**: The React app was compiled into static HTML/JS/CSS assets and injected into the Hugging Face Flask server, allowing the backend to serve the frontend UI simultaneously.
*   **Cloudflare Edge Worker**: Finally, a Cloudflare Worker (`neuro-ssl-worker`) was deployed to the global edge network. This worker acts as a proxy/iframe wrapper, embedding the Hugging Face Space on a custom, fast domain while providing premium loading animations and SEO metadata.
