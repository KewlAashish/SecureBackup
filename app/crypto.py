from __future__ import annotations
from pathlib import Path
import os
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import hmac
from .utils import KEYCHECK_PATH, CHUNK_SIZE

backend = default_backend()


# Derive a 32-byte key using Scrypt
# Store only the salt and parameters (within the encrypted file header) — never the password.


def derive_key(password: str, salt: bytes, n: int = 2**14, r: int = 8, p: int = 1, length: int = 32) -> bytes:
    kdf = Scrypt(salt=salt, length=length, n=n, r=r, p=p, backend=backend)
    return kdf.derive(password.encode("utf-8"))

def _cipher(key: bytes, iv: bytes):
    return Cipher(algorithms.AES(key), modes.GCM(iv), backend=backend)  

# We use a simple verifier: create random 32 bytes, encrypt with derived key, store as keycheck.bin.
# Later, on password entry, attempt to decrypt — if it fails, password is wrong.


def ensure_keycheck(password: str) -> None:
    if KEYCHECK_PATH.exists():
        return  
    salt = os.urandom(16)
    key = derive_key(password, salt)
    iv = os.urandom(12)
    verify_plain = os.urandom(32)
    encryptor = _cipher(key, iv).encryptor()
    ct = encryptor.update(verify_plain) + encryptor.finalize()
    tag = encryptor.tag
    # file format: magic(4) | salt(16) | iv(12) | tag(16) | ct(32)
    KEYCHECK_PATH.write_bytes(b"SKCK" + salt + iv + tag + ct)


def verify_password(password: str) -> bool:
    if not KEYCHECK_PATH.exists():
        return True # first run (will be created by ensure_keycheck)
    blob = KEYCHECK_PATH.read_bytes()
    if len(blob) < 4 + 16 + 12 + 16 + 32 or blob[:4] != b"SKCK":
        return False
    salt = blob[4:20]
    iv = blob[20:32]
    tag = blob[32:48]
    ct = blob[48:]
    try:
        key = derive_key(password, salt)
        decryptor = _cipher(key, iv).decryptor()
        decryptor.authenticate_tag(tag)
        _ = decryptor.update(ct) + decryptor.finalize()
        return True
    except Exception:
        return False
    
# File encryption format for backups (.sbk):
# magic(4)=SBK1 | salt(16) | iv(12) | tag(16) | ciphertext(streamed)


HEADER_MAGIC = b"SBK1"
HEADER_LEN = 4 + 16 + 12 + 16 # 48 bytes

def encrypt_file(plaintext_path: Path, ciphertext_path: Path, password: str) -> None:
    salt = os.urandom(16)
    iv = os.urandom(12)
    key = derive_key(password, salt)

    cipher = _cipher(key, iv)
    encryptor = cipher.encryptor()

    with open(plaintext_path, "rb") as fin, open(ciphertext_path, "wb") as fout:
        # Write provisional header with zero tag; we'll seek back to write the real tag after finalize.
        fout.write(HEADER_MAGIC + salt + iv + (b"\x00" * 16))
        while True:
            chunk = fin.read(CHUNK_SIZE)
            if not chunk:
                break
            data = encryptor.update(chunk)
            if data:
                fout.write(data)
        encryptor.finalize()
        tag = encryptor.tag
        # Seek to tag position and write it
        fout.seek(4 + 16 + 12)
        fout.write(tag)

def decrypt_file(ciphertext_path: Path, out_plain_path: Path, password: str) -> None:
    with open(ciphertext_path, "rb") as fin, open(out_plain_path, "wb") as fout:
        header = fin.read(HEADER_LEN)
        if len(header) != HEADER_LEN or header[:4] != HEADER_MAGIC:
            raise ValueError("Not a SecureBackup file or header corrupted")
        salt = header[4:20]
        iv = header[20:32]
        tag = header[32:48]
        key = derive_key(password, salt)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()
        while True:
            chunk = fin.read(CHUNK_SIZE)
            if not chunk:
                break
            data = decryptor.update(chunk)
            if data:
                fout.write(data)
        decryptor.finalize()