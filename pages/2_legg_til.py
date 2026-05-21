import streamlit as st
import re
from datetime import date, timedelta
from utils import VARER_TABLE, get_supabase_client, vis_i_dag_stripe

supabase = get_supabase_client()


def hent_varenavn(tekst):
    return [
        navn.strip().lower()
        for navn in re.split(r"[\n,]+", tekst)
        if navn.strip()
    ]


HURTIGVARER = [
    ("🥛", "melk"),
    ("🥚", "egg"),
    ("🧈", "smør"),
    ("🧀", "ost"),
    ("🍞", "brød"),
    ("🥣", "yoghurt"),
    ("🥬", "salat"),
    ("🍅", "tomat"),
    ("🥒", "agurk"),
    ("🥔", "potet"),
    ("🍗", "kylling"),
    ("🍝", "pasta"),
]

DATO_VALG = [
    ("+3 dager", 3),
    ("+7 dager", 7),
    ("+14 dager", 14),
]

KATEGORIER = ["kjøleskap", "fryser", "mat"]


def legg_til_hurtigvare(varenavn, input_key):
    eksisterende_varer = hent_varenavn(st.session_state.get(input_key, ""))

    if varenavn in eksisterende_varer:
        st.session_state[input_key] = "\n".join(
            vare for vare in eksisterende_varer
            if vare != varenavn
        )
        return

    tekst = st.session_state.get(input_key, "").strip()
    st.session_state[input_key] = f"{tekst}\n{varenavn}" if tekst else varenavn


def sett_holdbarhetsdato(dager, input_key):
    valgt_dato = st.session_state.get(input_key, date.today())
    st.session_state[input_key] = valgt_dato + timedelta(days=dager)


vis_i_dag_stripe()

st.title("➕ Legg til varer")

st.markdown(
    """
    <style>
    button[kind="primary"] {
        background: #e8f5ec;
        border-color: #4d9b63;
        color: #1f5d31;
        font-weight: 700;
    }

    button[kind="primary"]:hover {
        background: #d8eedf;
        border-color: #3f8753;
        color: #184b28;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "legg_til_feedback" in st.session_state:
    st.success(st.session_state.legg_til_feedback)
    del st.session_state.legg_til_feedback

if "legg_til_info" in st.session_state:
    st.info(st.session_state.legg_til_info)
    del st.session_state.legg_til_info

if "varer_input_nummer" not in st.session_state:
    st.session_state.varer_input_nummer = 0

if "sist_valgt_kategori" not in st.session_state:
    st.session_state.sist_valgt_kategori = "kjøleskap"

varer_input_key = f"varer_input_{st.session_state.varer_input_nummer}"
holdbar_til_key = "holdbar_til_valg"

if varer_input_key not in st.session_state:
    st.session_state[varer_input_key] = ""

if holdbar_til_key not in st.session_state:
    st.session_state[holdbar_til_key] = date.today() + timedelta(days=7)

if "kategori_valg" not in st.session_state:
    st.session_state.kategori_valg = st.session_state.sist_valgt_kategori

st.subheader("Hurtigvalg")

valgte_hurtigvarer = set(hent_varenavn(st.session_state.get(varer_input_key, "")))
hurtig_cols = st.columns(3)

for index, (ikon, varenavn) in enumerate(HURTIGVARER):
    valgt = varenavn in valgte_hurtigvarer
    label = f"✓ {ikon} {varenavn.capitalize()}" if valgt else f"{ikon} {varenavn.capitalize()}"

    with hurtig_cols[index % len(hurtig_cols)]:
        st.button(
            label,
            key=f"hurtigvare_{varenavn}",
            on_click=legg_til_hurtigvare,
            args=(varenavn, varer_input_key),
            type="primary" if valgt else "secondary",
            use_container_width=True,
        )

navn_tekst = st.text_area(
    "Varer",
    placeholder="egg\nmelk\npaprika",
    help="Skriv én vare per linje, eller skill med komma.",
    key=varer_input_key
)

st.subheader("Holdbarhet")

dato_cols = st.columns(3)

for index, (label, dager) in enumerate(DATO_VALG):
    with dato_cols[index]:
        st.button(
            label,
            key=f"dato_{dager}_dager",
            on_click=sett_holdbarhetsdato,
            args=(dager, holdbar_til_key),
            use_container_width=True,
        )

holdbar_til = st.date_input(
    "Holdbar til",
    key=holdbar_til_key
)

kategori = st.selectbox(
    "Kategori",
    KATEGORIER,
    key="kategori_valg"
)

if st.button("Legg til varer"):

    nye_varenavn = hent_varenavn(navn_tekst)

    if not nye_varenavn:
        st.warning("Skriv inn minst én vare først 😄")
        st.stop()

    lagt_til = []
    hoppet_over = []
    sett_i_input = set()

    for ny_vare in nye_varenavn:
        if ny_vare in sett_i_input:
            hoppet_over.append(ny_vare)
            continue

        sett_i_input.add(ny_vare)
        lagt_til.append(ny_vare)

        supabase.table(VARER_TABLE).insert({
            "navn": ny_vare,
            "kategori": kategori,
            "utløpsdato": holdbar_til.isoformat(),
            "status": "aktiv"
        }).execute()

    if lagt_til:
        st.session_state.legg_til_feedback = f"La til {len(lagt_til)} varer."
        st.session_state.sist_valgt_kategori = kategori
        st.session_state.varer_input_nummer += 1

        if hoppet_over:
            st.session_state.legg_til_info = f"Hoppet over duplikater i input: {', '.join(hoppet_over)}"

        st.rerun()
    else:
        st.warning("Ingen varer ble lagt til 😄")
