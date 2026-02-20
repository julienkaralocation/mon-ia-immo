import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go

# --- CONFIGURATION STYLE APPLE ---
st.set_page_config(page_title="ImmoScore Ultra", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1d1d1f; }
    .stApp { background-color: #ffffff; }
    
    /* Cartes de métriques épurées */
    div[data-testid="stMetric"] {
        background-color: #f5f5f7;
        border-radius: 20px;
        padding: 20px;
        border: 1px solid #e5e5e7;
    }
    
    /* Bouton type Apple */
    .stButton>button {
        background-color: #0071e3;
        color: white;
        border-radius: 25px;
        padding: 10px 25px;
        border: none;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #0077ed; transform: scale(1.02); }
    
    /* Sidebar et sliders */
    .css-1d391kg { background-color: #f5f5f7; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIQUE IA ROBUSTE ---
def config_ia():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        # On utilise le modèle le plus polyvalent
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return None

# --- INTERFACE ---
st.title("ImmoScore Ultra")
st.markdown("##### L'analyse immobilière haute précision.")

# On sépare en 3 colonnes pour l'aspect "Tableau de Bord"
col_inv, col_fin, col_res = st.columns([1, 1, 1.2], gap="large")

with col_inv:
    st.subheader("🏙️ Le Bien")
    prix_net = st.number_input("Prix Net Vendeur (€)", value=180000, step=5000)
    travaux = st.number_input("Budget Travaux (€)", value=15000)
    frais_agence = st.number_input("Frais d'agence (€)", value=0)
    
    type_achat = st.segmented_control("Régime fiscal", ["Ancien", "Neuf"], default="Ancien")
    tx_notaire = 0.075 if type_achat == "Ancien" else 0.025
    notaire = int(prix_net * tx_notaire)
    st.caption(f"Frais de notaire : {notaire} €")
    
    total_acquisition = prix_net + travaux + frais_agence + notaire

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
    
    # Calculs précis
    revenu_annuel = (loyer_hc * 12) * (1 - (vacance + gestion)/100)
    cash_flow = (revenu_annuel / 12) - mensualite - (taxe_f / 12)
    renta_nette = ((revenu_annuel - taxe_f) / total_acquisition) * 100

    # Affichage Apple Style
    st.metric("Cash-Flow Net", f"{int(cash_flow)} € / mois")
    st.metric("Rentabilité Nette", f"{renta_nette:.2f} %")

# --- GRAPHIQUE ET IA ---
st.divider()
c_graph, c_ia = st.columns([1, 1])

with c_graph:
    fig = go.Figure(data=[go.Pie(labels=['Charges & Prêt', 'Cash-Flow'], 
                                 values=[mensualite + (taxe_f/12), max(0, cash_flow)],
                                 hole=.6, marker_colors=['#f5f5f7', '#0071e3'])])
    fig.update_layout(showlegend=False, height=300, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

with c_ia:
    if st.button("Lancer l'audit intelligent"):
        model = config_ia()
        if model:
            prompt = f"""Expert immo strict. Analyse ce bien : Achat {total_acquisition}€, Loyer {loyer_hc}€, Cashflow {cash_flow}€/mois. 
            Renta {renta_nette}%. Travaux {travaux}€. Sois très critique, donne une note /10 et identifie le risque principal."""
            try:
                with st.spinner("Audit en cours..."):
                    # Technique de secours : on utilise generate_content directement sur le modèle
                    response = model.generate_content(prompt)
                    st.markdown(f"### 🤖 Verdict\n{response.text}")
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")
        else:
            st.error("L'IA n'est pas configurée. Vérifie tes 'Secrets' sur Streamlit.")
