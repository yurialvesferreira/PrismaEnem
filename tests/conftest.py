import os
import sys

# Garante que a raiz do projeto esteja no path para importar src/ e config/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
