import streamlit as st
from utils import ENV, vis_bruk_dette_forst



st.set_page_config(page_title="Kjøkkenappen", page_icon="🍳")

st.title("🏠 Varer hjemme")

if ENV == "dev":
    st.caption("🛠 Utviklingsmiljø")

vis_bruk_dette_forst(key_prefix="forside")

st.divider()
st.info("Velg side i menyen til venstre.")
