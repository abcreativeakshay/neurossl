#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# NeuroSSL — Hugging Face Spaces Deployment Setup Script
# ─────────────────────────────────────────────────────────────────
# This script packages the application into a deployment-ready
# directory that can be pushed to a Hugging Face Space.
#
# Usage: bash setup_deploy.sh
# ─────────────────────────────────────────────────────────────────

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEPLOY_DIR="$PROJECT_DIR/deploy"
HF_SPACE_DIR="$PROJECT_DIR/hf_space"

echo "🧠 NeuroSSL — Packaging for Hugging Face Spaces"
echo "================================================"

# 1. Build the React frontend for production
echo ""
echo "📦 Step 1: Building React frontend..."
cd "$PROJECT_DIR/frontend"
npm run build
echo "✅ Frontend built successfully."

# 2. Create the hf_space output directory
echo ""
echo "📂 Step 2: Creating hf_space/ directory..."
rm -rf "$HF_SPACE_DIR"
mkdir -p "$HF_SPACE_DIR/static"
mkdir -p "$HF_SPACE_DIR/data/demo_images"
mkdir -p "$HF_SPACE_DIR/data/figures"
mkdir -p "$HF_SPACE_DIR/checkpoints"

# 3. Copy deployment files
echo "📄 Step 3: Copying deployment files..."
cp "$DEPLOY_DIR/README.md" "$HF_SPACE_DIR/"
cp "$DEPLOY_DIR/Dockerfile" "$HF_SPACE_DIR/"
cp "$DEPLOY_DIR/requirements.txt" "$HF_SPACE_DIR/"
cp "$DEPLOY_DIR/app.py" "$HF_SPACE_DIR/"
cp "$PROJECT_DIR/backend/model.py" "$HF_SPACE_DIR/"

# 4. Copy built frontend
echo "🌐 Step 4: Copying built React frontend..."
cp -r "$PROJECT_DIR/frontend/dist/"* "$HF_SPACE_DIR/static/"

# 5. Copy data assets
echo "📊 Step 5: Copying data assets..."

# Figures
FIGURES_SRC="$PROJECT_DIR/Data/raw/neuro_ssl_outputs/outputs/figures"
if [ -d "$FIGURES_SRC" ]; then
    cp "$FIGURES_SRC"/*.png "$HF_SPACE_DIR/data/figures/" 2>/dev/null || echo "   (no PNG figures found)"
    echo "   ✅ Figures copied."
else
    echo "   ⚠️  Figures directory not found at: $FIGURES_SRC"
fi

# Report JSON
REPORT_SRC="$PROJECT_DIR/Data/raw/neuro_ssl_outputs/outputs/final_report.json"
if [ -f "$REPORT_SRC" ]; then
    cp "$REPORT_SRC" "$HF_SPACE_DIR/data/"
    echo "   ✅ final_report.json copied."
else
    echo "   ⚠️  final_report.json not found at: $REPORT_SRC"
fi

# Demo images (subset — 10 per category to keep size manageable)
OASIS_SRC="$PROJECT_DIR/Data/raw/neuro_ssl_outputs/data/raw/oasis_2d"
if [ -d "$OASIS_SRC" ]; then
    for category in "Mild Dementia" "Moderate Dementia" "Non Demented" "Very mild Dementia"; do
        cat_src="$OASIS_SRC/$category"
        cat_dst="$HF_SPACE_DIR/data/demo_images/$category"
        if [ -d "$cat_src" ]; then
            mkdir -p "$cat_dst"
            # Copy first 10 images per category (robust to spaces)
            copy_count=0
            for img_file in "$cat_src"/*.jpg "$cat_src"/*.png; do
                if [ -f "$img_file" ]; then
                    cp "$img_file" "$cat_dst/"
                    copy_count=$((copy_count + 1))
                    if [ $copy_count -ge 10 ]; then
                        break
                    fi
                fi
            done
            count=$(ls "$cat_dst" 2>/dev/null | wc -l | tr -d ' ')
            echo "   ✅ $category: $count demo images copied."
        fi
    done
else
    echo "   ⚠️  OASIS directory not found at: $OASIS_SRC"
fi

# 6. Create .gitattributes for LFS (checkpoint is large)
echo ""
echo "📝 Step 6: Creating .gitattributes for Git LFS..."
cat > "$HF_SPACE_DIR/.gitattributes" << 'EOF'
*.pt filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.safetensors filter=lfs diff=lfs merge=lfs -text
EOF

echo ""
echo "================================================"
echo "✅ Deployment package ready at: $HF_SPACE_DIR"
echo ""
echo "📁 Contents:"
find "$HF_SPACE_DIR" -type f | head -30
echo ""
echo "Next Steps:"
echo "  1. Create a Hugging Face account at https://huggingface.co"
echo "  2. Create a new Space: https://huggingface.co/new-space"
echo "     - Choose 'Docker' as the SDK"
echo "     - Select 'CPU basic' (free) or a GPU tier"
echo "  3. Clone the empty Space repo:"
echo "     git clone https://huggingface.co/spaces/YOUR_USERNAME/neuro-ssl"
echo "  4. Copy hf_space/ contents into the cloned repo:"
echo "     cp -r $HF_SPACE_DIR/* ./neuro-ssl/"
echo "  5. Upload your model checkpoint:"
echo "     Option A: Upload to HF Model repo and set HF_MODEL_REPO secret"
echo "     Option B: Copy checkpoint directly (needs Git LFS):"
echo "       cp /path/to/checkpoint_best.pt ./neuro-ssl/checkpoints/"
echo "  6. Push to HF:"
echo "     cd neuro-ssl && git add . && git commit -m 'Deploy NeuroSSL' && git push"
echo ""
