import sys
import os

print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")

try:
    import app
    print("Found app package")
except ImportError as e:
    print(f"Could not import app: {e}")

try:
    from app.schema import WearableEvent
    print("Found WearableEvent")
except ImportError as e:
    print(f"Could not import WearableEvent: {e}")

try:
    from rag.retriever import retriever
    print("Found RAG retriever")
except ImportError as e:
    print(f"Could not import rag: {e}")
