"""
NeuroSSL Dementia Classifier — HF Spaces Backend
Serves both the Flask API and the built React frontend from one container.
Downloads the model checkpoint from Hugging Face Hub on first startup.
"""
import os
import io
import json
import base64
import torch
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from model import get_model, preprocess_image, predict_with_uncertainty

# ──────────────────────────────────────────────────────────────────────────────
# Configuration — all paths relative to the container working directory
# ──────────────────────────────────────────────────────────────────────────────
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
STATIC_DIR = os.path.join(APP_DIR, "static")

CHECKPOINT_DIR = os.path.join(APP_DIR, "checkpoints")
CHECKPOINT_PATH = os.path.join(CHECKPOINT_DIR, "checkpoint_best.pt")

FIGURES_DIR = os.path.join(DATA_DIR, "figures")
OASIS_DIR = os.path.join(DATA_DIR, "demo_images")
REPORT_PATH = os.path.join(DATA_DIR, "final_report.json")

# ──────────────────────────────────────────────────────────────────────────────
# HF Hub model download settings
# Set these as Space secrets or environment variables:
#   HF_MODEL_REPO  = "your-username/neuro-ssl-model"
#   HF_MODEL_FILE  = "checkpoint_best.pt"
# ──────────────────────────────────────────────────────────────────────────────
HF_MODEL_REPO = os.environ.get("HF_MODEL_REPO", "ABCREATIVEAKSHAY/neuro-ssl-dementia-classifier")
HF_MODEL_FILE = os.environ.get("HF_MODEL_FILE", "checkpoint_best.pt")

# ──────────────────────────────────────────────────────────────────────────────
# Flask App
# ──────────────────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=STATIC_DIR)
CORS(app)

# Device — HF Spaces free tier has CPU only; paid tiers can have GPU
if torch.cuda.is_available():
    DEVICE = torch.device('cuda')
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    DEVICE = torch.device('mps')
else:
    DEVICE = torch.device('cpu')
print(f"Using device: {DEVICE}")

# Global model cache
MODEL = None


def download_checkpoint():
    """Download checkpoint from HF Hub if not already present locally."""
    if os.path.exists(CHECKPOINT_PATH):
        print(f"Checkpoint already exists at {CHECKPOINT_PATH}")
        return

    if not HF_MODEL_REPO:
        print("WARNING: HF_MODEL_REPO not set and no local checkpoint found.")
        print("Set the HF_MODEL_REPO environment variable to your model repo ID.")
        return

    print(f"Downloading checkpoint from {HF_MODEL_REPO}/{HF_MODEL_FILE}...")
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    from huggingface_hub import hf_hub_download
    downloaded_path = hf_hub_download(
        repo_id=HF_MODEL_REPO,
        filename=HF_MODEL_FILE,
        local_dir=CHECKPOINT_DIR,
        local_dir_use_symlinks=False
    )
    print(f"Checkpoint downloaded to: {downloaded_path}")


def load_cached_model():
    global MODEL
    if MODEL is None:
        download_checkpoint()
        if not os.path.exists(CHECKPOINT_PATH):
            raise FileNotFoundError(
                f"Checkpoint not found at: {CHECKPOINT_PATH}. "
                "Please set HF_MODEL_REPO env var or upload checkpoint manually."
            )
        MODEL = get_model(CHECKPOINT_PATH, DEVICE)
    return MODEL


