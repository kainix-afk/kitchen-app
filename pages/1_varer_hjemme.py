import streamlit as st
from utils import hent_varer, lagre_varer
import uuid

st.title("🏠 Varer hjemme")

# 1. HENT DATA
varer = hent_varer()

# 2. NORMALISER (men IKKE lagre her!)
normaliserte = []

for v in varer:

    if isinstance(v, str):
        normaliserte.append({
            "id": str(uuid.uuid4()),
            "navn": v,
            "kategori": "ukjent"
        })

    elif "id" not in v:
        v["id"] = str(uuid.uuid4())
        normaliserte.append(v)

    else:
        normaliserte.append(v)

varer = normaliserte

# 3. STATE
if "valgte_varer" not in st.session_state:
    st.session_state.valgte_varer = set()

def toggle_valg(vare_id):
    if vare_id in st.session_state.valgte_varer:
        st.session_state.valgte_varer.remove(vare_id)
    else:
        st.session_state.valgte_varer.add(vare_id)

# 4. GRUPPER
grupper = {
    "🥶 Kjøleskap": [],
    "🧊 Fryser": [],
    "🍞 Mat": [],
    "❓ Ukjent": []
}

for v in varer:
    kategori = v["kategori"]

    if kategori == "kjøleskap":
        key = "🥶 Kjøleskap"
    elif kategori == "fryser":
        key = "🧊 Fryser"
    elif kategori == "mat":
        key = "🍞 Mat"
    else:
        key = "❓ Ukjent"

    grupper[key].append(v)

# 5. UI
for kategori, items in grupper.items():
    st.subheader(kategori)

    if not items:
        st.write("Tomt")
    else:
        for v in items:

            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"• {v['navn'].capitalize()}")

            with col2:
                checked = v["id"] in st.session_state.valgte_varer

                st.checkbox(
                    "",
                    value=checked,
                    key=f"cb_{v['id']}",
                    on_change=toggle_valg,
                    args=(v["id"],)
                )

# 6. DELETE
st.divider()

if st.button("🗑️ Slett valgte"):

    varer = [v for v in varer if v["id"] not in st.session_state.valgte_varer]

    lagre_varer(varer)

    st.session_state.valgte_varer = set()

    st.rerun()