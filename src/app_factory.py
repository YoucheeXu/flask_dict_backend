#!/usr/bin/python3
import os

from src.app.dictapp import DictApp

# Singleton instance of DictApp
_dict_app_instance = None

def get_dict_app(proj_path: str) -> DictApp:
    """Create or retrieve the singleton DictApp instance (reuses DictApi's initialization logic).
    
    Returns:
        DictApp: Singleton instance of DictApp
        
    Raises:
        RuntimeError: If initialization fails (e.g., missing server.json)
    """
    global _dict_app_instance
    if _dict_app_instance is not None:
        return _dict_app_instance  # Reuse existing instance

    cfgfile = os.path.join(proj_path, "server.json")
    dict_app = DictApp(proj_path)
    ret = dict_app.read_configure(cfgfile)
    if ret:
        print(f"DictApp initialized successfully: {cfgfile}")
    else:
        print(f"There is no cfg file: {cfgfile}")
    _dict_app_instance = dict_app  # Cache the singleton instance
    return dict_app
