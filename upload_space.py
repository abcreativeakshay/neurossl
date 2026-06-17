from huggingface_hub import HfApi
import os

api = HfApi()
repo_id = "ABCREATIVEAKSHAY/neuro-ssl"
folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hf_space")

print(f"Uploading {folder_path} to {repo_id}...")
api.upload_folder(
    folder_path=folder_path,
    repo_id=repo_id,
    repo_type="space",
    commit_message="Fix model download repo env var and update UI colors"
)
print("Done!")
