import json
import os
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