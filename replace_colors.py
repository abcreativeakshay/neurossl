import os
import re

replacements = {
    r'#38bdf8': '#34d399',
    r'#0ea5e9': '#10b981',
    r'#0284c7': '#059669',
    r'#0369a1': '#047857',
    r'#8b5cf6': '#d97706',
    r'#6366F1': '#059669',
    r'#8B5CF6': '#d97706',
    r'#A5B4FC': '#6ee7b7',
    
    # RGBA strings
    r'2,\s*132,\s*199': '5, 150, 105',
    r'14,\s*165,\s*233': '16, 185, 129',
    r'56,\s*189,\s*248': '52, 211, 153',
    r'139,\s*92,\s*246': '217, 119, 6',
    r'3,\s*105,\s*161': '4, 120, 87',
    r'99,\s*102,\s*241': '5, 150, 105',
}

files = [
    'frontend/src/App.css',
    'cloudflare_worker/src/index.js'
]

for filepath in files:
    with open(filepath, 'r') as f:
        content = f.read()
        
    original = content
    for old, new in replacements.items():
        content = re.sub(old, new, content, flags=re.IGNORECASE)
        
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Updated {filepath}")
