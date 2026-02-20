import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION ESTHÉTIQUE ---
st.set_page_config(page_title="ImmoScore IA", page_icon="💎", layout="centered")

# Style CSS pour arrondir les angles et épurer l'interface
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 10px; height: 3em; background-color: #007BFF; color: white;}
    .reportview-container .main .block-container {padding-top: 2rem;}
    .stMetric {background-color: #f0f2f6; padding: 15px; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

# Initialisation de la bibliothèque en mémoire
if 'bibliotheque' not in st.session_state:
    st.session_state.bibliotheque = []

# --- LOGIQUE IA SÉCURISÉE ---
def analyser_bien(api_key, donnees):
    try:
        genai.configure(api_key=api_key)
        # Auto-détection du modèle disponible
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else models[0]
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""Expert immo strict. Analyse ce bien : {donnees}. 
        Donne une note sur 10, un verdict cash (cash-flow priority) et 2 conseils précis."""
        res = model.generate_content(prompt)
        return res.text
    except Exception as e:
        return f"L'IA n'a pas pu répondre : {str(e)}"

# --- NAVIGATION ---
tab1, tab2 = st.tabs(["🆕 Nouveau Calcul", "📚 Ma Bibliothèque"])

with tab1:
    st.header("Analyse de Bien")
    nom_bien = st.text_input("Nom du projet (ex: T2 centre-ville)", "Mon Investissement")
    
    with st.expander("💰 Chiffres de l'achat", expanded=True):
        p_achat = st.number_input("Prix d'achat (€)", value=100000)
        f_notaire = st.number_input("Frais de notaire (€)", value=int(p_achat * 0.08))
        travaux = st.number_input("Travaux estimés (€)", value=0)
        total_proj = p_achat + f_notaire + travaux

    with st.expander("📈 Revenus & Charges", expanded=True):
        loyer = st.number_input("Loyer mensuel HC (€)", value=600)
        mensualite = st.number_input("Mensualité crédit (€)", value=450)
        charges = st.number_input("Charges + Taxe foncière / mois (€)", value=100)
        notes = st.text_area("Observations (travaux, quartier, locataire...)")

    cash_flow = loyer - mensualite - charges
    renta_net = ((loyer - charges) * 12 / total_proj) * 100 if total_proj > 0 else 0

    # Affichage des scores rapides
    c1, c2 = st.columns(2)
    c1.metric("Cash-Flow", f"{cash_flow} €/mois")
    c2.metric("Renta Nette", f"{renta_net:.2f} %")

    if st.button("🧐 Analyser et Enregistrer"):
        if not api_key:
            st.warning("Veuillez entrer votre clé API dans la barre latérale.")
        else:
            avis_ia = analyser_bien(api_key, {"total": total_proj, "cashflow": cash_flow, "notes": notes})
            # Sauvegarde dans la bibliothèque
            bien = {
                "nom": nom_bien,
                "date": datetime.now().strftime("%d/%m/%Y"),
                "score": renta_net,
                "cashflow": cash_flow,
                "avis": avis_ia
            }
            st.session_state.bibliotheque.append(bien)
            st.success("Bien analysé et ajouté à la bibliothèque !")
            st.markdown(f"### Verdict de l'IA :\n{avis_ia}")

with tab2:
    st.header("Tes Biens Enregistrés")
    if not st.session_state.bibliotheque:
        st.info("Aucun bien enregistré pour le moment.")
    else:
        for b in reversed(st.session_state.bibliotheque):
            with st.container():
                st.markdown(f"""
                ---
                ### {b['nom']} ({b['date']})
                **Note Renta :** {b['score']:.2f}% | **Cash-flow :** {b['cashflow']}€/mois
                """)
                with st.expander("Voir l'analyse détaillée"):
                    st.write(b['avis'])

# Sidebar pour la clé
with st.sidebar:
    st.title("Paramètres")
    api_key = st.text_input("Clé API Gemini", type="password")
