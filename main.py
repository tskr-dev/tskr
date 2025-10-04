#!/usr/bin/env python3
"""Entry point for Tskr CLI - PyInstaller compatible."""

import os
import sys

# Add the src directory to Python path so we can import tskr
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_path)

from tskr.cli import app  # noqa

if __name__ == "__main__":
    app()
