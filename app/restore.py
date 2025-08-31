from __future__ import annotations
from pathlib import Path
import tarfile
import lz4.frame as lz4
from .crypto import decrypt_file
from .utils import TEMP_DIR
import io

def run_restore(encrypted_path: str, output_folder: str, password: str) -> None:
    enc = Path(encrypted_path)
    out_dir = Path(output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)

    tmp_compressed = TEMP_DIR / (enc.stem + ".tar.lz4")
    try:
        decrypt_file(enc, tmp_compressed, password)
        
        with open(tmp_compressed, 'rb') as f_in:
            compressed_data = f_in.read()
            decompressed_data = lz4.decompress(compressed_data)
        
        stream = io.BytesIO(decompressed_data)
        stream.seek(0)
        
        with tarfile.open(fileobj=stream, mode="r") as tar:
            tar.extractall(path=out_dir)

    finally:
        if tmp_compressed.exists():
            try:
                tmp_compressed.unlink()
            except Exception:
                pass