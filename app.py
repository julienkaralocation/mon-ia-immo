import streamlit as st
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURATION ESTHÉTIQUE ---
st.set_page_config(page_title="ImmoScore IA", page_icon="💎", layout="centered")

# CSS pour un look "Neumorphic / Mobile App"
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {gap: 10px;}
    .stTabs [data-baseweb="tab"] {background-color: #f0f2f6; border-radius: 10px; padding: 10px 20px;}
    .stTabs [aria-selected="true"] {background-color: #007BFF !important; color: white !important;}
    div[data-testid="stExpander"] {border: none; background-color: #f8f9fa; border-radius: 15px; margin-bottom: 10px;}
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION & SIDEBAR (Déplacée en haut pour éviter l'erreur) ---
if 'bibliotheque' not in st.session_state:
    st.session_state.bibliotheque = []

with st.sidebar:
    st.title("⚙️ Paramètres")
    api_key = st.text_input("Clé API Gemini", type="password")
    st.info("La clé API est nécessaire pour l'analyse par l'IA.")

# --- LOGIQUE IA SÉCURISÉE ---
def analyser_bien(key, donnees):
    try:
        genai.configure(api_key=key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""Tu es un investisseur immo impitoyable. Analyse : {donnees}. 
        Donne : 1. Une note sur 10. 2. Un avis tranché sur le cash-flow. 3. Le risque majeur."""
        res = model.generate_content(prompt)
        return res.text
    except Exception as e:
        return f"Erreur IA : {str(e)}"

# --- INTERFACE PRINCIPALE ---
tab1, tab2 = st.tabs(["➕ Nouveau Projet", "📂 Bibliothèque"])

with tab1:
    st.subheader("Calculateur de Rentabilité")
    
    nom_bien = st.text_input("Nom du bien", placeholder="Ex: Studio Lyon 7")
    
    col1, col2 = st.columns(2)
    with col1:
        p_achat = st.number_input("Prix d'achat (€)", value=120000, step=1000)
        travaux = st.number_input("Travaux (€)", value=0, step=500)
    with col2:
        loyer = st.number_input("Loyer mensuel (€)", value=700, step=50)
        charges = st.number_input("Charges/Taxes/mois (€)", value=120, step=10)

    f_notaire = int(p_achat * 0.08)
    mensualite = st.number_input("Mensualité crédit (€)", value=550)
    notes = st.text_area("Notes (état, quartier...)", placeholder="Toiture neuve, quartier calme...")

    total_proj = p_achat + f_notaire + travaux
    cash_flow = loyer - mensualite - charges
    renta_net = ((loyer - charges) * 12 / total_proj) * 100 if total_proj > 0 else 0

    st.divider()
    
    if st.button("🚀 Analyser & Sauvegarder"):
        if not api_key:
            st.error("⚠️ Erreur : Entre ta clé API dans le menu à gauche.")
        else:
            with st.spinner("L'IA réfléchit..."):
                avis_ia = analyser_bien(api_key, {"projet": total_proj, "cashflow": cash_flow, "notes": notes})
                bien = {
                    "id": datetime.now().timestamp(), # ID unique pour supprimer
                    "nom": nom_bien,
                    "date": datetime.now().strftime("%d/%m %H:%M"),
                    "renta": renta_net,
                    "cf": cash_flow,
                    "avis": avis_ia
                }
                st.session_state.bibliotheque.append(bien)
                st.balloons()
                st.markdown(f"### Verdict : \n {avis_ia}")

with tab2:
    st.subheader("Mes analyses enregistrées")
    if not st.session_state.bibliotheque:
        st.write("Aucun bien pour le moment.")
    else:
        for i, b in enumerate(reversed(st.session_state.bibliotheque)):
            with st.expander(f"{b['nom']} - {b['renta']:.1f}% Renta"):
                st.write(f"**Date :** {b['date']}")
                st.write(f"**Cash-flow :** {b['cf']}€/mois")
                st.info(f"**Avis IA :**\n{b['avis']}")
                # Bouton de suppression unique
                if st.button(f"Supprimer {b['nom']}", key=f"del_{b['id']}"):
                    st.session_state.bibliotheque.pop(len(st.session_state.bibliotheque)-1-i)
