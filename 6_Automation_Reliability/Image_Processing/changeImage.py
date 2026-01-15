#!/usr/bin/env python3
from PIL import Image
import os

source = "supplier-data/images"
dest = "supplier-data/images/processed"

os.makedirs(dest, exist_ok=True)

for file in os.listdir(source):
    if file.endswith(".tiff"):
        img = Image.open(f"{source}/{file}")
        img = img.convert("RGB")
        img = img.resize((600, 400))

        new_name = file.replace(".tiff", ".jpeg")
        img.save(f"{dest}/{new_name}", "JPEG")
