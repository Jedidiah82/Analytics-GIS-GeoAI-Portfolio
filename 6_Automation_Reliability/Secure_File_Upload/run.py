#!/usr/bin/env python3
import requests
import os

url = "http://localhost/fruits/"
desc_dir = "supplier-data/descriptions"

for file in os.listdir(desc_dir):
    with open(f"{desc_dir}/{file}") as f:
        lines = f.read().splitlines()

    payload = {
        "name": lines[0],
        "weight": int(lines[1].split()[0]),
        "description": lines[2],
        "image_name": file.replace(".txt", ".jpeg")
    }

    response = requests.post(url, json=payload)
    print(response.status_code, payload["name"])
