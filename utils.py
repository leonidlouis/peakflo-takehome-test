import os
from settings import BASE_DIR


def resolve_path(file_path: str) -> str:
    """Read a path, and returns an absolute version of that path"""
    if os.path.isabs(file_path):
        return file_path
    else:
        return os.path.join(BASE_DIR, file_path)
