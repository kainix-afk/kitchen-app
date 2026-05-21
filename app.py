import streamlit as st
from datetime import date
import utils
from utils import ENV, get_varer_clean, vis_bruk_dette_forst, vis_i_dag_stripe


st.set_page_config(page_title="Kjøkkenappen", page_icon="🍳")

getattr(utils, "rydd_varer_hjemme_angre_state", lambda: None)()
vis_i_dag_stripe()

st.title("🍳 Kjøkkenappen")

if ENV == "dev":
    st.caption("🛠 Utviklingsmiljø")

varer = get_varer_clean()

varer_med_dato = [
    vare
    for vare in varer
    if vare.get("holdbar_til")
]

for vare in varer_med_dato:
    vare["dager_igjen"] = (
        date.fromisoformat(vare["holdbar_til"]) - date.today()
    ).days

varer_med_dato.sort(key=lambda vare: vare["dager_igjen"])
neste_vare = varer_med_dato[0] if varer_med_dato else None
haster = [
    vare
    for vare in varer_med_dato
    if vare["dager_igjen"] <= 3
]

st.subheader("Hva nå?")

if not varer:
    st.write("Legg til varer for å komme i gang.")
else:
    st.write(f"Du har {len(varer)} varer hjemme.")

status_col, neste_col = st.columns(2)

with status_col:
    st.metric("Varer hjemme", len(varer))

with neste_col:
    if neste_vare:
        dager_igjen = neste_vare["dager_igjen"]

        if dager_igjen < 0:
            neste_tekst = f"utløpt for {abs(dager_igjen)} dager siden"
        elif dager_igjen == 0:
            neste_tekst = "går ut i dag"
        elif dager_igjen == 1:
            neste_tekst = "går ut i morgen"
        else:
            neste_tekst = f"om {dager_igjen} dager"

        st.metric(
            "Neste vare",
            neste_vare["navn"].capitalize(),
            neste_tekst
        )
    else:
        st.metric("Neste vare", "Ingen datoer")

if not varer:
    st.page_link("pages/2_legg_til.py", label="Legg til varer", icon="➕")
elif not haster:
    st.success("Ingen varer haster akkurat nå 🎉")
    st.page_link("pages/2_legg_til.py", label="Legg til flere varer", icon="➕")
else:
    st.info(f"{len(haster)} varer bør brukes snart.")
    st.page_link("pages/3_middagstips.py", label="Finn middagstips", icon="🍽️")

st.divider()

vis_bruk_dette_forst(varer, key_prefix="forside")

st.divider()
st.subheader("Snarveier")

link_col1, link_col2, link_col3 = st.columns(3)

with link_col1:
    st.page_link("pages/2_legg_til.py", label="Legg til", icon="➕")

with link_col2:
    st.page_link("pages/1_varer_hjemme.py", label="Varer hjemme", icon="🏠")

with link_col3:
    st.page_link("pages/4_statistikk.py", label="Statistikk", icon="📊")
