from huggingface_hub import HfApi
api = HfApi()
try:
    runtime = api.get_space_runtime("ABCREATIVEAKSHAY/neuro-ssl")
    print(f"Space Status: {runtime.stage}")
    print(f"Hardware: {runtime.hardware}")
    print(f"Raw Runtime: {runtime}")
except Exception as e:
    print(f"Error querying space: {e}")