# ──────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@app.route('/api/predict', methods=['POST'])
def predict_endpoint():
    try:
        model = load_cached_model()
    except Exception as e:
        return jsonify({'error': f"Failed to load PyTorch model checkpoint: {str(e)}"}), 500

    temperature = float(request.form.get('temperature', 1.6995))
    mc_samples = int(request.form.get('mc_samples', 10))
    threshold = float(request.form.get('threshold', 0.62))

    try:
        image_bytes = None
        if 'file' in request.files:
            file = request.files['file']
            image_bytes = file.read()
        elif request.form.get('image_path'):
            image_path = request.form.get('image_path')
            if not os.path.isabs(image_path):
                image_path = os.path.join(OASIS_DIR, image_path)
            if not os.path.exists(image_path):
                return jsonify({'error': f"Image path not found: {image_path}"}), 400
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
        else:
            return jsonify({'error': 'No file uploaded or demo image selected'}), 400

        tensor, pil_img = preprocess_image(image_bytes)
        result = predict_with_uncertainty(model, tensor, DEVICE, temperature, mc_samples)

        calibrated_prob = result['calibrated_probability']
        raw_prob = result['raw_probability']
        # Optional: invert class mapping if model outputs are reversed
        if os.getenv("INVERT_LABELS", "false").lower() == "true":
            calibrated_prob = 1.0 - calibrated_prob
            raw_prob = 1.0 - raw_prob
        mc_std = result['uncertainty']

        if mc_std > 0.15:
            clinical_message = "⚠️ LOW CONFIDENCE — Human diagnostic review required"
            confidence_level = "LOW"
            color_code = "yellow"
        elif calibrated_prob >= 0.75:
            clinical_message = "🔴 High likelihood of dementia-related changes"
            confidence_level = "HIGH"
            color_code = "red"
        elif calibrated_prob < 0.62:
            clinical_message = "🟢 No significant changes detected"
            confidence_level = "HIGH"
            color_code = "green"
        else:
            clinical_message = "🟡 INDETERMINATE — Clinical correlation recommended"
            confidence_level = "MODERATE"
            color_code = "orange"

        binary_prediction = (
            "Dementia-related changes detected"
            if calibrated_prob >= threshold
            else "No significant changes detected"
        )

        buffered = io.BytesIO()
        pil_img.save(buffered, format="JPEG")
        encoded_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return jsonify({
            'raw_probability': raw_prob,
            'calibrated_probability': calibrated_prob,
            'uncertainty': mc_std,
            'attention_map': result['attention_map'],
            'clinical_message': clinical_message,
            'confidence_level': confidence_level,
            'color_code': color_code,
            'binary_prediction': binary_prediction,
            'preprocessed_image_b64': f"data:image/jpeg;base64,{encoded_image}"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f"Inference execution error: {str(e)}"}), 500


@app.route('/api/demo-images', methods=['GET'])
def get_demo_images():
    """Scans demo_images subdirectories for the gallery."""
    if not os.path.exists(OASIS_DIR):
        return jsonify({'error': f"Demo images directory not found"}), 404

    categories = ["Mild Dementia", "Moderate Dementia", "Non Demented", "Very mild Dementia"]
    demo_data = {}

    for cat in categories:
        cat_path = os.path.join(OASIS_DIR, cat)
        if os.path.exists(cat_path):
            files = [f for f in os.listdir(cat_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            files.sort()
            demo_data[cat] = [
                {'name': f, 'relative_path': f"{cat}/{f}"}
                for f in files[:20]
            ]
        else:
            demo_data[cat] = []

    return jsonify(demo_data)


@app.route('/api/demo-image-file/<path:filename>', methods=['GET'])
def serve_demo_image(filename):
    return send_from_directory(OASIS_DIR, filename)


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    report = {}
    if os.path.exists(REPORT_PATH):
        try:
            with open(REPORT_PATH, 'r') as f:
                report = json.load(f)
        except Exception as e:
            report = {"error": f"Failed to read report: {str(e)}"}
    else:
        report = {"error": "final_report.json not found"}

    figures = []
    if os.path.exists(FIGURES_DIR):
        figures = [f for f in os.listdir(FIGURES_DIR) if f.lower().endswith('.png')]
        figures.sort()

    return jsonify({'metrics': report, 'figures': figures})


@app.route('/api/figures/<path:filename>', methods=['GET'])
def serve_figure(filename):
    return send_from_directory(FIGURES_DIR, filename)


# ──────────────────────────────────────────────────────────────────────────────
# Serve React Frontend (production build)
# ──────────────────────────────────────────────────────────────────────────────

@app.route('/')
def serve_index():
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(STATIC_DIR, 'assets'), filename)


@app.route('/<path:path>')
def serve_fallback(path):
    """SPA fallback — serve index.html for all unmatched routes."""
    file_path = os.path.join(STATIC_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, 'index.html')


# ──────────────────────────────────────────────────────────────────────────────
# Startup
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    try:
        load_cached_model()
    except Exception as ex:
        print(f"Warning: Could not preload model ({str(ex)}). Will retry on first request.")

    app.run(host='0.0.0.0', port=7860, debug=False)
