import os
import sys

# Root directory ko Python ke path mein add karna taaki app.py mil sake
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Direct app ko import karna bina kisi try-except ke taaki Vercel ko top-level 'app' mil jaye
from app import app