import torch, numpy as np, os, sys, glob
sys.path.append("/Users/akshaybiradar/Downloads/neuro_ssl/backend")
from model import get_model, preprocess_image, predict_with_uncertainty

ckpt = "/Users/akshaybiradar/Downloads/neuro_ssl/Data/raw/neuro_ssl_outputs/outputs/checkpoints/finetune/fold_0/checkpoint_best.pt"
device = torch.device('cpu')
model = get_model(ckpt, device)

base = "/Users/akshaybiradar/Downloads/neuro_ssl/hf_space/data/demo_images"
for cat in ["Mild Dementia", "Non Demented"]:
    imgs = sorted(glob.glob(os.path.join(base, cat, "*.jpg")))[:10]
    probs = []
    for p in imgs:
        with open(p,'rb') as f: data=f.read()
        t,_ = preprocess_image(data)
        r = predict_with_uncertainty(model, t, device, temperature=1.6995, mc_samples=0)
        probs.append(r['calibrated_probability'])
    print(f"\n{cat}: mean_cal_prob={np.mean(probs):.4f}  min={np.min(probs):.4f}  max={np.max(probs):.4f}")
    for i,p in enumerate(probs):
        print(f"  [{i}] cal_prob={p:.4f}  label_at_0.5={'DEM' if p>=0.5 else 'NON'}  label_at_0.75={'DEM' if p>=0.75 else 'NON'}")
