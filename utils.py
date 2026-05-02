import json
import os
from datetime import date
from html import escape
import streamlit as st

FIL = "varer.json"
KASTET_FIL = "kastet.json"

def hent_kastet():
    if not os.path.exists(KASTET_FIL):
        return []

    with open(KASTET_FIL, "r", encoding="utf-8") as fil:
        return json.load(fil)

def lagre_kastet(kastet):
    with open(KASTET_FIL, "w", encoding="utf-8") as fil:
        json.dump(kastet, fil, ensure_ascii=False, indent=2)

def normalize(text):
    return text.strip().lower()

def last_varer():
    if os.path.exists(FIL):
        with open(FIL, "r") as f:
            return json.load(f)
    return []

def lagre_varer(varer):
    st.session_state.varer = varer
    with open(FIL, "w") as f:
        json.dump(varer, f)

def hent_varer():
    if "varer" not in st.session_state:
        st.session_state.varer = last_varer()
    return st.session_state.varer

def get_varer_clean():
    varer = hent_varer()

    import uuid

    clean = []

    for v in varer:
        if isinstance(v, str):
            clean.append({
                "id": str(uuid.uuid4()),
                "navn": v,
                "kategori": "ukjent"
            })
        elif "id" not in v:
            v["id"] = str(uuid.uuid4())
            clean.append(v)
        else:
            clean.append(v)

    return clean   # ❌ IKKE lagre her

def _kort_vareliste(varer, maks_antall=3):
    navn = [
        escape(v["navn"].capitalize())
        for v in varer[:maks_antall]
    ]

    if len(varer) > maks_antall:
        navn.append(f"+{len(varer) - maks_antall}")

    return ", ".join(navn)

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
