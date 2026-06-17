import os
import io
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from PIL import Image
from einops import rearrange

class DropPath(nn.Module):
    def __init__(self, drop_prob=0.0):
        super().__init__()
        self.drop_prob = drop_prob
    def forward(self, x):
        if self.drop_prob == 0.0 or not self.training:
            return x
        keep_prob = 1 - self.drop_prob
        shape = (x.shape[0],) + (1,) * (x.ndim - 1)
        random_tensor = keep_prob + torch.rand(shape, dtype=x.dtype, device=x.device)
        random_tensor.floor_()
        return x.div(keep_prob) * random_tensor

class PatchEmbed2D(nn.Module):
    def __init__(self, img_size, patch_size, in_chans=1, embed_dim=384):
        super().__init__()
        self.patch_size = patch_size
        self.num_patches = (img_size[0] // patch_size[0]) * (img_size[1] // patch_size[1])
        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)
    def forward(self, x):
        x = self.proj(x)
        return rearrange(x, 'b e h w -> b (h w) e')

class TransformerBlock(nn.Module):
    def __init__(self, embed_dim, num_heads, mlp_ratio=4.0, dropout=0.0, drop_path=0.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = nn.MultiheadAttention(embed_dim, num_heads, dropout=dropout, batch_first=True)
        self.norm2 = nn.LayerNorm(embed_dim)
        mlp_dim = int(embed_dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, mlp_dim), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(mlp_dim, embed_dim), nn.Dropout(dropout)
        )
        self.drop_path = DropPath(drop_path)
    def forward(self, x):
        x_norm = self.norm1(x)
        attn_out, attn_weights = self.attn(x_norm, x_norm, x_norm, need_weights=True, average_attn_weights=False)
        x = x + self.drop_path(attn_out)
        x = x + self.drop_path(self.mlp(self.norm2(x)))
        return x, attn_weights

class MultiScaleViT2DEncoder(nn.Module):
    def __init__(self, img_size, patch_size, embed_dim=384, depth=12, num_heads=6,
                 mlp_ratio=4.0, dropout=0.0, drop_path_rate=0.1):
        super().__init__()
        self.patch_embed = PatchEmbed2D(img_size, patch_size, 1, embed_dim)
        num_patches = self.patch_embed.num_patches
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches+1, embed_dim))
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, depth)]
        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads, mlp_ratio, dropout, dpr[i]) for i in range(depth)
        ])
        self.norm = nn.LayerNorm(embed_dim)
        self.scale_indices = [2, 5, 8, 11]
        self.scale_fusion = nn.Sequential(
            nn.Linear(embed_dim * len(self.scale_indices), embed_dim), nn.GELU(), nn.LayerNorm(embed_dim)
        )
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        nn.init.trunc_normal_(self.cls_token, std=0.02)
    def forward(self, x, mask=None, return_all_tokens=False):
        B = x.size(0)
        tokens = self.patch_embed(x)
        tokens = tokens + self.pos_embed[:, 1:tokens.shape[1]+1]
        if mask is not None:
            tokens = tokens[mask].reshape(B, -1, tokens.size(-1))
        cls = self.cls_token.expand(B, -1, -1)
        tokens = torch.cat([cls, tokens], dim=1)
        tokens = tokens + self.pos_embed[:, :tokens.shape[1]]
        intermediate_features = []
        attn_maps = []
        for i, block in enumerate(self.blocks):
            tokens, attn = block(tokens)
            if i in self.scale_indices:
                intermediate_features.append(tokens[:, 1:])
            attn_maps.append(attn)
        tokens = self.norm(tokens)
        if len(intermediate_features) > 0:
            pooled_scales = [f.mean(dim=1) for f in intermediate_features]
            multi_scale_vec = torch.cat(pooled_scales, dim=-1)
            multi_scale_vec = self.scale_fusion(multi_scale_vec)
        else:
            multi_scale_vec = tokens[:, 0]
        if return_all_tokens:
            return tokens, multi_scale_vec, attn_maps
        return tokens

