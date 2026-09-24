import base64
import os
import shutil

os.makedirs('viral-image-templete', exist_ok=True)

srcs = [
    ('banner1', r'C:\Users\Mizan YT\Music\pdf_output\viral-image-templete\viral2.png', 'Image 1 (viral2)'),
    ('banner2', r'C:\Users\Mizan YT\Music\pdf_output\viral-image-templete\watch4.png', 'Image 2 (watch4)'),
    ('banner3', r'C:\Users\Mizan YT\Music\pdf_output\viral-image-templete\watch6.png', 'Image 3 (watch6)')
]

default_image_path = r'C:\Users\Mizan YT\Music\pdf_output\viral-image-templete\Screenshot 2026-09-09 092247.jpg'

js_content = "/** Preset Banner Images (Base64) **/\nconst PRESET_BANNERS = [\n"

for key, path, label in srcs:
    dest = os.path.join('viral-image-templete', os.path.basename(path))
    shutil.copy(path, dest)
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    mime = 'image/png' if path.endswith('.png') else 'image/jpeg'
    data_url = f"data:{mime};base64,{b64}"
    name = os.path.basename(path)
    js_content += f'  {{\n    id: "{key}",\n    name: "{name}",\n    label: "{label}",\n    dataUrl: "{data_url}"\n  }},\n'

js_content += "];\n\n"

# Process default image
dest = os.path.join('viral-image-templete', os.path.basename(default_image_path))
shutil.copy(default_image_path, dest)
with open(default_image_path, 'rb') as f:
    b64_default = base64.b64encode(f.read()).decode('utf-8')
mime_default = 'image/png' if default_image_path.endswith('.png') else 'image/jpeg'
default_data_url = f"data:{mime_default};base64,{b64_default}"

js_content += f'const FIXED_DEFAULT_BANNER_DATA_URL = "{default_data_url}";\n'

with open('default_banner_base64.js', 'w', encoding='utf-8') as f:
    f.write(js_content)

print("SUCCESS: 3 images + 1 default image converted to base64.")
