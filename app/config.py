from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import tomlkit
from .utils import CONFIG_PATH

DEFAULTS = {
    "jobs": [],
}

def load_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        ### CHANGE ###
        # Convert the TomlKit document to a standard Python dictionary
        # to avoid issues with its custom, non-standard data types like TomlKit.Array.
        toml_doc = tomlkit.parse(CONFIG_PATH.read_text(encoding="utf-8"))
        return toml_doc.unwrap()
    save_config(DEFAULTS)
    return DEFAULTS.copy()

def save_config(cfg: Dict[str, Any]) -> None:
    # We can remove the old config structure since it's now simplified to just jobs
    config_to_save = {"jobs": cfg.get("jobs", [])}
    doc = tomlkit.dumps(config_to_save)
    CONFIG_PATH.write_text(doc, encoding="utf-8")