import streamlit as st

from workspace import render_app

st.set_page_config(
    page_title="VoC Product Intelligence",
    page_icon="V",
    layout="wide",
    initial_sidebar_state="collapsed",
)

render_app()
