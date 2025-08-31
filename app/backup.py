from __future__ import annotations
from pathlib import Path
import tarfile
import lz4.frame as lz4
import logging
from typing import List
from .utils import TEMP_DIR
from .crypto import encrypt_file
import io

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _create_archive(sources: List[str]) -> bytes:
    """
    Creates a .tar.lz4 archive in memory and returns its bytes.
    """
    stream = io.BytesIO()
    
    with tarfile.open(fileobj=stream, mode="w") as tar:
        for src in sources:
            p = Path(src)
            try:
                tar.add(p, arcname=p.name)
            except Exception as e:
                logging.warning(f"Could not add {p} to archive, skipping. Reason: {e}")

    stream.seek(0)
    
    ### CHANGE ###
    # Replaced the incorrect constant with a valid integer compression level.
    # A level of 9 is a high-compression, high-speed setting for LZ4.
    compressed_data = lz4.compress(stream.read(), compression_level=9)
    
    return compressed_data

def run_backup(sources: List[str], destination_folder: str, password: str, output_filename: str) -> Path:
    dest_dir = Path(destination_folder)
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info("Starting to create in-memory TAR archive...")
    archive_bytes = _create_archive(sources)
    logging.info("Archiving and LZ4 compression complete.")
    
    out_path = dest_dir / output_filename
    
    tmp_archive_path = TEMP_DIR / f"payload_{Path(output_filename).stem}.tar.lz4"
    try:
        tmp_archive_path.write_bytes(archive_bytes)
        
        logging.info(f"Encrypting file to {out_path}...")
        encrypt_file(tmp_archive_path, out_path, password)
        logging.info("Encryption complete.")
    finally:
        if tmp_archive_path.exists():
            tmp_archive_path.unlink()
        
    return out_path