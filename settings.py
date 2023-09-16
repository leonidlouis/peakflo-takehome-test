import os
import sys

if getattr(sys, "frozen", False):
    # If the application is run as a bundle/package
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
