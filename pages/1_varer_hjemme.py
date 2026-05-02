import streamlit as st
from utils import hent_varer, lagre_varer, hent_kastet, lagre_kastet, vis_i_dag_stripe
import uuid
from datetime import datetime, date

vis_i_dag_stripe()

st.title("🏠 Varer hjemme")

if "spist_feedback" in st.session_state:
    st.success(st.session_state.spist_feedback)
    del st.session_state.spist_feedback

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
st.subheader("🍽️ Spis dette først")

varer_med_holdbarhet = [
    v for v in varer
    if v.get("holdbar_til")
]

def dager_igjen(v):
    return (date.fromisoformat(v["holdbar_til"]) - date.today()).days

def grunn_og_urgency(dager):
    if dager is None:
        return "Mangler holdbarhetsdato.", "⚪ Ukjent"
    if dager < 0:
        return "Denne er over dato og bør vurderes først.", "🔥 Høy"
    if dager == 0:
        return "Denne går ut i dag.", "🔥 Høy"
    if dager == 1:
        return "Denne har bare 1 dag igjen.", "🟡 Medium"
    if dager <= 2:
        return "Denne bør brukes snart.", "🟡 Medium"

    return "Denne holder en stund til.", "🟢 Lav"

varer_med_holdbarhet.sort(key=dager_igjen)

topp = varer_med_holdbarhet[:3]

if not topp:
    st.write("Ingen varer med holdbarhetsdato ennå")
else:
    for v in topp:
        dager = dager_igjen(v)

        if dager < 0:
            tekst = f"• {v['navn'].capitalize()} (utgått!) ⚠️"
        elif dager == 0:
            tekst = f"• {v['navn'].capitalize()} (går ut i dag) 🔥"
        elif dager == 1:
            tekst = f"• {v['navn'].capitalize()} (1 dag igjen)"
        else:
            tekst = f"• {v['navn'].capitalize()} ({dager} dager igjen)"

        st.write(tekst)

gamle_varer = [
    v for v in varer
    if v.get("holdbar_til") and dager_igjen(v) <= 2
]

with st.expander("⚠️ Se varer som snart går ut"):
    if not gamle_varer:
        st.write("Ingen varer går ut snart 🎉")
    else:
        gamle_varer.sort(key=dager_igjen)

        for v in gamle_varer:
            dager = dager_igjen(v)

            if dager < 0:
                tekst = f"• {v['navn'].capitalize()} (utgått!) ⚠️"
            elif dager == 0:
                tekst = f"• {v['navn'].capitalize()} (går ut i dag)"
            elif dager == 1:
                tekst = f"• {v['navn'].capitalize()} (1 dag igjen)"
            else:
                tekst = f"• {v['navn'].capitalize()} ({dager} dager igjen)"

            st.write(tekst)

for kategori, items in grupper.items():
    st.subheader(kategori)
    
    items.sort(
        key=lambda v: v.get("dato_lagt_til", ""),
        reverse=True
    )

    if not items:
        st.write("Tomt")
    else:
        for v in items:
            col1, col2 = st.columns([4, 1])

            with col1:
                raw_dato = v.get("dato_lagt_til")
                raw_holdbar = v.get("holdbar_til")

                if raw_dato:
                    dato_obj = datetime.fromisoformat(raw_dato)
                    dato_formatert = dato_obj.strftime("%d.%m.%Y")
                else:
                    dato_formatert = "ukjent dato"

                if raw_holdbar:
                    holdbar_obj = date.fromisoformat(raw_holdbar)
                    dager_igjen_verdi = (holdbar_obj - date.today()).days
                    holdbar_formatert = holdbar_obj.strftime("%d.%m.%Y")
                else:
                    dager_igjen_verdi = None
                    holdbar_formatert = "ukjent"

                tekst = f"• {v['navn'].capitalize()}"

                if dager_igjen_verdi is not None:
                    if dager_igjen_verdi < 0:
                        tekst += " ⚠️"
                    elif dager_igjen_verdi <= 2:
                        tekst += " 🔥"

                label = tekst

                with st.expander(label):
                    if dager_igjen_verdi is None:
                        st.write(f"Lagt til: {dato_formatert}")
                        st.write("Holdbar til: ukjent")
                    elif dager_igjen_verdi < 0:
                        st.write(f"Lagt til: {dato_formatert}")
                        st.write(f"Holdbar til: {holdbar_formatert} (utgått)")
                    elif dager_igjen_verdi == 0:
                        st.write(f"Lagt til: {dato_formatert}")
                        st.write(f"Holdbar til: {holdbar_formatert} (går ut i dag)")
                    elif dager_igjen_verdi == 1:
                        st.write(f"Lagt til: {dato_formatert}")
                        st.write(f"Holdbar til: {holdbar_formatert} (1 dag igjen)")
                    else:
                        st.write(f"Lagt til: {dato_formatert}")
                        st.write(f"Holdbar til: {holdbar_formatert} ({dager_igjen_verdi} dager igjen)")

                    grunn, urgency = grunn_og_urgency(dager_igjen_verdi)
                    st.write(f"**Grunn:** {grunn}")
                    st.write(f"**Urgency:** {urgency}")

                    spist_col, kastet_col = st.columns(2)

                    with spist_col:
                        if st.button("✅ Spist", key=f"spist_{v['id']}"):
                            varer = [item for item in varer if item["id"] != v["id"]]
                            lagre_varer(varer)
                            st.session_state.spist_feedback = "Nice 👌 du reddet mat fra å bli kastet"
                            st.rerun()

                    with kastet_col:
                        if st.button("❌ Kastet", key=f"kastet_{v['id']}"):
                            kastet = hent_kastet()

                            kastet.append({
                                "navn": v["navn"],
                                "kategori": v.get("kategori", "ukjent"),
                                "dato_kastet": date.today().isoformat(),
                                "holdbar_til": v.get("holdbar_til")
                            })

                            lagre_kastet(kastet)

                            varer = [item for item in varer if item["id"] != v["id"]]
                            lagre_varer(varer)

                            st.rerun()

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
