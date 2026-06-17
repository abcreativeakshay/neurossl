import time
from huggingface_hub import HfApi
api = HfApi()

for i in range(30):
    try:
        runtime = api.get_space_runtime("ABCREATIVEAKSHAY/neuro-ssl")
        print(f"[{i*5}s] Stage: {runtime.stage}")
        if runtime.stage == "RUNNING":
            print("🚀 Space is fully RUNNING and live with the new code!")
            break
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(5)
