
import sys
from pathlib import Path

def get_app_dir() -> Path:
    """
    Return the base directory for the application.
    - In source mode: directory of this file (CashMonitor root).
    - In frozen mode: directory of the executable.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent
