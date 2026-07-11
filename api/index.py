import os
import sys
from flask import Flask

# Root directory ko Python ke path mein add karna taaki app.py mil sake
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    # Aapke app.py ko import karne ki koshish karega
    from app import app
except Exception as e:
    import traceback
    error_app = Flask(__name__)
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def catch_all_errors(path):
        error_details = traceback.format_exc()
        return f"""
        <div style="font-family: monospace; padding: 20px; background: #fff5f5; color: #c53030; border: 1px solid #feb2b2; border-radius: 5px; max-width: 800px; margin: 20px auto;">
            <h2 style="margin-top: 0;">❌ Problem detected in app.py!</h2>
            <p><strong>Error Message:</strong> {str(e)}</p>
            <pre style="background: #fff; padding: 15px; border: 1px solid #cbd5e0; overflow-x: auto; white-space: pre-wrap;">{error_details}</pre>
        </div>
        """, 500
        
    app = error_app