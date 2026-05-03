from datetime import date
from html import escape
import streamlit as st
from supabase import create_client

url = "https://olzqkoagqplbmrfbhyva.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9senFrb2FncXBsYm1yZmJoeXZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc3NjA0ODYsImV4cCI6MjA5MzMzNjQ4Nn0.lTXQq93svaY-hJzl3BT7dXh7gJKPBrxQTsChfx84xSI"
supabase = create_client(url, key)

def normalize(text):
    return text.strip().lower()

def get_varer_clean():
    response = supabase.table("varer").select("*").eq("status", "aktiv").execute()
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
