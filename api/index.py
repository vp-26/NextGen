import os
import sys

# Root directory ko Python ke path mein add karna taaki app.py mil sake
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app
