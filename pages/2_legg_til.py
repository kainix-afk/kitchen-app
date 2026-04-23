import streamlit as st
from utils import hent_varer, lagre_varer
from utils import get_varer_clean, lagre_varer

st.title("➕ Legg til vare")

navn = st.text_input("Vare")

kategori = st.selectbox(
    "Kategori",
    ["kjøleskap", "fryser", "mat"]
)

if st.button("Legg til"):

    if not navn.strip():
        st.warning("Skriv inn en vare først 😄")
        st.stop()

    varer = hent_varer()

    ny_vare = navn.strip().lower()

    eksisterer = any(
        v["navn"] == ny_vare if isinstance(v, dict) else v == ny_vare
        for v in varer
    )

    if eksisterer:
        st.warning("Du har allerede denne varen 😄")
    else:
        varer.append({
            "navn": ny_vare,
            "kategori": kategori
        })

        lagre_varer(varer)
        st.success("Lagt til!")
        st.rerun()