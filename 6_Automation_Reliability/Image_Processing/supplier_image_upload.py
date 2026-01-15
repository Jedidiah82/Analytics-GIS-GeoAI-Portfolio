#!/usr/bin/env python3
import requests
import os

url = "http://localhost/upload/"
path = "supplier-data/images/processed"

for img in os.listdir(path):
    with open(f"{path}/{img}", "rb") as f:
        response = requests.post(url, files={"file": f})
        print(response.status_code, img)
