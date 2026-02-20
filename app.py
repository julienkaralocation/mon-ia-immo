import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go

# --- CONFIGURATION UI ---
st.set_page_config(page_title="ImmoInvest Pro", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #1e3a8a; }
    .stButton>button { 
        height: 3.5rem; border-radius: 12px; font-size: 1.1rem; 
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        border: none; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    div[data-testid="stExpander"] { border-radius: 15px; background-color: white !important; border: 1px solid #e5e7eb; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE IA ---
try:
    # On récupère la clé dans les secrets
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.warning("⚠️ Configuration de la clé API manquante dans les Secrets.")

def appel_ia(prompt):
    # Liste de secours des noms de modèles
    noms_modeles = ['models/gemini-1.5-flash-latest', 'gemini-1.5-flash', 'models/gemini-pro']
    for nom in noms_modeles:
        try:
            model = genai.GenerativeModel(nom)
            res = model.generate_content(prompt)
            return res.text
        except:
            continue
    return "Désolé, l'IA est indisponible pour le moment."

# --- INTERFACE ---
st.title("💎 ImmoInvest Pro")
st.caption("L'assistant intelligent pour vos calculs de rentabilité")

# Section Calculs
with st.expander("📍 Détails de l'Achat", expanded=True):
    p_achat = st.number_input("Prix d'achat Net Vendeur (€)", value=120000, step=5000)
    notaire_type = st.radio("Frais de notaire", ["Ancien (~7.5%)", "Neuf (~2.5%)"], horizontal=True)
    tx_notaire = 0.075 if "Ancien" in notaire_type else 0.025
    travaux = st.number_input("Budget Travaux (€)", value=10000)
    
    total_projet = p_achat + (p_achat * tx_notaire) + travaux

with st.expander("📊 Revenus & Charges", expanded=True):
    loyer = st.number_input("Loyer Mensuel HC (€)", value=750)
    mensualite = st.number_input("Mensualité Crédit (€)", value=500)
    charges = st.number_input("Charges + Taxe Foncière / mois (€)", value=120)

# Calculs finaux
cf = loyer - mensualite - charges
renta = ((loyer - charges) * 12 / total_projet) * 100 if total_projet > 0 else 0

# Dashboard Visuel
st.divider()
c1, c2 = st.columns(2)
c1.metric("Cash-flow", f"{cf} €/mois")
c2.metric("Renta Nette", f"{renta:.2f} %")

# Graphique
fig = go.Figure(data=[go.Pie(labels=['Charges/Crédit', 'Bénéfice Net'], 
                             values=[mensualite + charges, max(0, cf)],
                             hole=.5, marker_colors=['#e5e7eb', '#3b82f6'])])
fig.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
st.plotly_chart(fig, use_container_width=True)

# Bouton IA
if st.button("✨ Obtenir l'Analyse de l'IA"):
    prompt_expert = f"Analyse ce bien : Achat {total_projet}€, Loyer {loyer}€, Cashflow {cf}€/mois. Sois très critique et donne une note sur 10."
    with st.spinner("Analyse en cours..."):
        verdict = appel_ia(prompt_expert)
        st.info(f"### 🤖 Verdict de l'Expert\n{verdict}")
