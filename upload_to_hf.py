"""
NeuroSSL — Upload Model to Hugging Face Hub
============================================
Uploads the model checkpoint, architecture code, config, and model card
to a Hugging Face Model repository.

Usage:
    python upload_to_hf.py
"""

import os
from huggingface_hub import HfApi, login

# ─── Configuration ───────────────────────────────────────────────────────────
HF_USERNAME = "ABCREATIVEAKSHAY"
REPO_NAME = "neuro-ssl-dementia-classifier"
REPO_ID = f"{HF_USERNAME}/{REPO_NAME}"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_REPO_DIR = os.path.join(PROJECT_DIR, "hf_model_repo")

# Path to your best fine-tuned checkpoint
CHECKPOINT_SRC = os.path.join(
    PROJECT_DIR,
    "Data", "raw", "neuro_ssl_outputs", "outputs",
    "checkpoints", "finetune", "fold_0", "checkpoint_best.pt"
)

CHECKPOINT_DST = os.path.join(MODEL_REPO_DIR, "checkpoint_best.pt")


def main():
    # ── Step 1: Login ────────────────────────────────────────────────────────
    print("🔐 Step 1: Logging in to Hugging Face...")
    print("   You'll need a token with WRITE access.")
    print("   Get one at: https://huggingface.co/settings/tokens")
    print()
    login()  # Will prompt for token interactively
    print("✅ Logged in successfully!\n")

    # ── Step 2: Symlink / copy checkpoint into repo dir ──────────────────────
    print("📦 Step 2: Preparing checkpoint...")
    if not os.path.exists(CHECKPOINT_SRC):
        print(f"❌ ERROR: Checkpoint not found at:\n   {CHECKPOINT_SRC}")
        print("   Please check the path and try again.")
        return

    if not os.path.exists(CHECKPOINT_DST):
        print(f"   Creating symlink to avoid duplicating 2.6 GB file...")
        os.symlink(CHECKPOINT_SRC, CHECKPOINT_DST)
        print(f"   ✅ Symlinked checkpoint_best.pt")
    else:
        print(f"   ✅ Checkpoint already present at {CHECKPOINT_DST}")

    # ── Step 3: Create or get the repo ───────────────────────────────────────
    print(f"\n🌐 Step 3: Creating HF repo '{REPO_ID}'...")
    api = HfApi()
    try:
        api.create_repo(
            repo_id=REPO_ID,
            repo_type="model",
            exist_ok=True,
            private=False,
        )
        print(f"   ✅ Repository ready: https://huggingface.co/{REPO_ID}")
    except Exception as e:
        print(f"   ⚠️  Repo creation note: {e}")

    # ── Step 4: Upload the entire folder ─────────────────────────────────────
    print(f"\n🚀 Step 4: Uploading to https://huggingface.co/{REPO_ID} ...")
    print("   This may take a while for the 2.6 GB checkpoint...\n")

    api.upload_folder(
        folder_path=MODEL_REPO_DIR,
        repo_id=REPO_ID,
        repo_type="model",
        commit_message="Upload NeuroSSL dementia classifier — model weights, architecture, and config",
        ignore_patterns=[".*", "__pycache__"],
    )

    print(f"\n{'='*60}")
    print(f"🎉 SUCCESS! Model uploaded to Hugging Face!")
    print(f"{'='*60}")
    print(f"\n   🔗 https://huggingface.co/{REPO_ID}")
    print(f"\n   Files uploaded:")
    print(f"     • README.md          (model card)")
    print(f"     • config.json        (architecture config)")
    print(f"     • model.py           (model code)")
    print(f"     • checkpoint_best.pt (trained weights, ~2.6 GB)")
    print(f"\n   To download in code:")
    print(f"     from huggingface_hub import hf_hub_download")
    print(f"     path = hf_hub_download(repo_id='{REPO_ID}', filename='checkpoint_best.pt')")
    print()


if __name__ == "__main__":
    main()
