#!/bin/zsh
set -e
scanner_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$scanner_dir"
trap 'echo "Startup failed. Read the error above, then press Enter to close."; read' ZERR
if ! command -v python3 >/dev/null 2>&1; then
  echo "Install Python 3.9 or newer from https://www.python.org/downloads/ and try again."
  read
  exit 1
fi
if [[ ! -x "$scanner_dir/.venv/bin/python3" ]]; then
  python3 -m venv "$scanner_dir/.venv"
fi
if ! "$scanner_dir/.venv/bin/python3" -c 'import certifi' 2>/dev/null; then
  "$scanner_dir/.venv/bin/python3" -m pip install -r requirements.txt
fi
"$scanner_dir/.venv/bin/python3" front/server.py --open
