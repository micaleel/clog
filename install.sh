#!/usr/bin/env bash
set -e

python -m venv .venv
source .venv/bin/activate
expected=clog/.venv/bin/python
actual=$(which python)

if [[ $actual == *$expected* ]]; then
	pip install --upgrade pip  --quiet
	pip install -r requirements.txt --quiet
	pip install -e . --quiet
	echo "✨✨ Clog is installed! ✨✨"
else
	echo "Installation aborted! Ensure that:"
	echo "  [1] virtual environment is activated, and"
	echo "  [2] make install is run from project root"
fi
