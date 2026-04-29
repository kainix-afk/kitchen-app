)import streamlit as st
from datetime import date, timedelta
from utils import hent_varer, lagre_varer
import uuid

st.title("➕ Legg til vare")

navn = st.text_input("Vare")

dato = st.date_input("Når la du den inn?", value=date.today())

holdbar_til = st.date_input(
    "Holdbar til",
    value=date.today() + timedelta(days=7)
)

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
            "id": str(uuid.uuid4()),
            "navn": ny_vare,
            "kategori": kategori,
            "dato_lagt_til": date.today().isoformat(),
            "holdbar_til": holdbar_til.isoformat()
            })

        lagre_varer(varer)
        st.success("Lagt til!")
        st.rerun()