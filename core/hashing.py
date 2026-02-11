import hashlib
import os
import shutil
import time

def get_file_hash(path: str) -> str:
    """Generates a SHA-256 hash of a file's content with retry logic."""
    if not os.path.exists(path): 
        return None
    
    sha256_hash = hashlib.sha256()
    attempts = 0
    while attempts < 3:
        try:
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except PermissionError:
            time.sleep(0.1)
            attempts += 1
        except Exception:
            return None
    return None

def ensure_vault(project_path: str) -> str:
    vault_path = os.path.join(project_path, ".sci_vault")
    os.makedirs(vault_path, exist_ok=True)
    return vault_path

def save_to_vault(file_path: str, project_path: str) -> str:
    """Copies file to vault named by its hash."""
    file_hash = get_file_hash(file_path)
    if not file_hash: return None
    
    vault_dir = ensure_vault(project_path)
    dest = os.path.join(vault_dir, f"{file_hash}.csv")
    
    if not os.path.exists(dest):
        try:
            shutil.copy2(file_path, dest)
        except Exception as e:
            print(f"Vault Backup Failed: {e}")
            return None
            
    return file_hash