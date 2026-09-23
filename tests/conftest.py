import os
import sys

# Mantis resolves configs/local.yml relative to the working directory
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
