import pathlib
import sys

FILE = pathlib.Path(__file__).resolve()
MODULE_DIR = FILE.parent  # repository root
REPO_ROOT_DIR = MODULE_DIR.parent
MODEL_DIR = REPO_ROOT_DIR / 'models'
if str(REPO_ROOT_DIR) not in sys.path:
    sys.path.append(str(REPO_ROOT_DIR))

