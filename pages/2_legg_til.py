import streamlit as st
import re
from datetime import date, timedelta
import utils
from utils import VARER_TABLE, get_supabase_client, get_varer_clean, insert_vare, normalize, vis_i_dag_stripe

supabase = get_supabase_client()

getattr(utils, "rydd_varer_hjemme_angre_state", lambda: None)()


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
ENHETER = ["", "stk", "pakke", "poser", "g", "kg", "dl", "l"]


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


def vare_finnes_hjemme(varenavn):
    response = (
        supabase.table(VARER_TABLE)
        .select("id")
        .eq("status", "aktiv")
        .ilike("navn", varenavn.strip())
        .limit(1)
        .execute()
    )

    return bool(response.data)


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

    .optional-label {
        font-size: 0.78rem;
        font-weight: 500;
        color: #6b7280;
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

st.markdown("### Mengde <span class='optional-label'>(valgfritt)</span>", unsafe_allow_html=True)

mengde_col, enhet_col = st.columns(2)

with mengde_col:
    mengde = st.number_input(
        "Mengde",
        min_value=0.0,
        step=1.0,
        value=1.0
    )

with enhet_col:
    enhet = st.selectbox(
        "Enhet",
        ENHETER
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

    varer_hjemme = {
        normalize(vare["navn"])
        for vare in get_varer_clean()
        if vare.get("navn")
    }
    lagt_til = []
    hoppet_over_input = []
    hoppet_over_hjemme = []
    sett_i_input = set()

    for ny_vare in nye_varenavn:
        normalisert_vare = normalize(ny_vare)

        if normalisert_vare in sett_i_input:
            hoppet_over_input.append(ny_vare)
            continue

        sett_i_input.add(normalisert_vare)

        if normalisert_vare in varer_hjemme or vare_finnes_hjemme(ny_vare):
            hoppet_over_hjemme.append(ny_vare)
            continue

        lagt_til.append(ny_vare)

        vare_data = {
            "navn": ny_vare,
            "kategori": kategori,
            "utløpsdato": holdbar_til.isoformat(),
            "status": "aktiv",
        }

        if enhet:
            vare_data["mengde"] = mengde
            vare_data["enhet"] = enhet

        insert_vare(supabase, vare_data)
        varer_hjemme.add(normalisert_vare)

    info_meldinger = []

    if hoppet_over_input:
        info_meldinger.append(
            f"Hoppet over duplikater i input: {', '.join(hoppet_over_input)}"
        )

    if hoppet_over_hjemme:
        info_meldinger.append(
            f"Finnes allerede hjemme: {', '.join(hoppet_over_hjemme)}"
        )

    if lagt_til:
        st.session_state.legg_til_feedback = f"La til {len(lagt_til)} varer."
        st.session_state.sist_valgt_kategori = kategori
        st.session_state.varer_input_nummer += 1

        if info_meldinger:
            st.session_state.legg_til_info = " | ".join(info_meldinger)

        st.rerun()
    elif info_meldinger:
        st.info("Ingen nye varer ble lagt til. " + " | ".join(info_meldinger))
    else:
        st.warning("Ingen varer ble lagt til 😄")
