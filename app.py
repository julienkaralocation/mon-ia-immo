import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURATION STYLE APPLE ---
st.set_page_config(page_title="ImmoScore Ultra", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1d1d1f; }
    .stApp { background-color: #ffffff; }
    div[data-testid="stMetric"] { background-color: #f5f5f7; border-radius: 20px; padding: 20px; border: 1px solid #e5e5e7; }
    .stButton>button { background-color: #0071e3; color: white; border-radius: 25px; padding: 10px 25px; border: none; font-weight: 600; width: 100%; transition: all 0.3s ease; }
    .stButton>button:hover { background-color: #0077ed; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION MÉMOIRE ---
if 'bibliotheque' not in st.session_state:
    st.session_state.bibliotheque = []

# --- LOGIQUE IA SÉCURISÉE (Correction 404) ---
def config_ia():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        # On force la version stable v1 pour éviter l'erreur v1beta
        genai.configure(api_key=api_key, transport='grpc') 
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

# --- FONCTION PDF ---
def generer_pdf(bien, analyse):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, f"Rapport : {bien['nom']}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Date: {bien['date']}", ln=True)
    pdf.cell(200, 10, f"Rentabilite Nette: {bien['renta']:.2f}%", ln=True)
    pdf.cell(200, 10, f"Cash-Flow: {bien['cf']} euros/mois", ln=True)
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"Analyse de l'expert :\n{analyse}")
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
            mensualite = pret * (tm * (1+tm)**(duree*12)) / ((1+tm)**(duree*12) - 1)
        else: mensualite = 0
        st.info(f"Mensualité : {int(mensualite)} €/mois")

    with col_res:
        st.subheader("📈 Rendement")
        loyer_hc = st.number_input("Loyer mensuel HC (€)", value=950)
        taxe_f = st.number_input("Taxe foncière annuelle (€)", value=900)
        gestion = st.slider("Frais de gestion/Assurance (%)", 0, 15, 7)
        vacance = st.slider("Vacance locative (%)", 0, 10, 3)
        revenu_annuel = (loyer_hc * 12) * (1 - (vacance + gestion)/100)
        cash_flow = (revenu_annuel / 12) - mensualite - (taxe_f / 12)
        renta_nette = ((revenu_annuel - taxe_f) / total_acquisition) * 100
        st.metric("Cash-Flow Net", f"{int(cash_flow)} € / mois")
        st.metric("Rentabilité Nette", f"{renta_nette:.2f} %")

    st.divider()
    
    if st.button("✨ LANCER L'AUDIT & SAUVEGARDER"):
        model = config_ia()
        if model:
            prompt = f"Expert immo strict. Analyse : Achat {total_acquisition}€, Loyer {loyer_hc}€, Cashflow {cash_flow}€/mois. Renta {renta_nette:.2f}%. Sois très critique, donne une note /10 et identifie le risque."
            try:
                with st.spinner("L'IA analyse votre projet..."):
                    response = model.generate_content(prompt)
                    verdict = response.text
                    # Sauvegarde
                    bien = {
                        "id": datetime.now().timestamp(),
                        "nom": nom_projet,
                        "date": datetime.now().strftime("%d/%m/%Y"),
                        "renta": renta_nette,
                        "cf": int(cash_flow),
                        "avis": verdict
                    }
                    st.session_state.bibliotheque.append(bien)
                    st.success("Analyse terminée et ajoutée à la bibliothèque !")
                    st.markdown(f"### 🤖 Verdict\n{verdict}")
                    
                    # Bouton PDF
                    pdf_data = generer_pdf(bien, verdict)
                    st.download_button("📥 Télécharger le Rapport PDF", data=pdf_data, file_name=f"Rapport_{nom_projet}.pdf")
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")
        else:
            st.error("IA non configurée. Vérifiez vos Secrets.")

with tab_biblio:
    st.subheader("Mes Projets Enregistrés")
    if not st.session_state.bibliotheque:
        st.info("La bibliothèque est vide.")
    else:
        for i, b in enumerate(reversed(st.session_state.bibliotheque)):
            with st.expander(f"{b['nom']} - {b['renta']:.2f}% Renta"):
                st.write(f"**Cash-flow :** {b['cf']}€/mois")
                st.write(f"**Analyse :** {b['avis']}")
                if st.button(f"Supprimer {b['nom']}", key=f"del_{b['id']}"):
                    st.session_state.bibliotheque.pop(len(st.session_state.bibliotheque)-1-i)
                    st.rerun()
