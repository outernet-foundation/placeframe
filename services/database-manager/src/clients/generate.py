#!/usr/bin/env python3
from pathlib import Path

from common.openapi import generate

from ..main import app

if __name__ == "__main__":
    generate(app, Path(__file__).resolve().parent, Path(__file__).resolve().parent / "python")
