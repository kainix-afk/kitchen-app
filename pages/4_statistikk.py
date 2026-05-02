import streamlit as st
from collections import Counter
from utils import hent_kastet, vis_i_dag_stripe

vis_i_dag_stripe()

st.title("📊 Kastet-statistikk")

kastet = hent_kastet()

if not kastet:
    st.write("Ingen kastede varer ennå 🎉")
else:
    navn_liste = [v["navn"] for v in kastet]

    teller = Counter(navn_liste)

    for navn, antall in teller.most_common():
        if antall == 1:
            st.write(f"• {navn.capitalize()}: kastet 1 gang")
        else:
            st.write(f"• {navn.capitalize()}: kastet {antall} ganger")
st.subheader("Mest kastet")

topp = teller.most_common(3)

for navn, antall in topp:
    st.write(f"🥇 {navn.capitalize()} – {antall}")
