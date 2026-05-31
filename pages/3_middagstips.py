import streamlit as st
import re
from html import escape
from datetime import date
import utils
from utils import VARER_TABLE, format_mengde, get_supabase_client, normalize, get_varer_clean, vis_i_dag_stripe

getattr(utils, "rydd_varer_hjemme_angre_state", lambda: None)()
supabase = get_supabase_client()
vis_i_dag_stripe()

if "middag_brukt_feedback" in st.session_state:
    st.success(st.session_state.middag_brukt_feedback)
    del st.session_state.middag_brukt_feedback

varer = get_varer_clean()

recipes = {
    "Omelett": ["egg", "melk"],
    "Pannekaker": ["egg", "melk", "mel"],
    "Ostesmørbrød": ["brød", "ost"],
    "Eggerøre": ["egg"],
    "Pasta med saus": ["pasta", "tomatsaus"],
    "Tomatsuppe med egg": ["tomatsuppe", "egg"],
    "Pasta carbonara": ["pasta", "egg", "bacon"],
    "Pasta med kjøttdeig": ["pasta", "kjøttdeig", "tomatsaus"],
    "Taco": ["tortilla", "kjøttdeig", "ost"],
    "Quesadilla": ["tortilla", "ost"],
    "Stekt ris": ["ris", "egg"],
    "Ris med kylling": ["ris", "kylling"],
    "Kyllingwok": ["kylling", "grønnsaker"],
    "Wok med ris": ["ris", "grønnsaker"],
    "Fiskepinner med potet": ["fiskepinner", "potet"],
    "Laks med ris": ["laks", "ris"],
    "Potetomelett": ["potet", "egg"],
    "Bakt potet": ["potet", "ost"],
    "Pytt i panne": ["potet", "egg"],
    "Kjøttboller med pasta": ["kjøttboller", "pasta"],
    "Pølser med lompe": ["pølser", "lompe"],
    "Pølser med potetmos": ["pølser", "potetmos"],
    "Grønnsakssuppe": ["grønnsaker", "buljong"],
    "Linsesuppe": ["linser", "tomatsaus"],
    "Chili con carne": ["kjøttdeig", "bønner", "tomatsaus"],
    "Toast med skinke og ost": ["brød", "skinke", "ost"],
    "Tunfisksalat": ["tunfisk", "salat"],
    "Kyllingsalat": ["kylling", "salat"],
    "Havregrøt": ["havregryn", "melk"],
    "Yoghurt med müsli": ["yoghurt", "müsli"],
}

varer_lower = [
    normalize(v["navn"] if isinstance(v, dict) else v)
    for v in varer
]


def ord_i(tekst):
    return re.findall(r"\w+", normalize(tekst))


def vare_matcher(vare_navn, ingrediens):
    ingrediens = normalize(ingrediens)
    vare_navn = normalize(vare_navn)

    return ingrediens == vare_navn or ingrediens in ord_i(vare_navn)


def dager_igjen(vare):
    holdbar_til = vare.get("holdbar_til")

    if not holdbar_til:
        return None

    return (date.fromisoformat(holdbar_til) - date.today()).days


def har_vare(ingrediens):
    return any(
        vare_matcher(vare, ingrediens)
        for vare in varer_lower
    )


def vurder_rett(rett, ingredienser):
    mangler = [
        ingrediens for ingrediens in ingredienser
        if not har_vare(ingrediens)
    ]
    brukte_varer = [
        vare for vare in varer
        if any(vare_matcher(vare["navn"], ingrediens) for ingrediens in ingredienser)
    ]
    varer_som_haster = [
        vare for vare in brukte_varer
        if dager_igjen(vare) is not None and dager_igjen(vare) <= 2
    ]

    kan_lages = len(mangler) == 0
    score = 0

    if kan_lages:
        score += 100

    score += len(brukte_varer) * 10
    score += len(varer_som_haster) * 30
    score -= len(mangler) * 40

    return {
        "rett": rett,
        "ingredienser": ingredienser,
        "mangler": mangler,
        "brukte_varer": brukte_varer,
        "varer_som_haster": varer_som_haster,
        "kan_lages": kan_lages,
        "score": score,
    }


def vare_label(vare):
    navn = vare.get("navn", "").capitalize()
    mengde_tekst = format_mengde(vare)

    if mengde_tekst:
        return f"{navn} · {mengde_tekst}"

    return navn


def unike_varer(varer_liste):
    sett = set()
    unike = []

    for vare in varer_liste:
        vare_id = vare.get("id")

        if not vare_id or vare_id in sett:
            continue

        sett.add(vare_id)
        unike.append(vare)

    return unike


