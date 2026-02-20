import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION PRO ---
st.set_page_config(page_title="ImmoInvest AI", page_icon="📈", layout="wide")

# Design CSS Avancé
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); padding: 20px; }
    div[data-testid="stExpander"] { border-radius: 15px; background-color: white; border: none; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
    .stButton>button { border-radius: 12px; background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%); color: white; border: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Récupération de la clé API via les Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ La clé API n'est pas configurée dans les Secrets de l'application.")

# --- MOTEUR DE CALCUL DÉTAILLÉ ---
with st.sidebar:
    st.header("📍 Localisation & Type")
    nom_bien = st.text_input("Nom du projet", "Appartement T3 - Centre")
    ville = st.text_input("Ville", "Bordeaux")
    type_bien = st.selectbox("Type", ["Ancien (7.5% notaire)", "Neuf (2.5% notaire)"])
    notaire_taux = 0.025 if "Neuf" in type_bien else 0.075

st.title("💎 ImmoInvest AI")
st.markdown("##### L'expertise immobilière augmentée par l'intelligence artificielle.")

col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    with st.expander("💰 Coûts d'acquisition", expanded=True):
        prix_net = st.number_input("Prix d'achat net vendeur (€)", value=150000, step=5000)
        frais_agence = st.number_input("Frais d'agence (€)", value=0)
        frais_notaire = int(prix_net * notaire_taux)
        st.caption(f"Frais de notaire estimés : {frais_notaire} €")
        travaux = st.number_input("Budget travaux (€)", value=10000)
        mobilier = st.number_input("Ameublement (€)", value=0)
        total_acquisition = prix_net + frais_agence + frais_notaire + travaux + mobilier
    
    with st.expander("🏦 Financement & Charges", expanded=True):
        apport = st.number_input("Apport personnel (€)", value=20000)
        taux = st.number_input("Taux d'intérêt (%)", value=3.8, format="%.2f")
        duree = st.slider("Durée du prêt (ans)", 5, 25, 20)
        montant_pret = total_acquisition - apport
        
        # Calcul mensualité
        if montant_pret > 0:
            tm = (taux/100)/12
            n = duree * 12
            mensualite = montant_pret * (tm * (1+tm)**n) / ((1+tm)**n - 1)
        else: mensualite = 0
        
        st.info(f"Mensualité estimée : {int(mensualite)} €/mois")
        taxe_fonciere = st.number_input("Taxe foncière annuelle (€)", value=800)
        charges_copro = st.number_input("Charges copro annuelles (€)", value=600)

with col_right:
    with st.expander("📈 Revenus Locatifs", expanded=True):
        loyer_hc = st.number_input("Loyer mensuel HC (€)", value=850)
        vacance = st.slider("Vacance locative (%)", 0, 10, 5)
        loyer_annuel_net = (loyer_hc * 12) * (1 - vacance/100)
    
    # CALCULS FINAUX
    charges_annuelles = taxe_fonciere + charges_copro
    cash_flow_mensuel = (loyer_annuel_net / 12) - mensualite - (charges_annuelles / 12)
    renta_nette = ((loyer_annuel_net - charges_annuelles) / total_acquisition) * 100

    # AFFICHAGE DASHBOARD
    st.subheader("Bilan Financier")
    c1, c2 = st.columns(2)
    c1.metric("Cash-Flow Mensuel", f"{int(cash_flow_mensuel)} €", delta=f"{int(cash_flow_mensuel)} €")
    c2.metric("Rentabilité Nette", f"{renta_nette:.2f} %")

    # GRAPHIQUE
    labels = ['Crédit', 'Charges/Impôts', 'Cash-Flow']
    v_cf = max(0, cash_flow_mensuel)
    fig = go.Figure(data=[go.Pie(labels=labels, values=[mensualite, charges_annuelles/12, v_cf], hole=.4)])
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
    st.plotly_chart(fig, use_container_width=True)

# --- ANALYSE IA ---
if st.button("✨ GÉNÉRER L'ANALYSE EXPERT"):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""Analyse ce projet à {ville}:
        Achat: {total_acquisition}€, Loyer: {loyer_hc}€, Cashflow: {cash_flow_mensuel}€/mois. 
        Renta: {renta_nette}%. Travaux: {travaux}€. Notes: {nom_bien}.
        Sois très strict. Donne une note /10 et analyse si le projet est viable ou dangereux."""
        
        with st.spinner("L'IA analyse le marché..."):
            response = model.generate_content(prompt)
            st.markdown("### 🤖 Verdict de l'IA")
            st.write(response.text)
    except Exception as e:
        st.error(f"L'analyse a échoué. Vérifiez votre configuration. ({e})")
