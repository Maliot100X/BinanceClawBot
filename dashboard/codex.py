#!/usr/bin/env python3
import sys
import os

# Set root to parent directory
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

# Import the actual main from the root codex.py
from codex import main

if __name__ == "__main__":
    main()
