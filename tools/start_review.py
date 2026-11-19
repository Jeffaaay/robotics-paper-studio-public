"""Stage original sample media once, then start the local review room."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8893)
    args = parser.parse_args()
    destination = ROOT / 'output/launch30'
    destination.mkdir(parents=True, exist_ok=True)
    for sample in (ROOT / 'samples').iterdir():
        target = destination / sample.name
        if sample.is_file() and not target.exists():
            shutil.copy2(sample, target)
    subprocess.run([sys.executable, str(ROOT/'tools/review_server.py'), '--port', str(args.port)], check=True)
