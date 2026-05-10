import streamlit as st
from utils import ENV, vis_i_dag_stripe



st.set_page_config(page_title="Kjøkkenappen", page_icon="🍳")

vis_i_dag_stripe()

st.title("🍳 Kjøkkenappen")

if ENV == "dev":
    st.caption("🛠 Utviklingsmiljø")

st.write("Velkommen til kjøkkenassistenten din.")

st.info("Velg side i menyen til venstre.")
