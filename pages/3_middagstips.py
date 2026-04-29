import streamlit as st
from utils import normalize, get_varer_clean

varer = get_varer_clean()

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

varer_lower = [
    normalize(v["navn"] if isinstance(v, dict) else v)
    for v in varer
]

for rett, ingredienser in recipes.items():
    mangler = []

    for i in ingredienser:
        if normalize(i) not in varer_lower:
            mangler.append(i)

    if len(mangler) == 0:
        kan_lage.append((rett, ingredienser))
    elif len(mangler) == 1:
        nesten.append((rett, mangler[0]))

if kan_lage:
    st.success("✅ Kan lage nå")
    for rett, ingredienser in kan_lage:
            st.write(f"• {rett} — bruker: {', '.join(ingredienser)}")

if nesten:
    st.warning("🟡 Mangler én ingrediens")
    for rett, ting in nesten:
        st.write(f"• {rett} (mangler {ting})")

if not kan_lage and not nesten:
    st.write("❌ Ingen forslag for nå.")