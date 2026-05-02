import streamlit as st
import re
from datetime import date, timedelta
from utils import hent_varer, lagre_varer, vis_i_dag_stripe
import uuid

def hent_varenavn(tekst):
    return [
        navn.strip().lower()
        for navn in re.split(r"[\n,]+", tekst)
        if navn.strip()
    ]


vis_i_dag_stripe()

st.title("➕ Legg til varer")

if "legg_til_feedback" in st.session_state:
    st.success(st.session_state.legg_til_feedback)
    del st.session_state.legg_til_feedback

if "legg_til_info" in st.session_state:
    st.info(st.session_state.legg_til_info)
    del st.session_state.legg_til_info

if "varer_input_nummer" not in st.session_state:
    st.session_state.varer_input_nummer = 0

navn_tekst = st.text_area(
    "Varer",
    placeholder="egg\nmelk\npaprika",
    help="Skriv én vare per linje, eller skill med komma.",
    key=f"varer_input_{st.session_state.varer_input_nummer}"
)

dato = st.date_input("Når la du den inn?", value=date.today())

holdbar_til = st.date_input(
    "Holdbar til",
    value=date.today() + timedelta(days=7)
)

kategori = st.selectbox(
    "Kategori",
    ["kjøleskap", "fryser", "mat"]
)

if st.button("Legg til varer"):

    nye_varenavn = hent_varenavn(navn_tekst)

    if not nye_varenavn:
        st.warning("Skriv inn minst én vare først 😄")
        st.stop()

    varer = hent_varer()
    eksisterende_navn = {
        v["navn"] if isinstance(v, dict) else v
        for v in varer
    }

    lagt_til = []
    hoppet_over = []
    sett_i_input = set()

    for ny_vare in nye_varenavn:
        if ny_vare in eksisterende_navn or ny_vare in sett_i_input:
            hoppet_over.append(ny_vare)
            continue

        sett_i_input.add(ny_vare)
        lagt_til.append(ny_vare)

        varer.append({
            "id": str(uuid.uuid4()),
            "navn": ny_vare,
            "kategori": kategori,
            "dato_lagt_til": dato.isoformat(),
            "holdbar_til": holdbar_til.isoformat()
        })

    if lagt_til:
        lagre_varer(varer)
        st.session_state.legg_til_feedback = f"La til {len(lagt_til)} varer."
        st.session_state.varer_input_nummer += 1

        if hoppet_over:
            st.session_state.legg_til_info = f"Hoppet over disse fordi de allerede finnes: {', '.join(hoppet_over)}"

        st.rerun()
    else:
        st.warning("Alle varene finnes allerede 😄")
