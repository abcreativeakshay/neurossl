import sys
import os
import glob
import io

# Add backend directory to path
sys.path.append(os.path.abspath("backend"))

from app import app

# Set testing mode
app.config['TESTING'] = True
client = app.test_client()

def test_upload(path):
    print(f"Testing API upload for {os.path.basename(path)}:")
    try:
        with open(path, 'rb') as f:
            img_bytes = f.read()
        
        # Use StringIO/BytesIO to simulate file upload
        data = {
            'file': (io.BytesIO(img_bytes), os.path.basename(path)),
            'temperature': '1.6995',
            'mc_samples': '10',
            'threshold': '0.70'
        }
        
        response = client.post('/api/predict', data=data, content_type='multipart/form-data')
        print(f"  Status Code: {response.status_code}")
        json_data = response.get_json()
        if response.status_code == 200:
            print(f"  Calibrated Prob: {json_data.get('calibrated_probability'):.4f}")
            print(f"  Prediction: {json_data.get('binary_prediction')}")
        else:
            print(f"  Error Message: {json_data.get('error')}")
    except Exception as e:
        print(f"  Error: {e}")
    print("-" * 50)

print("--- TESTING REAL OASIS SCAN ---")
oasis_files = glob.glob("Data/raw/neuro_ssl_outputs/data/raw/oasis_2d/**/*.jpg", recursive=True)
if oasis_files:
    test_upload(oasis_files[0])
else:
    print("OASIS images not found for testing.")

print("--- TESTING NON-MRI SCAN (1750576974109.png) ---")
if os.path.exists("1750576974109.png"):
    test_upload("1750576974109.png")

print("--- TESTING NON-MRI SCAN (images (1).jpeg) ---")
if os.path.exists("images (1).jpeg"):
    test_upload("images (1).jpeg")
