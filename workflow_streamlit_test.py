import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

st.title("Autonomous Research Analyst - Import Test")
st.write("Streamlit page loaded.")

from app.graph.workflow import research_graph

st.success("Research workflow imported successfully.")
st.write(research_graph)
