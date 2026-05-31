import streamlit as st
from collections import Counter
from datetime import date, timedelta
import utils
from utils import KASTET_TABLE, format_mengde, get_supabase_client, vis_i_dag_stripe

supabase = get_supabase_client()

getattr(utils, "rydd_varer_hjemme_angre_state", lambda: None)()
vis_i_dag_stripe()

st.title("📊 Kastet-statistikk")

response = supabase.table(KASTET_TABLE).select("*").execute()
kastet = response.data

for k in kastet:
    k["holdbar_til"] = k.get("utløpsdato")


def innenfor_periode(vare, dager):
    dato_kastet = vare.get("dato_kastet")

    if not dato_kastet:
        return False

    grense = date.today() - timedelta(days=dager)
    return date.fromisoformat(dato_kastet) >= grense


def varenavn_med_mengde(vare):
    navn = (vare.get("navn") or "Ukjent").capitalize()
    mengde_tekst = format_mengde(vare)

    if mengde_tekst:
        return f"{navn} · {mengde_tekst}"

    return navn


def vis_kastet_statistikk(varer, tom_tekst):
    if not varer:
        st.write(tom_tekst)
        return

    teller = Counter(varenavn_med_mengde(v) for v in varer)
    st.metric("Kastet", len(varer))

    st.subheader("Mest kastet")
    for navn, antall in teller.most_common(3):
        st.write(f"• {navn} – {antall}")

    with st.expander("Se alle"):
        for navn, antall in teller.most_common():
            if antall == 1:
                st.write(f"• {navn}: kastet 1 gang")
            else:
                st.write(f"• {navn}: kastet {antall} ganger")


if not kastet:
    st.write("Ingen kastede varer ennå 🎉")
else:
    siste_uke = [
        v for v in kastet
        if innenfor_periode(v, 7)
    ]
    siste_maned = [
        v for v in kastet
        if innenfor_periode(v, 30)
    ]

    uke_tab, maned_tab, totalt_tab = st.tabs([
        "Siste uke",
        "Siste måned",
        "Totalt"
    ])

    with uke_tab:
        vis_kastet_statistikk(
            siste_uke,
            "Ingenting kastet siste uke 🎉"
        )

    with maned_tab:
        vis_kastet_statistikk(
            siste_maned,
            "Ingenting kastet siste måned 🎉"
        )

    with totalt_tab:
        vis_kastet_statistikk(
            kastet,
            "Ingen kastede varer ennå 🎉"
        )
