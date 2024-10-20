import os, sys, json

sys.path.append('./libs')

import tools.utils  as utils

pkg_list=[
    "chromadb",
    "langchain",
    "pyngrok",
    "lark",
    "streamlit",
    "optimum",
    "transformers",
    "huggingface_hub",
    "sentence-transformers",
    "langchain-huggingface",
    "langchain-community",
    "langchain-chroma",
    "langchain-text-splitters",
    "langchain-ollama"
]
print("---------------------------------------------",flush=True)
print("Installing python modules",flush=True)
utils.pip_install(pkg_list)
print("Done!",flush=True)
print("---------------------------------------------",flush=True)