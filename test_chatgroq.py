import streamlit as st
import os

st.title("My Demo App")

# read secret via st.secrets or env var
api_key = st.secrets.get("OPENAI_API_KEY") if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")
st.write("API key present:", bool(api_key))
