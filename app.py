import streamlit as st
import json
import os

def normalize(text):
    return text.strip().lower()

st.title("🏠 Kjøkkenappen")

FIL = "varer.json"

# last inn varer fra fil
def last_varer():
    if os.path.exists(FIL):
        with open(FIL, "r") as f:
            return json.load(f)
    return ["Melk", "Egg", "Ost"]

# lagre varer til fil
def lagre_varer(varer):
    with open(FIL, "w") as f:
        json.dump(varer, f)

if "varer" not in st.session_state:
    st.session_state.varer = last_varer()

st.subheader("Varer hjemme")

for vare in st.session_state.varer:
    st.write("•", vare.capitalize())

st.divider()

col1, col2 = st.columns(2)

st.text_input("Legg til vare", key="ny_vare")

with col1:
    if st.button("Legg til"):
        if st.session_state.ny_vare:
            ren = st.session_state.ny_vare.strip().lower()

            if normalize(ren) not in [normalize(v) for v in st.session_state.varer]:
                st.session_state.varer.append(ren)

            lagre_varer(st.session_state.varer)

            st.rerun()
            

with col2:
    if st.button("Nullstill liste"):
        st.session_state.varer = []
        lagre_varer([])
        st.rerun()

st.divider()
st.subheader("🍽️ Middag-forslag")

recipes = {
    "Omelett": ["egg", "melk"],
    "Pannekaker": ["egg", "melk"],
    "Ostesmørbrød": ["brød", "ost"],
    "Eggerøre": ["egg"],
    "Pasta med saus": ["pasta", "tomatsaus"]
}

kan_lage = []
nesten = []

varer_lower = [normalize(v) for v in st.session_state.varer]

for rett, ingredienser in recipes.items():
    mangler = []

    for i in ingredienser:
        if normalize(i) not in varer_lower:
            mangler.append(i)

    if len(mangler) == 0:
        kan_lage.append(rett)

    elif len(mangler) == 1:
        nesten.append((rett, mangler[0]))
if kan_lage:
    st.success("✅ Kan lage nå")
    for rett in kan_lage:
        st.write("•", rett)
if nesten:
    st.warning("🟡 Mangler én ingrediens")
    for rett, ting in nesten:
        st.write(f"• {rett} (mangler {ting})")
if not kan_lage and not nesten:
    st.write("❌ Ingen forslag for nå.")
