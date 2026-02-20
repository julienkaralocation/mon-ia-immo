import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import requests
import json

# --- CONFIGURATION STYLE APPLE ---
st.set_page_config(page_title="ImmoScore Ultra V3", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1d1d1f; }
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] { background-color: #f5f5f7; border-radius: 20px; padding: 20px; border: 1px solid #e5e5e7; }
    .stTextArea textarea { border-radius: 15px; border: 1px solid #e5e5e7; background-color: #f5f5f7; }
    .stButton>button { background-color: #0071e3; color: white; border-radius: 25px; padding: 10px 25px; border: none; font-weight: 600; width: 100%; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DONNÉES (Session State par défaut, prêt pour GSheets) ---
if 'bibliotheque' not in st.session_state:
    st.session_state.bibliotheque = []

# --- LOGIQUE IA AUTO-DÉTECTION ---
def analyser_avec_ia(prompt):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        headers = {'Content-Type': 'application/json'}
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        list_res = requests.get(list_url)
        models_data = list_res.json()
        available_models = [m['name'] for m in models_data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        selected_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/{selected_model}:generateContent?key={api_key}"
        res = requests.post(gen_url, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}]})
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "L'IA n'a pas pu répondre. Vérifiez votre clé API."

# --- INTERFACE ---
st.title("ImmoScore Ultra")
tab_calcul, tab_biblio = st.tabs(["💎 Analyseur Pro", "📂 Ma Database"])

with tab_calcul:
    col_inv, col_fin, col_res = st.columns([1, 1, 1.2], gap="large")

    with col_inv:
        st.subheader("🏙️ Le Bien")
        nom_projet = st.text_input("Nom du projet", "Studio Hypercentre")
        prix_net = st.number_input("Prix d'achat (€)", value=150000)
        travaux = st.number_input("Rénovation estimée (€)", value=10000)
        type_achat = st.radio("Régime", ["Ancien", "Neuf"], horizontal=True)
        tx_notaire = 0.075 if type_achat == "Ancien" else 0.025
        total_acquisition = prix_net + travaux + int(prix_net * tx_notaire)
        
        # RÉINTÉGRATION DES NOTES
        notes_investisseur = st.text_area("📝 Notes (Rénovation, locataires, quartier...)", 
                                         placeholder="Ex: Locataire en place depuis 5 ans, toiture à réviser dans 3 ans, excellente sectorisation scolaire...")

    with col_fin:
        st.subheader("🏦 Financement")
        apport = st.slider("Apport (€)", 0, total_acquisition, int(total_acquisition*0.1))
        taux = st.slider("Taux (%)", 0.5, 6.0, 3.8, 0.1)
        duree = st.select_slider("Durée (ans)", options=[15, 20, 25], value=20)
        pret = total_acquisition - apport
        if pret > 0:
            tm = (taux/100)/12
            mensualite = pret * (tm * (1+tm)**(duree*12)) / ((1+tm)**(duree*12) - 1)
        else: mensualite = 0
        st.info(f"Mensualité : {int(mensualite)} €/mois")

    with col_res:
        st.subheader("📈 Performance")
        loyer_hc = st.number_input("Loyer mensuel HC (€)", value=800)
        taxe_f = st.number_input("Taxe foncière (€/an)", value=750)
        cf = (loyer_hc * 0.9) - mensualite - (taxe_f/12) # 10% frais gestion/vacance inclus
        renta = ((loyer_hc * 12) - taxe_f) / total_acquisition * 100
        
        st.metric("Cash-Flow (Net de gestion)", f"{int(cf)} €/mois")
        st.metric("Rentabilité Nette", f"{renta:.2f} %")

    st.divider()
    
    if st.button("🚀 ANALYSER ET ENREGISTRER DANS LA BASE"):
        prompt = f"Expert immo. Analyse : Achat {total_acquisition}€, Loyer {loyer_hc}€, CF {int(cf)}€/mois. Notes de l'investisseur : {notes_investisseur}. Donne une note/10."
        with st.spinner("L'IA étudie le dossier..."):
            verdict = analyser_avec_ia(prompt)
            bien = {
                "id": datetime.now().timestamp(),
                "nom": nom_projet,
                "date": datetime.now().strftime("%d/%m/%Y"),
                "renta": f"{renta:.2f}%",
                "cf": f"{int(cf)}€",
                "notes": notes_investisseur,
                "avis": verdict
            }
            st.session_state.bibliotheque.append(bien)
            st.success("Données sauvegardées !")
            st.markdown(f"### 🤖 Verdict de l'IA\n{verdict}")

with tab_biblio:
    st.subheader("🗄️ Bibliothèque de Biens")
    if not st.session_state.bibliotheque:
        st.info("Aucun bien enregistré.")
    else:
        for b in reversed(st.session_state.bibliotheque):
            with st.expander(f"📍 {b['nom']} - {b['renta']}"):
                st.write(f"**Date :** {b['date']}")
                st.write(f"**Notes investisseur :** {b['notes']}")
                st.info(f"**Analyse IA :** {b['avis']}")
                if st.button(f"🗑️ Supprimer", key=f"del_{b['id']}"):
                    st.session_state.bibliotheque = [x for x in st.session_state.bibliotheque if x['id'] != b['id']]
                    st.rerun()
