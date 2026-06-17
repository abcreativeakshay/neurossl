import os
import io
import json
import base64
import torch
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from model import get_model, preprocess_image, predict_with_uncertainty

app = Flask(__name__)
# Enable CORS for the React dev server port
CORS(app)

# Workspace Absolute Paths
WORKSPACE_DIR = "/Users/akshaybiradar/Downloads/neuro_ssl"
CHECKPOINT_PATH = os.path.join(WORKSPACE_DIR, "Data/raw/neuro_ssl_outputs/outputs/checkpoints/finetune/fold_0/checkpoint_best.pt")
FIGURES_DIR = os.path.join(WORKSPACE_DIR, "Data/raw/neuro_ssl_outputs/outputs/figures")
OASIS_DIR = os.path.join(WORKSPACE_DIR, "Data/raw/neuro_ssl_outputs/data/raw/oasis_2d")
REPORT_PATH = os.path.join(WORKSPACE_DIR, "Data/raw/neuro_ssl_outputs/outputs/final_report.json")

# Device configuration
DEVICE = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Using device: {DEVICE}")

# Global model cache
MODEL = None

def load_cached_model():
    global MODEL
    if MODEL is None:
        if not os.path.exists(CHECKPOINT_PATH):
            raise FileNotFoundError(f"Checkpoint not found at: {CHECKPOINT_PATH}")
        MODEL = get_model(CHECKPOINT_PATH, DEVICE)
    return MODEL

@app.route('/api/predict', methods=['POST'])
def predict_endpoint():
    try:
        model = load_cached_model()
    except Exception as e:
        return jsonify({'error': f"Failed to load PyTorch model checkpoint: {str(e)}"}), 500

    # Retrieve parameters with defaults matching the notebook
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
            # Resolve image path relative to workspace or as absolute path
            if not os.path.isabs(image_path):
                image_path = os.path.join(OASIS_DIR, image_path)
            if not os.path.exists(image_path):
                return jsonify({'error': f"Image path not found: {image_path}"}), 400
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
        else:
            return jsonify({'error': 'No file uploaded or demo image selected'}), 400

        # Preprocess and run model
        tensor, pil_img = preprocess_image(image_bytes)
        result = predict_with_uncertainty(model, tensor, DEVICE, temperature, mc_samples)

        calibrated_prob = result['calibrated_probability']
        mc_std = result['uncertainty']

        # Clinical thresholds tuned to model output range (0.60-0.80)
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

        binary_prediction = "Dementia-related changes detected" if calibrated_prob >= threshold else "No significant neurodegeneration detected"

        # Base64 encode the preprocessed grayscale image for preview
        buffered = io.BytesIO()
        pil_img.save(buffered, format="JPEG")
        encoded_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return jsonify({
            'raw_probability': result['raw_probability'],
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
    """Scans raw oasis_2d subdirectories and returns limited selection for gallery."""
    if not os.path.exists(OASIS_DIR):
        return jsonify({'error': f"OASIS directory not found at: {OASIS_DIR}"}), 404

    categories = ["Mild Dementia", "Moderate Dementia", "Non Demented", "Very mild Dementia"]
    demo_data = {}

    for cat in categories:
        cat_path = os.path.join(OASIS_DIR, cat)
        if os.path.exists(cat_path):
            files = [f for f in os.listdir(cat_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            files.sort()
            demo_data[cat] = [
                {
                    'name': f,
                    'relative_path': f"{cat}/{f}"
                }
                for f in files[:20]
            ]
        else:
            demo_data[cat] = []

    return jsonify(demo_data)

@app.route('/api/demo-image-file/<path:filename>', methods=['GET'])
def serve_demo_image(filename):
    """Serves raw MRI scans from the OASIS directory."""
    return send_from_directory(OASIS_DIR, filename)

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Reads final_report.json and lists validation curves."""
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

    return jsonify({
        'metrics': report,
        'figures': figures
    })

@app.route('/api/figures/<path:filename>', methods=['GET'])
def serve_figure(filename):
    """Serves the generated training and calibration curves."""
    return send_from_directory(FIGURES_DIR, filename)

if __name__ == '__main__':
    try:
        load_cached_model()
    except Exception as ex:
        print(f"Warning: Could not preload models on startup ({str(ex)}). Will retry on first request.")
    
    app.run(host='0.0.0.0', port=5050, debug=False)
