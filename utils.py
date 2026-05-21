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

def format_mengde(vare):
    mengde = vare.get("mengde")
    enhet = (vare.get("enhet") or "").strip()

    if mengde in (None, ""):
        return ""

    try:
        if float(mengde) == 0:
            return ""
    except (TypeError, ValueError):
        pass

    try:
        mengde_tekst = f"{float(mengde):g}"
    except (TypeError, ValueError):
        mengde_tekst = str(mengde).strip()

    return f"{mengde_tekst} {enhet}".strip()


def insert_vare(supabase, vare):
    try:
        return supabase.table(VARER_TABLE).insert(vare).execute(), False
    except Exception as error:
        feiltekst = str(error).lower()
        har_mengdefelt = "mengde" in vare or "enhet" in vare
        mangler_mengdefelt = any(
            tekst in feiltekst
            for tekst in ("mengde", "enhet", "column", "schema cache")
        )

        if har_mengdefelt and mangler_mengdefelt:
            vare_uten_mengde = {
                key: value
                for key, value in vare.items()
                if key not in ("mengde", "enhet")
            }
            return supabase.table(VARER_TABLE).insert(vare_uten_mengde).execute(), True

        raise

def rydd_varer_hjemme_angre_state():
    request_id = None
    angre_handling = st.session_state.get("angre_handling")
    legg_til_pa_nytt_vare = st.session_state.get("legg_til_pa_nytt_vare")

    if angre_handling:
        request_id = angre_handling.get("request_id")

    if not request_id and legg_til_pa_nytt_vare:
        request_id = legg_til_pa_nytt_vare.get("request_id")

    for key in (
        "angre_handling",
        "angre_feedback",
        "inline_slettet_vare",
        "legg_til_pa_nytt_vare",
    ):
        st.session_state.pop(key, None)

    if request_id:
        st.session_state.pop(f"vis_legg_til_pa_nytt_dato_{request_id}", None)
        st.session_state.pop(f"legg_til_pa_nytt_holdbar_til_{request_id}", None)

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
        return "Mangler dato"
    if dager < 0:
        return "Utløpt"
    if dager == 0:
        return "I dag"
    if dager == 1:
        return "I morgen"

    return f"Om {dager} dager"

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
        "dato_kastet": date.today().isoformat(),
        "mengde": vare.get("mengde"),
        "enhet": vare.get("enhet", "")
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

def vis_bruk_dette_forst(varer=None, key_prefix="bruk_forst", maks_antall=5):
    if "bruk_forst_feedback" in st.session_state:
        st.success(st.session_state.bruk_forst_feedback)
        del st.session_state.bruk_forst_feedback

    if varer is None:
        varer = get_varer_clean()

    prioriterte_varer = []

    for vare in varer:
        if vare.get("status") and vare.get("status") != "aktiv":
            continue

        dager = _dager_igjen(vare)

        if dager is not None and dager <= 3:
            prioriterte_varer.append((dager, vare))

    prioriterte_varer.sort(key=lambda item: item[0])
    prioriterte_varer = prioriterte_varer[:maks_antall]

    st.subheader("🔥 Bruk dette først")

    if not prioriterte_varer:
        st.info("Ingen varer som haster akkurat nå. Alt ser rolig ut ✅")
        return

    for dager, vare in prioriterte_varer:
        navn = escape(vare["navn"].capitalize())
        tekst = escape(_holdbar_tekst(dager))

        st.markdown(
            f"""
            <div style="
                align-items: center;
                border-bottom: 1px solid #edf0f2;
                display: flex;
                gap: 12px;
                justify-content: space-between;
                padding: 7px 0;
            ">
                <div style="font-weight: 750; line-height: 1.25;">{navn}</div>
                <div style="
                    color: #5f4a2a;
                    font-size: 0.9rem;
                    font-weight: 750;
                    white-space: nowrap;
                ">{tekst}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