class SecondOrderClassifier(nn.Module):
    def __init__(self, encoder, num_classes=2, dropout=0.3, use_second_order=True):
        super().__init__()
        self.encoder = encoder
        self.use_second_order = use_second_order
        embed_dim = encoder.blocks[0].norm1.normalized_shape[0]
        if use_second_order:
            self.cov_proj = nn.Sequential(
                nn.Linear(embed_dim * embed_dim, embed_dim * 4), nn.GELU(), nn.Dropout(dropout),
                nn.Linear(embed_dim * 4, embed_dim)
            )
            self.head = nn.Sequential(
                nn.LayerNorm(embed_dim * 2), nn.Dropout(dropout), nn.Linear(embed_dim * 2, num_classes)
            )
        else:
            self.head = nn.Sequential(nn.LayerNorm(embed_dim), nn.Dropout(dropout), nn.Linear(embed_dim, num_classes))
        self.mc_dropout = nn.Dropout(dropout)
    def forward(self, x, return_features=False, mc_dropout=False):
        tokens, multi_scale, _ = self.encoder(x, return_all_tokens=True)
        cls = tokens[:, 0]
        if self.use_second_order:
            patches = tokens[:, 1:]
            mean_patches = patches.mean(dim=1, keepdim=True)
            centered = patches - mean_patches
            cov = torch.bmm(centered.transpose(1,2), centered) / centered.size(1)
            cov_vec = cov.reshape(cov.size(0), -1)
            second_order = self.cov_proj(cov_vec)
            second_order = F.normalize(second_order, p=2, dim=-1)
            features = torch.cat([cls, second_order], dim=-1)
        else:
            features = cls
        if mc_dropout:
            features = self.mc_dropout(features)
        logits = self.head(features)
        if return_features:
            return logits, features, cls
        return logits

def get_model(checkpoint_path, device):
    """Load model once and transfer to target device."""
    print(f"Loading checkpoint from {checkpoint_path}...")
    ckpt = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
    encoder = MultiScaleViT2DEncoder((224, 224), (16, 16), 384, 12, 6, drop_path_rate=0.0)
    model = SecondOrderClassifier(encoder, num_classes=2, dropout=0.3, use_second_order=True)
    model.load_state_dict(ckpt['model_state'])
    model = model.to(device).eval()
    print("Model loaded successfully!")
    return model

def preprocess_image(image_path_or_bytes, target_size=(224, 224)):
    """Convert and normalize image to Z-score tensor."""
    if isinstance(image_path_or_bytes, (str, bytes)) and isinstance(image_path_or_bytes, str):
        img = Image.open(image_path_or_bytes).convert('L')
    else:
        img = Image.open(io.BytesIO(image_path_or_bytes)).convert('L')
        
    img = img.resize((target_size[1], target_size[0]), Image.BILINEAR)
    tensor = torch.from_numpy(np.array(img, dtype=np.float32)).unsqueeze(0) / 255.0
    mu = tensor.mean()
    std = tensor.std() + 1e-8
    tensor = (tensor - mu) / std
    return tensor.unsqueeze(0), img

def attention_rollout(model, x, device):
    """Compute the vision transformer attention maps using rollout."""
    model.eval()
    with torch.no_grad():
        _, _, attn_maps = model.encoder(x.to(device), return_all_tokens=True)
        B = x.size(0)
        result = torch.eye(attn_maps[0].size(-1), device=device).unsqueeze(0).repeat(B, 1, 1)
        for attn in attn_maps:
            attn = attn.mean(dim=1)
            attn = attn + torch.eye(attn.size(-1), device=device).unsqueeze(0)
            attn = attn / attn.sum(dim=-1, keepdim=True)
            result = torch.bmm(result, attn)
        mask = result[:, 0, 1:]
        H = W = int(np.sqrt(mask.size(1)))
        mask = mask.reshape(B, H, W)
        mask = (mask - mask.min()) / (mask.max() - mask.min() + 1e-8)
    return mask

def predict_with_uncertainty(model, tensor, device, temperature=1.6995, mc_samples=10):
    """Run model inference, MC Dropout uncertainty estimation, and attention rollout."""
    tensor = tensor.to(device)
    
    # 1. Main deterministic calibrated prediction
    model.eval()
    with torch.no_grad():
        logits = model(tensor)
        raw_probs = torch.softmax(logits, dim=1)
        calibrated_logits = logits / temperature
        calibrated_probs = torch.softmax(calibrated_logits, dim=1)
        
    # 2. MC Dropout predictions for uncertainty quantification
    mc_probs = []
    if mc_samples > 0:
        model.train()
        with torch.no_grad():
            for _ in range(mc_samples):
                logit = model(tensor, mc_dropout=True)
                prob = torch.softmax(logit, dim=1)[:, 1]
                mc_probs.append(prob.item())
        model.eval()
        mc_std = np.std(mc_probs)
    else:
        mc_std = 0.0
    
    # 3. Attention rollout Map
    attn_mask = attention_rollout(model, tensor, device)
    attn_mask_np = attn_mask[0].cpu().numpy() # shape (14, 14)
    
    return {
        'raw_probability': float(raw_probs[0, 1]),
        'calibrated_probability': float(calibrated_probs[0, 1]),
        'uncertainty': float(mc_std),
        'attention_map': attn_mask_np.tolist() # converts to nested list (14x14)
    }
