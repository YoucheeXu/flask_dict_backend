#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

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

    try:
        cfgfile = os.path.join(proj_path, "server.json")
        dict_app = DictApp(proj_path)
        _ = dict_app.read_configure(cfgfile)
        print(f"DictApp initialized successfully: {cfgfile}")
        _dict_app_instance = dict_app  # Cache the singleton instance
        return dict_app
    except Exception as e:
        raise RuntimeError(f"Failed to initialize DictApp: {str(e)}") from e
