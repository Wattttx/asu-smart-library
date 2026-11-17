"""
Vercel Serverless Function Entry Point for Assam Skill University Smart Library
Proxies API requests into the LibraryRequestHandler.
"""

import sys
import os

# Ensure project root is in path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from database import init_db, seed_data
from server import LibraryRequestHandler

# Ensure database is seeded in /tmp if running on Vercel
try:
    init_db()
    seed_data(force=False)
except Exception as e:
    print(f"Database setup note: {e}")

class handler(LibraryRequestHandler):
    def __init__(self, *args, **kwargs):
        # Override directory to absolute path of static folder
        static_dir = os.path.join(root_dir, "static")
        super().__init__(*args, directory=static_dir, **kwargs)
