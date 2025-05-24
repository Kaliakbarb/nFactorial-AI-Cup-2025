import os

port = os.environ.get("PORT", 8000)
os.system(f"streamlit run main.py --server.port={port} --server.address=0.0.0.0")
