import streamlit as st
from utils import ENV, KASTET_TABLE, VARER_TABLE, vis_i_dag_stripe
import uuid
from datetime import datetime, date, timedelta
from supabase import create_client

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

vis_i_dag_stripe()

st.title("🏠 Varer hjemme")

if ENV == "dev":
    st.caption("🛠 Utviklingsmiljø")

if "spist_feedback" in st.session_state:
    st.success(st.session_state.spist_feedback)
    del st.session_state.spist_feedback

if "lagt_til_pa_nytt_feedback" in st.session_state:
    st.success(st.session_state.lagt_til_pa_nytt_feedback)
    del st.session_state.lagt_til_pa_nytt_feedback

if "dato_endret_feedback" in st.session_state:
    st.success(st.session_state.dato_endret_feedback)
    del st.session_state.dato_endret_feedback

# 1. HENT DATA
response = supabase.table(VARER_TABLE).select("*").eq("status", "aktiv").execute()
varer = response.data

for v in varer:
    v["holdbar_til"] = v.get("utløpsdato")
    v["dato_lagt_til"] = v.get("lagt_til")


@st.dialog("Legge til på nytt?")
def vis_legg_til_pa_nytt_dialog():
    vare = st.session_state.get("legg_til_pa_nytt_vare")

    if not vare:
        return

    st.write(f"Vil du legge til **{vare['navn'].capitalize()}** på nytt?")
    vis_dato_key = f"vis_legg_til_pa_nytt_dato_{vare['request_id']}"

    if not st.session_state.get(vis_dato_key):
        ja_col, nei_col = st.columns(2)

        with ja_col:
            if st.button("Ja", key="vis_dato_legg_til_pa_nytt"):
                st.session_state[vis_dato_key] = True
                st.rerun()

        with nei_col:
            if st.button("Nei", key="avbryt_legg_til_pa_nytt"):
                del st.session_state.legg_til_pa_nytt_vare
                st.session_state.pop(vis_dato_key, None)
                st.rerun()

        return

    holdbar_til = st.date_input(
        "Ny holdbarhetsdato",
        value=date.today() + timedelta(days=7),
        key=f"legg_til_pa_nytt_holdbar_til_{vare['request_id']}"
    )

    legg_til_col, avbryt_col = st.columns(2)

    with legg_til_col:
        if st.button("Legg til", key="bekreft_legg_til_pa_nytt"):
            supabase.table(VARER_TABLE).insert({
                "navn": vare["navn"],
                "kategori": vare.get("kategori", "ukjent"),
                "utløpsdato": holdbar_til.isoformat(),
                "status": "aktiv"
            }).execute()

            st.session_state.lagt_til_pa_nytt_feedback = f"La til {vare['navn']} på nytt."
            del st.session_state.legg_til_pa_nytt_vare
            st.session_state.pop(vis_dato_key, None)
            st.rerun()

    with avbryt_col:
        if st.button("Avbryt", key="avbryt_dato_legg_til_pa_nytt"):
            del st.session_state.legg_til_pa_nytt_vare
            st.session_state.pop(vis_dato_key, None)
            st.rerun()


if "legg_til_pa_nytt_vare" in st.session_state:
    vis_legg_til_pa_nytt_dialog()

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
            tekst = f"{v['navn'].capitalize()} (utgått!)"
        elif dager == 0:
            tekst = f"{v['navn'].capitalize()} (går ut i dag)"
        elif dager == 1:
            tekst = f"{v['navn'].capitalize()} (1 dag igjen)"
        else:
            tekst = f"{v['navn'].capitalize()} ({dager} dager igjen)"

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

                    ny_holdbar_til = st.date_input(
                        "Endre holdbarhetsdato",
                        value=holdbar_obj if raw_holdbar else date.today() + timedelta(days=7),
                        key=f"endre_holdbar_til_{v['id']}_{raw_holdbar or 'ukjent'}"
                    )

                    if st.button("Lagre dato", key=f"lagre_dato_{v['id']}"):
                        supabase.table(VARER_TABLE).update({
                            "utløpsdato": ny_holdbar_til.isoformat()
                        }).eq("id", v["id"]).execute()

                        st.session_state.dato_endret_feedback = f"Oppdaterte dato for {v['navn']}."
                        st.rerun()

                    spist_col, kastet_col = st.columns(2)

                    with spist_col:
                        if st.button("✅ Spist", key=f"spist_{v['id']}"):
                            supabase.table(VARER_TABLE).update({
                                "status": "spist"
                            }).eq("id", v["id"]).execute()
                            st.session_state.spist_feedback = "Nice 👌 du reddet mat fra å bli kastet"
                            st.session_state.legg_til_pa_nytt_vare = {
                                "navn": v["navn"],
                                "kategori": v.get("kategori", "ukjent"),
                                "request_id": str(uuid.uuid4())
                            }
                            st.rerun()

                    with kastet_col:
                        if st.button("❌ Kastet", key=f"kastet_{v['id']}"):
                            supabase.table(KASTET_TABLE).insert({
                                "navn": v["navn"],
                                "kategori": v.get("kategori", "ukjent"),
                                "utløpsdato": v.get("holdbar_til"),
                                "dato_kastet": date.today().isoformat()
                            }).execute()

                            supabase.table(VARER_TABLE).update({
                                "status": "kastet"
                            }).eq("id", v["id"]).execute()
                            st.session_state.legg_til_pa_nytt_vare = {
                                "navn": v["navn"],
                                "kategori": v.get("kategori", "ukjent"),
                                "request_id": str(uuid.uuid4())
                            }

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

    for vare_id in st.session_state.valgte_varer:
        supabase.table(VARER_TABLE).update({
            "status": "slettet"
        }).eq("id", vare_id).execute()

    st.session_state.valgte_varer = set()

    st.rerun()
