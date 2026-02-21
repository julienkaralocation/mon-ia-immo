import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
from datetime import datetime
import requests
import json

# --- CONFIGURATION ÉPURÉE ---
st.set_page_config(
    page_title="Netly",
    page_icon="https://i.postimg.cc/6qPDSVdQ/apple-touch-icon.png", https://i.postimg.cc/6qPDSVdQ/apple-touch-icon.png
    layout="wide"
)

st.markdown("""
    <head>
        <link rel="apple-touch-icon" href="https://i.postimg.cc/6qPDSVdQ/apple-touch-icon.png">
    </head>
    <style>
    /* Garde ton style Apple ici */
    .stApp { background-color: #ffffff !important; }
    h1, h2, h3, h4, p, span, label, div, .stMetricValue { 
        color: #1d1d1f !important; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    div[data-testid="stMetric"] { 
        background-color: #f5f5f7 !important; 
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #e5e5e7;
    }
    .stButton>button {
        background-color: #0071e3 !important;
        color: white !important;
        border-radius: 12px;
        font-weight: 500;
        border: none;
        height: 3em;
        width: 100%;
    }
    footer {visibility: hidden;}
    .signature {
        text-align: center;
        padding: 20px;
        font-size: 12px;
        color: #86868b !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE IA ---
def analyser_avec_ia(prompt):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        headers = {'Content-Type': 'application/json'}
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        list_res = requests.get(list_url)
        available_models = [m['name'] for m in list_res.json().get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        selected_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/{selected_model}:generateContent?key={api_key}"
        res = requests.post(gen_url, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}]})
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "Analyse indisponible."

# --- INTERFACE ---
st.title("Netly")
st.markdown("##### Analyse d'investissement immobilier")

col1, col2, col3 = st.columns([1, 1, 1.2], gap="large")

with col1:
    st.subheader("Projet")
    nom_projet = st.text_input("Nom", "Appartement T2")
    p_achat = st.number_input("Prix d'achat (€)", value=120000)
    travaux = st.number_input("Travaux (€)", value=15000)
    meubles = st.number_input("Meubles (€)", value=3000)
    frais_agence = st.number_input("Frais d'agence (€)", value=0)
    
    type_immo = st.radio("Notaire", ["Ancien", "Neuf"], horizontal=True)
    tx_notaire = 0.075 if "Ancien" in type_immo else 0.025
    notaire = int(p_achat * tx_notaire)
    
    total_projet = p_achat + travaux + meubles + frais_agence + notaire
    st.caption(f"Coût total : {total_projet:,} €")

with col2:
    st.subheader("Charges & Crédit")
    apport = st.number_input("Apport (€)", value=15000)
    duree = st.select_slider("Années", options=[15, 20, 25], value=20)
    taux = st.slider("Taux (%)", 0.5, 6.0, 3.8)
    
    pret = total_projet - apport
    if pret > 0:
        tm = (taux/100)/12
        mensualite = pret * (tm * (1+tm)**(duree*12)) / ((1+tm)**(duree*12) - 1)
    else: mensualite = 0
    
    st.divider()
    charges_m = st.number_input("Copro (€/mois)", value=80)
    taxe_f = st.number_input("Taxe Foncière (€/an)", value=900)
    frais_fixes_annuels = st.number_input("Gestion & Assurances (€/an)", value=600)
    vacance_p = st.slider("Vacance (%)", 0, 10, 4)

with col3:
    st.subheader("Performance")
    loyer_hc = st.number_input("Loyer mensuel HC (€)", value=750)
    
    revenu_annuel = loyer_hc * 12
    perte_vacance = revenu_annuel * (vacance_p / 100)
    charges_totales = (charges_m * 12) + taxe_f + frais_fixes_annuels + perte_vacance
    
    cash_flow = (revenu_annuel - charges_totales) / 12 - mensualite
    renta_nette = ((revenu_annuel - charges_totales) / total_projet) * 100

    st.metric("Cash-flow Net", f"{int(cash_flow)} €/mois")
    st.metric("Rentabilité Nette", f"{renta_nette:.2f} %")
    
    notes = st.text_area("Observations", placeholder="Locataire en place, état des parties communes...", height=100)

if st.button("LANCER L'AUDIT"):
    with st.spinner("Audit en cours..."):
        prompt = f"Expert. Projet: {total_projet}€. Loyer: {loyer_hc}€. CF: {int(cash_flow)}€. Notes: {notes}. Note/10 et 2 points clés."
        verdict = analyser_avec_ia(prompt)
        st.markdown(f"**Verdict Netly**\n\n{verdict}")

st.markdown('<div class="signature">Propulsé par Netly • Modèle expert Gemini 1.5</div>', unsafe_allow_html=True)