def vis_lag_middag(forslag, key_prefix):
    rett = forslag["rett"]
    brukte_varer = unike_varer(forslag["brukte_varer"])
    bekreft_key = f"middag_bekreft_{key_prefix}"

    if not brukte_varer:
        return

    if st.session_state.get(bekreft_key):
        st.write("Dette vil markere brukte varer som brukt:")
        valgte_varer = []

        for vare in brukte_varer:
            if st.checkbox(
                vare_label(vare),
                value=True,
                key=f"bruk_middag_{key_prefix}_{vare['id']}",
            ):
                valgte_varer.append(vare)

        avbryt_col, bruk_col = st.columns(2)

        with avbryt_col:
            if st.button("Avbryt", key=f"avbryt_middag_{key_prefix}", use_container_width=True):
                st.session_state.pop(bekreft_key, None)
                st.rerun()

        with bruk_col:
            if st.button("Bruk varer", key=f"bruk_middag_{key_prefix}", type="primary", use_container_width=True):
                if not valgte_varer:
                    st.warning("Velg minst én vare først.")
                    st.stop()

                for vare in valgte_varer:
                    supabase.table(VARER_TABLE).update({
                        "status": "spist"
                    }).eq("id", vare["id"]).execute()

                st.session_state.pop(bekreft_key, None)
                st.session_state.middag_brukt_feedback = f"Markerte {len(valgte_varer)} varer som brukt for {rett}."
                st.rerun()
    elif st.button("Lag denne middagen", key=f"lag_middag_{key_prefix}", use_container_width=True):
        st.session_state[bekreft_key] = True
        st.rerun()


# Steg 1: vurder alle rettene mot varene du har hjemme.
forslag = [
    vurder_rett(rett, ingredienser)
    for rett, ingredienser in recipes.items()
]

# Steg 2: del forslagene i "kan lage nå" og "mangler litt".
kan_lage = [
    forslag for forslag in forslag
    if forslag["kan_lages"]
]
nesten = [
    forslag for forslag in forslag
    if len(forslag["mangler"]) == 1
]

# Steg 3: velg dagens beste forslag.
kan_lage.sort(key=lambda forslag: forslag["score"], reverse=True)
nesten.sort(key=lambda forslag: forslag["score"], reverse=True)
dagens_valg = kan_lage[0] if kan_lage else None

if dagens_valg:
    ikon = "🔥" if dagens_valg["varer_som_haster"] else "🍽️"
    begrunnelse = "Bruker varer som snart går ut." if dagens_valg["varer_som_haster"] else "Du har alt du trenger."

    st.markdown(
        f"""
        <div style="
            background: #fff4df;
            border: 1px solid #ffd89a;
            border-radius: 8px;
            padding: 18px 20px;
            margin: 8px 0 18px 0;
            display: flex;
            gap: 14px;
            align-items: center;
        ">
            <div style="font-size: 2.2rem; line-height: 1;">{ikon}</div>
            <div>
                <div style="
                    color: #7a3e00;
                    font-size: 0.9rem;
                    font-weight: 700;
                    margin-bottom: 4px;
                ">Spis i dag</div>
                <div style="
                    color: #1f1f1f;
                    font-size: 1.35rem;
                    font-weight: 800;
                    line-height: 1.2;
                ">{escape(dagens_valg["rett"])}</div>
                <div style="
                    color: #5f4a2a;
                    font-size: 0.98rem;
                    margin-top: 4px;
                ">{begrunnelse}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if dagens_valg["varer_som_haster"]:
        navn = [
            vare["navn"].capitalize()
            for vare in dagens_valg["varer_som_haster"]
        ]
        st.write(f"Bra valg fordi dette bruker varer som snart går ut: {', '.join(navn)}.")

    vis_lag_middag(dagens_valg, "dagens")
else:
    st.markdown(
        """
        <div style="
            background: #f4f7fb;
            border: 1px solid #d7e0ec;
            border-radius: 8px;
            padding: 18px 20px;
            margin: 8px 0 18px 0;
            display: flex;
            gap: 14px;
            align-items: center;
        ">
            <div style="font-size: 2.2rem; line-height: 1;">🍽️</div>
            <div>
                <div style="
                    color: #2c4a67;
                    font-size: 0.9rem;
                    font-weight: 700;
                    margin-bottom: 4px;
                ">Spis i dag</div>
                <div style="
                    color: #1f1f1f;
                    font-size: 1.35rem;
                    font-weight: 800;
                    line-height: 1.2;
                ">Ingen full match ennå</div>
                <div style="
                    color: #40566b;
                    font-size: 0.98rem;
                    margin-top: 4px;
                ">Se forslagene som bare mangler én ingrediens.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.expander("Slik velger appen", expanded=True):
    st.write("1. Sjekker hvilke ingredienser du har hjemme.")
    st.write("2. Finner retter der alle ingrediensene finnes.")
    st.write("3. Gir ekstra poeng hvis retten bruker varer som går ut snart.")
    st.write("4. Hvis ingenting kan lages nå, viser den retter som mangler én ingrediens.")

st.divider()
st.subheader("Alle forslag")

if kan_lage:
    st.success("✅ Kan lage nå")
    for index, forslag in enumerate(kan_lage):
        with st.expander(f"{forslag['rett']} — bruker: {', '.join(forslag['ingredienser'])}", expanded=False):
            st.write("Varer som brukes:")

            for vare in unike_varer(forslag["brukte_varer"]):
                st.write(f"• {vare_label(vare)}")

            vis_lag_middag(forslag, f"liste_{index}")

if nesten:
    st.warning("🟡 Mangler én ingrediens")
    for forslag in nesten:
        st.write(
            f"• {forslag['rett']} (mangler {forslag['mangler'][0]})"
        )

if not kan_lage and not nesten:
    st.write("❌ Ingen forslag for nå.")
