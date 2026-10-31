#!/usr/bin/python3
import os
import threading
from _thread import lock

from src.app.dictapp import DictApp

# Singleton instance of DictApp
_dict_app_instance: DictApp | None = None
_dict_app_lock: lock = threading.Lock()

def get_dict_app(proj_path: str) -> DictApp:
    """Create or retrieve the singleton DictApp instance (reuses DictApi's initialization logic).
    
    Returns:
        DictApp: Singleton instance of DictApp
        
    Raises:
        RuntimeError: If initialization fails (e.g., missing server.json)
    """
    global _dict_app_instance
    if _dict_app_instance is not None:
        return _dict_app_instance
    with _dict_app_lock:
        if _dict_app_instance is not None:      # double-check
            return _dict_app_instance  # pyright: ignore[reportUnreachable]
        cfgfile = os.path.join(proj_path, "server.json")
        dict_app = DictApp(proj_path)
        ret = dict_app.read_configure(cfgfile)
        print(f"DictApp initialized: {cfgfile}" if ret else f"No cfg: {cfgfile}")
        _dict_app_instance = dict_app
        return dict_app
