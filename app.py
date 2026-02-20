import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import requests
import json
import gspread

# --- FORCER LE MODE CLAIR ET COULEURS LISIBLES ---
st.set_page_config(page_title="ImmoScore Ultra", layout="wide")

st.markdown("""
    <style>
    /* Force le texte en noir et fond blanc pour mobile */
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, h4, span, label { 
        color: #1d1d1f !important; 
    }
    .stApp { background-color: #ffffff !important; }
    
    /* Input fields plus visibles */
    input, textarea {
        background-color: #f5f5f7 !important;
        color: #1d1d1f !important;
        border: 1px solid #d2d2d7 !important;
    }
    
    /* Bouton Apple Bleu */
    .stButton>button {
        background-color: #0071e3 !important;
        color: white !important;
        border-radius: 20px;
        border: none;
        height: 3.5em;
        font-weight: 600;
    }
    
    /* Cartes de résultats */
    div[data-testid="stMetric"] {
        background-color: #f5f5f7 !important;
        border: 1px solid #e5e5e7 !important;
        border-radius: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION SAUVEGARDE GOOGLE SHEETS ---
def sauvegarder_dans_gsheet(data_dict):
    try:
        # On utilise le lien direct via les secrets
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_url(st.secrets["GSHEET_URL"])
        worksheet = sh.get_worksheet(0)
        # On ajoute la ligne : Nom, Date, Renta, CF, Notes, Avis
        worksheet.append_row([
            data_dict['nom'], data_dict['date'], 
            data_dict['renta'], data_dict['cf'], 
            data_dict['notes'], data_dict['avis']
        ])
        return True
    except Exception as e:
        st.error(f"Erreur Google Sheet : {e}")
        return False

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
    except: return "L'IA est momentanément indisponible."

# --- INTERFACE ---
st.title("💎 ImmoScore Ultra")

col_inv, col_fin, col_res = st.columns([1, 1, 1.2], gap="medium")

with col_inv:
    st.subheader("🏙️ Le Bien")
    nom_projet = st.text_input("Nom du projet", "Appartement T2")
    prix_net = st.number_input("Prix d'achat (€)", value=150000)
    travaux = st.number_input("Travaux (€)", value=10000)
    notes_investisseur = st.text_area("📝 Notes (Locataire, quartier, état...)", placeholder="Détaillez ici...")

with col_fin:
    st.subheader("🏦 Banque")
    apport = st.slider("Apport (€)", 0, prix_net, 15000)
    taux = st.slider("Taux (%)", 1.0, 5.0, 3.5, 0.1)
    duree = st.select_slider("Années", options=[15, 20, 25], value=20)
    # Calcul simplifié mensualité
    total_pret = (prix_net + travaux + (prix_net * 0.08)) - apport
    tm = (taux/100)/12
    mensu = total_pret * (tm * (1+tm)**(duree*12)) / ((1+tm)**(duree*12) - 1) if total_pret > 0 else 0
    st.info(f"Mensualité : {int(mensu)} €")

with col_res:
    st.subheader("📈 Résultat")
    loyer = st.number_input("Loyer mensuel HC (€)", value=850)
    renta = ((loyer * 12) / (prix_net + travaux)) * 100
    cf = loyer - mensu - (loyer * 0.2) # Estimation charges/taxes 20%
    st.metric("Cash-Flow estimé", f"{int(cf)} €/m")
    st.metric("Renta brute", f"{renta:.2f} %")

st.divider()

if st.button("🚀 ANALYSER ET ENREGISTRER"):
    with st.spinner("Analyse et sauvegarde..."):
        prompt = f"Expert immo. Prix {prix_net}€, Loyer {loyer}€. Notes : {notes_investisseur}. Donne une note/10."
        verdict = analyser_avec_ia(prompt)
        
        # Données à sauvegarder
        bien = {
            "nom": nom_projet,
            "date": datetime.now().strftime("%d/%m/%Y"),
            "renta": f"{renta:.2f}%",
            "cf": f"{int(cf)}€",
            "notes": notes_investisseur,
            "avis": verdict
        }
        
        # Tentative de sauvegarde
        if sauvegarder_dans_gsheet(bien):
            st.success("✅ Sauvegardé dans le Google Sheet !")
        
        st.markdown(f"### 🤖 Verdict\n{verdict}")
