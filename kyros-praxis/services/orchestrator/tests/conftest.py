import sys
from pathlib import Path

# Ensure 'services' within kyros-praxis is importable as a top-level package
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
