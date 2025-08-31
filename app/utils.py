from __future__ import annotations
import os
from pathlib import Path


APP_NAME = "SecureBackup"


# %APPDATA% path on Windows
APPDATA_DIR = Path(os.getenv("APPDATA", str(Path.home() / ".config"))) / APP_NAME
APPDATA_DIR.mkdir(parents=True, exist_ok=True)


LOG_DIR = APPDATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


CONFIG_PATH = APPDATA_DIR / "config.toml"
KEYCHECK_PATH = APPDATA_DIR / "keycheck.bin" # stores encrypted verifier blob


TEMP_DIR = APPDATA_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)


### CHANGE ###
# Removed DEFAULT_BACKUP_NAME to prevent overwriting issues.
# Filenames are now generated dynamically in the GUI.


CHUNK_SIZE = 1024 * 1024 # 1MB streaming