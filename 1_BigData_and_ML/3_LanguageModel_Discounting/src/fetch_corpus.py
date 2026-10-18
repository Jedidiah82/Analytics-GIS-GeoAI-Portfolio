"""Download canonical Text8; never silently replace it with Wikipedia XML."""
import argparse
import hashlib
from pathlib import Path
import urllib.request
import zipfile

EXPECTED_SHA256 = '6e890197040d37d85beb962ae1f041ff1d9a9ca8d20c7d99c85027eebf51dca7'


def fetch(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / 'text8.zip'
    urllib.request.urlretrieve('https://mattmahoney.net/dc/text8.zip', archive)
    with zipfile.ZipFile(archive) as source:
        if source.namelist() != ['text8']:
            raise ValueError('Unexpected archive members')
        with source.open('text8') as stream, (destination / 'text8').open('wb') as target:
            while chunk := stream.read(1024 * 1024):
                target.write(chunk)
    digest = hashlib.sha256((destination / 'text8').read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError('Canonical Text8 checksum mismatch')
    print('Verified canonical Text8 SHA-256:', digest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', default='data')
    fetch(parser.parse_args().destination)
