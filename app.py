import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import requests
import json

# --- CONFIGURATION STYLE APPLE ---
st.set_page_config(page_title="ImmoScore Ultra", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1d1d1f; }
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] { background-color: #f5f5f7; border-radius: 20px; padding: 20px; border: 1px solid #e5e5e7; }
    .stButton>button { background-color: #0071e3; color: white; border-radius: 25px; padding: 10px 25px; border: none; font-weight: 600; width: 100%; transition: all 0.3s ease; height: 3em;}
    .stButton>button:hover { background-color: #0077ed; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION MÉMOIRE ---
if 'bibliotheque' not in st.session_state:
    st.session_state.bibliotheque = []

# --- LOGIQUE IA ULTRA-ROBUSTE (Correction 404 Définitive) ---
def analyser_avec_ia(prompt):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        headers = {'Content-Type': 'application/json'}
        
        # ÉTAPE 1 : On demande à Google la liste des modèles autorisés pour TA clé
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        list_res = requests.get(list_url)
        
        if list_res.status_code != 200:
            return f"Erreur de clé : Google rejette la clé. Vérifie qu'elle est bien active sur AI Studio."
            
        models_data = list_res.json()
        # On cherche un modèle qui accepte la génération de contenu
        available_models = [
            m['name'] for m in models_data.get('models', []) 
            if 'generateContent' in m.get('supportedGenerationMethods', [])
        ]
        
        if not available_models:
            return "Aucun modèle de génération trouvé pour cette clé. Active Gemini 1.5 sur AI Studio."

        # ÉTAPE 2 : On prend le meilleur modèle disponible (souvent le premier de la liste)
        # On essaie de privilégier gemini-1.5-flash s'il est dans la liste
        selected_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
        
        # ÉTAPE 3 : On lance l'analyse
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/{selected_model}:generateContent?key={api_key}"
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        res = requests.post(gen_url, headers=headers, json=data)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Erreur lors de la génération ({res.status_code})."

    except Exception as e:
        return f"Erreur système : {str(e)}"
# --- FONCTION PDF ---
def generer_pdf(bien, analyse):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, f"Rapport : {bien['nom']}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Date: {bien['date']}", ln=True)
    pdf.cell(200, 10, f"Total Investi: {bien['total']:,} euros", ln=True)
    pdf.cell(200, 10, f"Rentabilite Nette: {bien['renta']:.2f}%", ln=True)
    pdf.cell(200, 10, f"Cash-Flow: {bien['cf']} euros/mois", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"Analyse de l'expert :\n{analyse}".encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFACE PRINCIPALE ---
st.title("ImmoScore Ultra")

tab_calcul, tab_biblio = st.tabs(["💎 Analyseur", "📂 Bibliothèque"])

with tab_calcul:
    col_inv, col_fin, col_res = st.columns([1, 1, 1.2], gap="large")

    with col_inv:
        st.subheader("🏙️ Le Bien")
        nom_projet = st.text_input("Nom du projet", "Appartement Lyon")
        prix_net = st.number_input("Prix Net Vendeur (€)", value=180000, step=5000)
        travaux = st.number_input("Budget Travaux (€)", value=15000)
        frais_agence = st.number_input("Frais d'agence (€)", value=0)
        type_achat = st.radio("Régime fiscal", ["Ancien", "Neuf"], horizontal=True)
        tx_notaire = 0.075 if type_achat == "Ancien" else 0.025
        notaire = int(prix_net * tx_notaire)
        total_acquisition = prix_net + travaux + frais_agence + notaire
        st.caption(f"Frais de notaire : {notaire} €")

    with col_fin:
        st.subheader("🏦 Financement")
        apport = st.slider("Apport Personnel (€)", 0, int(total_acquisition), int(total_acquisition*0.1))
        taux = st.slider("Taux d'intérêt (%)", 0.5, 6.0, 3.8, 0.1)
        duree = st.select_slider("Durée du prêt (ans)", options=[10, 15, 20, 25], value=20)
        pret = total_acquisition - apport
        if pret > 0:
            tm = (taux/100)/12
            n = duree * 12
            mensualite = pret * (tm * (1+tm)**n) / ((1+tm)**n - 1)
        else: mensualite = 0
        st.info(f"Mensualité : {int(mensualite)} €/mois")

    with col_res:
        st.subheader("📈 Rendement")
        loyer_hc = st.number_input("Loyer mensuel HC (€)", value=950)
        taxe_f = st.number_input("Taxe foncière annuelle (€)", value=900)
        gestion = st.slider("Gestion/Assurance (%)", 0, 15, 7)
        vacance = st.slider("Vacance (%)", 0, 10, 3)
        revenu_annuel = (loyer_hc * 12) * (1 - (vacance + gestion)/100)
        cash_flow = (revenu_annuel / 12) - mensualite - (taxe_f / 12)
        renta_nette = ((revenu_annuel - taxe_f) / total_acquisition) * 100
        st.metric("Cash-Flow Net", f"{int(cash_flow)} € / mois")
        st.metric("Rentabilité Nette", f"{renta_nette:.2f} %")

    st.divider()
    
    if st.button("✨ LANCER L'AUDIT & SAUVEGARDER"):
        prompt = f"Expert immo strict. Analyse : Achat {total_acquisition}€, Loyer {loyer_hc}€, Cashflow {cash_flow}€/mois. Renta {renta_nette:.2f}%. Sois très critique, donne une note /10 et identifie le risque."
        with st.spinner("L'IA analyse votre projet..."):
            verdict = analyser_avec_ia(prompt)
            if "Erreur" in verdict:
                st.error(verdict)
            else:
                bien = {
                    "id": datetime.now().timestamp(),
                    "nom": nom_projet,
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "total": total_acquisition,
                    "renta": renta_nette,
                    "cf": int(cash_flow),
                    "avis": verdict
                }
                st.session_state.bibliotheque.append(bien)
                st.success("Analyse terminée !")
                st.markdown(f"### 🤖 Verdict\n{verdict}")
                
                pdf_data = generer_pdf(bien, verdict)
                st.download_button("📥 Télécharger le Rapport PDF", data=pdf_data, file_name=f"Rapport_{nom_projet}.pdf")

with tab_biblio:
    st.subheader("Mes Projets Enregistrés")
    if not st.session_state.bibliotheque:
        st.info("La bibliothèque est vide.")
    else:
        for i, b in enumerate(reversed(st.session_state.bibliotheque)):
            with st.expander(f"{b['nom']} - {b['renta']:.2f}% Renta"):
                st.write(f"**Date :** {b['date']} | **Investissement :** {b['total']:,} €")
                st.write(f"**Cash-flow :** {b['cf']} €/mois")
                st.info(f"**Analyse :**\n{b['avis']}")
                if st.button(f"Supprimer {b['nom']}", key=f"del_{b['id']}"):
                    st.session_state.bibliotheque.pop(len(st.session_state.bibliotheque)-1-i)
                    st.rerun()
