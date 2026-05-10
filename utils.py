from datetime import date
from html import escape
import streamlit as st
from supabase import create_client

ENV = st.secrets.get("ENV", "live")

if ENV == "dev":
    VARER_TABLE = "varer_dev"
    KASTET_TABLE = "kastet_dev"
else:
    VARER_TABLE = "varer"
    KASTET_TABLE = "kastet"

def normalize(text):
    return text.strip().lower()

@st.cache_resource
def get_supabase_client():
    mangler = [
        navn
        for navn in ("SUPABASE_URL", "SUPABASE_KEY")
        if navn not in st.secrets
    ]

    if mangler:
        st.error(f"Mangler Streamlit secret: {', '.join(mangler)}")
        st.stop()

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)

def get_varer_clean():
    supabase = get_supabase_client()
    response = supabase.table(VARER_TABLE).select("*").eq("status", "aktiv").execute()
    varer = response.data

    for v in varer:
        v["holdbar_til"] = v.get("utløpsdato")
        v["dato_lagt_til"] = v.get("lagt_til")

    return varer

def _kort_vareliste(varer, maks_antall=3):
    navn = [
        escape(v["navn"].capitalize())
        for v in varer[:maks_antall]
    ]

    if len(varer) > maks_antall:
        navn.append(f"+{len(varer) - maks_antall}")

    return ", ".join(navn)

def _dager_igjen(vare):
    holdbar_til = vare.get("holdbar_til") or vare.get("utløpsdato")

    if not holdbar_til:
        return None

    return (date.fromisoformat(holdbar_til) - date.today()).days

def _holdbar_tekst(dager):
    if dager is None:
        return "mangler dato"
    if dager < 0:
        return f"utløpt for {abs(dager)} dager siden"
    if dager == 0:
        return "går ut i dag"
    if dager == 1:
        return "går ut i morgen"

    return f"{dager} dager igjen"

def _registrer_brukt(supabase, vare):
    supabase.table(VARER_TABLE).update({
        "status": "spist"
    }).eq("id", vare["id"]).execute()

    st.session_state.bruk_forst_feedback = f"Markerte {vare['navn']} som brukt."
    st.rerun()

def _registrer_kastet(supabase, vare):
    supabase.table(KASTET_TABLE).insert({
        "navn": vare["navn"],
        "kategori": vare.get("kategori", "ukjent"),
        "utløpsdato": vare.get("holdbar_til") or vare.get("utløpsdato"),
        "dato_kastet": date.today().isoformat()
    }).execute()

    supabase.table(VARER_TABLE).update({
        "status": "kastet"
    }).eq("id", vare["id"]).execute()

    st.session_state.bruk_forst_feedback = f"Markerte {vare['navn']} som kastet."
    st.rerun()

def _lagre_holdbarhetsdato(supabase, vare, ny_dato):
    supabase.table(VARER_TABLE).update({
        "utløpsdato": ny_dato.isoformat()
    }).eq("id", vare["id"]).execute()

    st.session_state.bruk_forst_feedback = f"Oppdaterte dato for {vare['navn']}."
    st.rerun()

def vis_bruk_dette_forst(varer=None, key_prefix="bruk_forst"):
    if "bruk_forst_feedback" in st.session_state:
        st.success(st.session_state.bruk_forst_feedback)
        del st.session_state.bruk_forst_feedback

    if varer is None:
        varer = get_varer_clean()

    prioriterte_varer = []

    for vare in varer:
        dager = _dager_igjen(vare)

        if dager is not None and dager <= 3:
            prioriterte_varer.append((dager, vare))

    prioriterte_varer.sort(key=lambda item: item[0])

    st.subheader("🟠 Bruk dette først")

    if not prioriterte_varer:
        st.write("Ingen varer som haster akkurat nå.")
        return

    supabase = get_supabase_client()

    for dager, vare in prioriterte_varer:
        vare_id = vare.get("id")

        if not vare_id:
            continue

        raw_holdbar = vare.get("holdbar_til") or vare.get("utløpsdato")
        holdbar_til = date.fromisoformat(raw_holdbar)
        label = f"{vare['navn'].capitalize()} - {_holdbar_tekst(dager)}"

        with st.expander(label, expanded=True):
            st.write(f"Holdbar til: {holdbar_til.strftime('%d.%m.%Y')}")

            brukt_col, kastet_col, dato_col = st.columns([1, 1, 2])

            with brukt_col:
                if st.button("✅ Brukt", key=f"{key_prefix}_brukt_{vare_id}"):
                    _registrer_brukt(supabase, vare)

            with kastet_col:
                if st.button("🗑 Kastet", key=f"{key_prefix}_kastet_{vare_id}"):
                    _registrer_kastet(supabase, vare)

            with dato_col:
                ny_dato = st.date_input(
                    "Ny dato",
                    value=holdbar_til,
                    key=f"{key_prefix}_ny_dato_{vare_id}_{raw_holdbar}"
                )

                if st.button("📅 Endre dato", key=f"{key_prefix}_endre_dato_{vare_id}"):
                    _lagre_holdbarhetsdato(supabase, vare, ny_dato)

def vis_i_dag_stripe():
    varer = get_varer_clean()
    i_dag = []
    snart = []

    for v in varer:
        holdbar_til = v.get("holdbar_til")

        if not holdbar_til:
            continue

        dager = (date.fromisoformat(holdbar_til) - date.today()).days

        if dager <= 0:
            i_dag.append(v)
        elif dager == 1:
            snart.append(v)

    deler = []

    if i_dag:
        deler.append(f"🔥 I dag: bruk {_kort_vareliste(i_dag)}")

    if snart:
        deler.append(f"⚠️ Snart: {_kort_vareliste(snart)}")

    if not deler:
        deler.append("✅ I dag: ingenting haster")

    bakgrunn = "#fff4df" if i_dag else "#fffbea" if snart else "#edf8f0"
    kant = "#ffd89a" if i_dag else "#f0dc82" if snart else "#bfe6c8"
    tekstfarge = "#2b2114" if i_dag or snart else "#1f4d2b"

    st.markdown(
        f"""
        <div style="
            background: {bakgrunn};
            border: 1px solid {kant};
            border-radius: 8px;
            color: {tekstfarge};
            font-weight: 700;
            padding: 10px 14px;
            margin: 0 0 14px 0;
            line-height: 1.35;
        ">
            {" · ".join(deler)}
        </div>
        """,
        unsafe_allow_html=True,
    )
