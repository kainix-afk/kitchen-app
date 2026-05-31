import streamlit as st
from utils import ENV, KASTET_TABLE, VARER_TABLE, format_mengde, get_supabase_client, insert_vare, vis_bruk_dette_forst, vis_i_dag_stripe
import uuid
from datetime import datetime, date, timedelta
from html import escape

supabase = get_supabase_client()

KATEGORIER = ["kjøleskap", "fryser", "mat", "ukjent"]
ENHETER = ["", "stk", "pakke", "pose", "g", "kg", "dl", "liter"]

vis_i_dag_stripe()

st.title("🏠 Varer hjemme")

if ENV == "dev":
    st.caption("🛠 Utviklingsmiljø")

st.markdown(
    """
    <style>
    div[data-testid="stButton"] > button {
        min-height: 2.25rem;
        padding: 0.25rem 0.75rem;
    }

    button[kind="primary"] {
        background: #2f8f46;
        border-color: #2f8f46;
        color: white;
    }

    button[kind="primary"]:hover {
        background: #26763a;
        border-color: #26763a;
        color: white;
    }

    button[kind="secondary"] {
        background: #3f4752;
        border-color: #3f4752;
        color: white;
    }

    button[kind="secondary"]:hover {
        background: #303842;
        border-color: #303842;
        color: white;
    }

    div[data-testid="stExpander"] details {
        border-color: #edf0f2;
    }

    div[data-testid="stExpander"] summary {
        color: #68717d;
        font-size: 0.86rem;
        min-height: 2rem;
        padding-bottom: 0.25rem;
        padding-top: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def rydd_legg_til_pa_nytt_state(request_id):
    st.session_state.pop("legg_til_pa_nytt_vare", None)

    if request_id:
        st.session_state.pop(f"vis_legg_til_pa_nytt_dato_{request_id}", None)
        st.session_state.pop(f"legg_til_pa_nytt_holdbar_til_{request_id}", None)


def vare_finnes_hjemme(varenavn):
    response = (
        supabase.table(VARER_TABLE)
        .select("id")
        .eq("status", "aktiv")
        .ilike("navn", varenavn.strip())
        .limit(1)
        .execute()
    )

    return bool(response.data)


def angre_siste_handling():
    handling = st.session_state.get("angre_handling")

    if not handling:
        return

    supabase.table(VARER_TABLE).update({
        "status": "aktiv"
    }).eq("id", handling["vare_id"]).execute()

    kastet_id = handling.get("kastet_id")

    if kastet_id:
        supabase.table(KASTET_TABLE).delete().eq("id", kastet_id).execute()

    rydd_legg_til_pa_nytt_state(handling.get("request_id"))

    if st.session_state.get("inline_slettet_vare", {}).get("id") == handling["vare_id"]:
        del st.session_state.inline_slettet_vare

    if handling["handling"] != "slettet":
        st.session_state.angre_feedback = f"Angret {handling['handling']} for {handling['navn']}."

    del st.session_state.angre_handling
    st.rerun()


if "angre_feedback" in st.session_state:
    st.success(st.session_state.angre_feedback)
    del st.session_state.angre_feedback

if "angre_handling" in st.session_state:
    handling = st.session_state.angre_handling

    if handling["handling"] != "slettet":
        angre_col, tom_col = st.columns([1, 3])

        with angre_col:
            if st.button("Angre", key="angre_siste_handling", use_container_width=True):
                angre_siste_handling()

        with tom_col:
            st.caption(f"Sist handling: {handling['handling']} - {handling['navn'].capitalize()}")


if "spist_feedback" in st.session_state:
    st.success(st.session_state.spist_feedback)
    del st.session_state.spist_feedback

if "lagt_til_pa_nytt_feedback" in st.session_state:
    st.success(st.session_state.lagt_til_pa_nytt_feedback)
    del st.session_state.lagt_til_pa_nytt_feedback

if "dato_endret_feedback" in st.session_state:
    st.success(st.session_state.dato_endret_feedback)
    del st.session_state.dato_endret_feedback

if "vare_endret_feedback" in st.session_state:
    st.success(st.session_state.vare_endret_feedback)
    del st.session_state.vare_endret_feedback

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

    if "angre_handling" in st.session_state:
        if st.button("Angre handling", key="angre_fra_dialog", use_container_width=True):
            angre_siste_handling()

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
            if vare_finnes_hjemme(vare["navn"]):
                st.session_state.lagt_til_pa_nytt_feedback = f"{vare['navn'].capitalize()} finnes allerede hjemme."
            else:
                insert_vare(supabase, {
                    "navn": vare["navn"],
                    "kategori": vare.get("kategori", "ukjent"),
                    "utløpsdato": holdbar_til.isoformat(),
                    "status": "aktiv",
                    "mengde": vare.get("mengde"),
                    "enhet": vare.get("enhet", ""),
                })

                st.session_state.lagt_til_pa_nytt_feedback = f"La til {vare['navn']} på nytt."

            if st.session_state.get("angre_handling", {}).get("request_id") == vare["request_id"]:
                del st.session_state.angre_handling

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

def holdbar_dato(vare):
    raw_holdbar = vare.get("holdbar_til")

    if not raw_holdbar:
        return None

    try:
        return date.fromisoformat(raw_holdbar)
    except (TypeError, ValueError):
        return None


def dager_igjen(vare):
    dato = holdbar_dato(vare)

    if dato is None:
        return None

    return (dato - date.today()).days


def kategori_key(vare):
    kategori = vare.get("kategori", "ukjent")

    if kategori == "kjøleskap":
        return "🥶 Kjøleskap"
    if kategori == "fryser":
        return "🧊 Fryser"
    if kategori == "mat":
        return "🍞 Mat"

    return "❓ Ukjent"


def mengde_til_float(verdi):
    if verdi in (None, ""):
        return 0.0

    try:
        return float(verdi)
    except (TypeError, ValueError):
        return 0.0


def normalisert_enhet(enhet):
    enhet = (enhet or "").strip()

    if enhet.lower() in ("none", "l"):
        return "liter" if enhet.lower() == "l" else ""

    return enhet


def oppdater_vare(vare_id, vare_data):
    supabase.table(VARER_TABLE).update(vare_data).eq("id", vare_id).execute()


# 3. UI
filter_col, sort_col = st.columns([2, 1])

with filter_col:
    filter_valg = st.radio(
        "Vis",
        ["Alle", "Haster", "Utgått"],
        horizontal=True,
        key="varer_hjemme_filter",
    )

with sort_col:
    sortering = st.radio(
        "Sorter etter",
        ["Dato", "Navn"],
        horizontal=True,
        key="varer_hjemme_sortering",
    )

filtrerte_varer = []

for vare in varer:
    dager = dager_igjen(vare)

    if filter_valg == "Haster" and (dager is None or dager > 3):
        continue
    if filter_valg == "Utgått" and (dager is None or dager >= 0):
        continue

    filtrerte_varer.append(vare)

vis_bruk_dette_forst(filtrerte_varer, key_prefix="varer_hjemme")

# 4. GRUPPER
grupper = {
    "🥶 Kjøleskap": [],
    "🧊 Fryser": [],
    "🍞 Mat": [],
    "❓ Ukjent": []
}

for v in filtrerte_varer:
    grupper[kategori_key(v)].append(v)

inline_slettet_vare = st.session_state.get("inline_slettet_vare")

if inline_slettet_vare and st.session_state.get("angre_handling", {}).get("handling") == "slettet":
    grupper[kategori_key(inline_slettet_vare)].append(inline_slettet_vare)

def grunn_og_urgency(dager):
    if dager is None:
        return "Mangler holdbarhetsdato.", "⚪ Ukjent"
    if dager < 0:
        return "Denne er over dato og bør vurderes først.", "🔥 Høy"
    if dager == 0:
        return "Denne går ut i dag.", "🔥 Høy"
    if dager == 1:
        return "Denne har bare 1 dag igjen.", "🟡 Medium"
    if dager <= 3:
        return "Denne bør brukes snart.", "🟡 Medium"

    return "Denne holder en stund til.", "🟢 Lav"


def prioritet_for_dager(dager):
    if dager is None:
        return {
            "badge": "Mangler dato",
            "tone": "Ukjent",
            "bg": "#f7f7f7",
            "border": "#d9d9d9",
            "accent": "#8a8f98",
            "badge_bg": "#eceff3",
            "text": "#2f343a",
            "rank": 3,
        }
    if dager < 0:
        return {
            "badge": "Utløpt",
            "tone": "Haster",
            "bg": "#fff1f0",
            "border": "#ffccc7",
            "accent": "#d4380d",
            "badge_bg": "#ffd8d2",
            "text": "#5c1f12",
            "rank": 0,
        }
    if dager == 0:
        return {
            "badge": "I dag",
            "tone": "Haster",
            "bg": "#fff1f0",
            "border": "#ffccc7",
            "accent": "#d4380d",
            "badge_bg": "#ffd8d2",
            "text": "#5c1f12",
            "rank": 0,
        }
    if dager <= 3:
        return {
            "badge": f"{dager} dag{'er' if dager != 1 else ''}",
            "tone": "Snart",
            "bg": "#fff8e6",
            "border": "#f4d27a",
            "accent": "#d48806",
            "badge_bg": "#ffe9a8",
            "text": "#4a3510",
            "rank": 1,
        }

    return {
        "badge": f"{dager} dager",
        "tone": "Trygg",
        "bg": "#f5f6f7",
        "border": "#d9dee4",
        "accent": "#9aa3ad",
        "badge_bg": "#e9edf1",
        "text": "#30343a",
        "rank": 2,
    }


def vare_sortering(vare):
    navn = vare.get("navn", "").lower()

    if sortering == "Navn":
        return (navn, vare.get("dato_lagt_til", ""))

    dager = dager_igjen(vare)

    if dager is None:
        return (1, 9999, navn)

    return (0, dager, navn)


def kategori_telling(items):
    synlige_varer = [
        vare for vare in items
        if not vare.get("__slettet_placeholder")
    ]
    brukes_snart = 0

    for vare in synlige_varer:
        dager = dager_igjen(vare)

        if dager is not None and dager <= 3:
            brukes_snart += 1

    return len(synlige_varer), brukes_snart


for kategori, items in grupper.items():
    antall_varer, brukes_snart = kategori_telling(items)
    with st.expander(f"{kategori} · {antall_varer} varer", expanded=True):
        st.caption(f"Brukes snart: {brukes_snart}")

        items.sort(key=vare_sortering)

        if not items:
            tomtekster = {
                "🥶 Kjøleskap": "Ingen varer i kjøleskapet ennå. Legg til din første vare 👇",
                "🧊 Fryser": "Ingen varer i fryseren ennå. Legg til noe når du fyller på 👇",
                "🍞 Mat": "Ingen tørrvarer her ennå. Legg til din første vare 👇",
                "❓ Ukjent": "Ingen varer uten kategori akkurat nå.",
            }
            st.info(tomtekster.get(kategori, "Ingen varer her ennå."))
        else:
            for v in items:
                if v.get("__slettet_placeholder"):
                    with st.container(border=True):
                        angre_col, tekst_col = st.columns([1, 3])

                        with angre_col:
                            if st.button("Angre", key=f"angre_slett_{v['id']}", use_container_width=True):
                                angre_siste_handling()

                        with tekst_col:
                            st.write(f"{v['navn'].capitalize()} ble slettet.")

                    st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
                    continue

                raw_dato = v.get("dato_lagt_til")
                raw_holdbar = v.get("holdbar_til")

                if raw_dato:
                    dato_obj = datetime.fromisoformat(raw_dato)
                    dato_formatert = dato_obj.strftime("%d.%m.%Y")
                else:
                    dato_formatert = "ukjent dato"

                holdbar_obj = holdbar_dato(v)

                if holdbar_obj:
                    dager_igjen_verdi = (holdbar_obj - date.today()).days
                    holdbar_formatert = holdbar_obj.strftime("%d.%m.%Y")
                else:
                    dager_igjen_verdi = None
                    holdbar_formatert = "ukjent"

                prioritet = prioritet_for_dager(dager_igjen_verdi)
                grunn, urgency = grunn_og_urgency(dager_igjen_verdi)
                mengde_tekst = format_mengde(v)
                varenavn = escape(v["navn"].capitalize())
                vare_tittel = varenavn

                if mengde_tekst:
                    vare_tittel = f"{varenavn} · {escape(mengde_tekst)}"

                with st.container(border=True):
                    st.markdown(
                        f"""
                        <div style="
                            background: {prioritet['bg']};
                            border-left: 5px solid {prioritet['accent']};
                            border-radius: 7px;
                            color: {prioritet['text']};
                            padding: 7px 9px 6px 9px;
                            margin: -5px 0 6px 0;
                        ">
                            <div style="
                                align-items: center;
                                display: flex;
                                gap: 8px;
                                justify-content: space-between;
                            ">
                                <div style="font-size: 0.98rem; font-weight: 800; line-height: 1.2;">
                                    {vare_tittel}
                                </div>
                                <div style="
                                    background: {prioritet['badge_bg']};
                                    border: 1px solid {prioritet['border']};
                                    border-radius: 999px;
                                    font-size: 0.78rem;
                                    font-weight: 800;
                                    padding: 2px 8px;
                                    white-space: nowrap;
                                ">
                                    {prioritet['badge']}
                                </div>
                            </div>
                            <div style="font-size: 0.83rem; line-height: 1.3; margin-top: 2px;">
                                {prioritet['tone']} · holdbar til {escape(holdbar_formatert)}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.session_state.get("rediger_vare_id") == v["id"]:
                        rediger_kategori = v.get("kategori", "ukjent")

                        if rediger_kategori not in KATEGORIER:
                            rediger_kategori = "ukjent"

                        rediger_enhet = normalisert_enhet(v.get("enhet", ""))
                        enhet_valg = ENHETER if rediger_enhet in ENHETER else ENHETER + [rediger_enhet]

                        with st.form(f"rediger_vare_{v['id']}"):
                            st.markdown("**Rediger vare**")
                            nytt_navn = st.text_input(
                                "Navn",
                                value=v.get("navn", ""),
                                key=f"rediger_navn_{v['id']}",
                            )
                            ny_holdbar_til = st.date_input(
                                "Holdbar til",
                                value=holdbar_obj or date.today() + timedelta(days=7),
                                key=f"rediger_holdbar_til_{v['id']}",
                            )

                            rediger_mengde_col, rediger_enhet_col = st.columns(2)

                            with rediger_mengde_col:
                                ny_mengde = st.number_input(
                                    "Mengde",
                                    min_value=0.0,
                                    step=1.0,
                                    value=mengde_til_float(v.get("mengde")),
                                    key=f"rediger_mengde_{v['id']}",
                                )

                            with rediger_enhet_col:
                                ny_enhet = st.selectbox(
                                    "Enhet",
                                    enhet_valg,
                                    index=enhet_valg.index(rediger_enhet),
                                    key=f"rediger_enhet_{v['id']}",
                                )

                            ny_kategori = st.selectbox(
                                "Kategori",
                                KATEGORIER,
                                index=KATEGORIER.index(rediger_kategori),
                                key=f"rediger_kategori_{v['id']}",
                            )

                            lagre_col, avbryt_col = st.columns(2)

                            with lagre_col:
                                lagre_redigering = st.form_submit_button(
                                    "Lagre endringer",
                                    use_container_width=True,
                                )

                            with avbryt_col:
                                avbryt_redigering = st.form_submit_button(
                                    "Avbryt",
                                    use_container_width=True,
                                )

                        if avbryt_redigering:
                            st.session_state.pop("rediger_vare_id", None)
                            st.rerun()

                        if lagre_redigering:
                            nytt_navn = nytt_navn.strip()

                            if not nytt_navn:
                                st.warning("Navn kan ikke være tomt.")
                                st.stop()

                            vare_data = {
                                "navn": nytt_navn.lower(),
                                "kategori": ny_kategori,
                                "utløpsdato": ny_holdbar_til.isoformat(),
                                "mengde": ny_mengde if ny_mengde > 0 else None,
                                "enhet": ny_enhet if ny_mengde > 0 else "",
                            }
                            oppdater_vare(v["id"], vare_data)
                            st.session_state.vare_endret_feedback = f"Oppdaterte {nytt_navn}."
                            st.session_state.pop("rediger_vare_id", None)
                            st.rerun()

                    brukt_col, kastet_col = st.columns(2)

                    with brukt_col:
                        if st.button("✓ Brukt", key=f"spist_{v['id']}", type="primary", use_container_width=True):
                            request_id = str(uuid.uuid4())

                            supabase.table(VARER_TABLE).update({
                                "status": "spist"
                            }).eq("id", v["id"]).execute()
                            st.session_state.spist_feedback = "Nice 👌 du reddet mat fra å bli kastet"
                            st.session_state.pop("inline_slettet_vare", None)
                            st.session_state.pop("rediger_vare_id", None)
                            st.session_state.angre_handling = {
                                "handling": "spist",
                                "vare_id": v["id"],
                                "navn": v["navn"],
                                "request_id": request_id,
                            }
                            st.session_state.legg_til_pa_nytt_vare = {
                                "navn": v["navn"],
                                "kategori": v.get("kategori", "ukjent"),
                                "mengde": v.get("mengde"),
                                "enhet": v.get("enhet", ""),
                                "request_id": request_id
                            }
                            st.rerun()

                    with kastet_col:
                        if st.button("✕ Kastet", key=f"kastet_{v['id']}", use_container_width=True):
                            request_id = str(uuid.uuid4())
                            kastet_response = supabase.table(KASTET_TABLE).insert({
                                "navn": v["navn"],
                                "kategori": v.get("kategori", "ukjent"),
                                "utløpsdato": v.get("holdbar_til"),
                                "dato_kastet": date.today().isoformat(),
                                "mengde": v.get("mengde"),
                                "enhet": v.get("enhet", "")
                            }).execute()
                            kastet_data = kastet_response.data or []
                            kastet_id = kastet_data[0].get("id") if kastet_data else None

                            supabase.table(VARER_TABLE).update({
                                "status": "kastet"
                            }).eq("id", v["id"]).execute()
                            st.session_state.spist_feedback = f"Markerte {v['navn']} som kastet."
                            st.session_state.pop("inline_slettet_vare", None)
                            st.session_state.pop("rediger_vare_id", None)
                            st.session_state.angre_handling = {
                                "handling": "kastet",
                                "vare_id": v["id"],
                                "navn": v["navn"],
                                "request_id": request_id,
                                "kastet_id": kastet_id,
                            }
                            st.session_state.legg_til_pa_nytt_vare = {
                                "navn": v["navn"],
                                "kategori": v.get("kategori", "ukjent"),
                                "mengde": v.get("mengde"),
                                "enhet": v.get("enhet", ""),
                                "request_id": request_id
                            }

                            st.rerun()

                    if st.checkbox("Detaljer", key=f"detaljer_{v['id']}"):
                        st.write(f"Lagt til: {dato_formatert}")

                        if mengde_tekst:
                            st.write(f"Mengde: {mengde_tekst}")

                        if dager_igjen_verdi is None:
                            st.write("Holdbar til: ukjent")
                        elif dager_igjen_verdi < 0:
                            st.write(f"Holdbar til: {holdbar_formatert} (utgått)")
                        elif dager_igjen_verdi == 0:
                            st.write(f"Holdbar til: {holdbar_formatert} (går ut i dag)")
                        elif dager_igjen_verdi == 1:
                            st.write(f"Holdbar til: {holdbar_formatert} (1 dag igjen)")
                        else:
                            st.write(f"Holdbar til: {holdbar_formatert} ({dager_igjen_verdi} dager igjen)")

                        st.write(f"**Grunn:** {grunn}")
                        st.write(f"**Urgency:** {urgency}")

                        ny_holdbar_til = st.date_input(
                            "Endre holdbarhetsdato",
                            value=holdbar_obj or date.today() + timedelta(days=7),
                            key=f"endre_holdbar_til_{v['id']}_{raw_holdbar or 'ukjent'}"
                        )

                        if st.button("Lagre dato", key=f"lagre_dato_{v['id']}", use_container_width=True):
                            supabase.table(VARER_TABLE).update({
                                "utløpsdato": ny_holdbar_til.isoformat()
                            }).eq("id", v["id"]).execute()

                            st.session_state.dato_endret_feedback = f"Oppdaterte dato for {v['navn']}."
                            st.rerun()

                    tom_col, rediger_col, slett_col = st.columns([2, 1, 1])

                    with rediger_col:
                        if st.button("Rediger", key=f"rediger_{v['id']}", use_container_width=True):
                            st.session_state.rediger_vare_id = v["id"]
                            st.rerun()

                    with slett_col:
                        if st.button("Slett", key=f"slett_{v['id']}", use_container_width=True):
                            supabase.table(VARER_TABLE).update({
                                "status": "slettet"
                            }).eq("id", v["id"]).execute()
                            st.session_state.pop("spist_feedback", None)
                            st.session_state.pop("rediger_vare_id", None)
                            st.session_state.inline_slettet_vare = {
                                **v,
                                "__slettet_placeholder": True,
                            }
                            st.session_state.angre_handling = {
                                "handling": "slettet",
                                "vare_id": v["id"],
                                "navn": v["navn"],
                            }
                            st.rerun()

                st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
