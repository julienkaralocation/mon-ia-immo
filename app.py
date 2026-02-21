import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
from datetime import datetime
import requests
import json

# --- FORCER LE MODE CLAIR ET LISIBILITÉ MOBILE ---
st.set_page_config(page_title="ImmoScore Ultra V4", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    h1, h2, h3, h4, p, span, label, div, .stMetricValue { 
        color: #1d1d1f !important; 
    }
    div[data-testid="stMetric"] { 
        background-color: #f5f5f7 !important; 
        border-radius: 15px;
        padding: 15px;
    }
    .stButton>button {
        background-color: #0071e3 !important;
        color: white !important;
        border-radius: 20px;
        font-weight: 600;
        height: 3em;
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
    except: return "L'IA n'est pas disponible pour le moment."

# --- INTERFACE ---
st.title("💎 ImmoScore Ultra")
st.markdown("### Analyse Financière Haute Précision")

col1, col2, col3 = st.columns([1, 1, 1.2], gap="large")

with col1:
    st.subheader("🏙️ Investissement")
    nom_projet = st.text_input("Nom du projet", "T2 Centre Ville")
    p_achat = st.number_input("Prix Net Vendeur (€)", value=120000, step=1000)
    travaux = st.number_input("Budget Travaux (€)", value=15000, step=500)
    meubles = st.number_input("Ameublement (€)", value=3000, step=500)
    frais_agence = st.number_input("Frais d'agence (€)", value=0)
    
    type_immo = st.radio("Frais de notaire", ["Ancien (~7.5%)", "Neuf (~2.5%)"], horizontal=True)
    tx_notaire = 0.075 if "Ancien" in type_immo else 0.025
    notaire = int(p_achat * tx_notaire)
    
    total_projet = p_achat + travaux + meubles + frais_agence + notaire
    st.info(f"**Coût Total : {total_projet:,} €**")

with col2:
    st.subheader("🏦 Financement & Charges")
    apport = st.number_input("Apport Personnel (€)", value=15000)
    duree = st.select_slider("Durée (ans)", options=[15, 20, 25], value=20)
    taux = st.slider("Taux (%)", 0.5, 6.0, 3.8, 0.1)
    
    pret = total_projet - apport
    if pret > 0:
        tm = (taux/100)/12
        mensualite = pret * (tm * (1+tm)**(duree*12)) / ((1+tm)**(duree*12) - 1)
    else: mensualite = 0
    
    st.divider()
    charges_m = st.number_input("Charges Copro mensuelles (€)", value=80)
    taxe_f = st.number_input("Taxe Foncière annuelle (€)", value=900)
    # MODIFICATION : PASSAGE EN MONTANT FIXE ANNUEL
    frais_gestion_annuel = st.number_input("Frais Gestion + Assurances (€/an)", value=600, step=50)
    vacance_p = st.slider("Vacance locative (%)", 0, 10, 4)

with col3:
    st.subheader("📈 Rendement Réel")
    loyer_hc = st.number_input("Loyer Mensuel HC (€)", value=750)
    
    # Calculs précis
    revenu_annuel_theorique = loyer_hc * 12
    perte_vacance = revenu_annuel_theorique * (vacance_p / 100)
    
    # Calcul Cash-flow avec les nouveaux frais fixes
    charges_annuelles_totales = (charges_m * 12) + taxe_f + frais_gestion_annuel + perte_vacance
    cash_flow = (revenu_annuel_theorique - charges_annuelles_totales) / 12 - mensualite
    renta_nette = ((revenu_annuel_theorique - charges_annuelles_totales) / total_projet) * 100

    st.metric("Cash-flow Net", f"{int(cash_flow)} €/mois")
    st.metric("Rentabilité Nette", f"{renta_nette:.2f} %")
    
    notes = st.text_area("📝 Notes de l'expert", placeholder="Ex: État de la copropriété, profil locataire...", height=150)

st.divider()

if st.button("🚀 LANCER L'ANALYSE IA"):
    with st.spinner("Analyse en cours..."):
        prompt = f"""Expert Immobilier. Analyse ce projet :
        - Coût Total : {total_projet}€
        - Loyer HC : {loyer_hc}€/mois
        - Charges (Copro + Taxe F + Gestion/Assurance) : {int(charges_annuelles_totales)}€/an
        - Cashflow : {int(cash_flow)}€/mois
        - Renta Nette : {renta_nette:.2f}%
        - Notes : {notes}
        Donne un verdict tranché, une note sur 10 et les 2 points de vigilance."""
        
        verdict = analyser_avec_ia(prompt)
        st.markdown(f"### 🤖 Verdict de l'IA\n{verdict}")
