import streamlit as st
import google.generativeai as genai

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="IA Investisseur Immo", page_icon="🏠")
st.title("🏠 IA Investisseur : Analyse de Rentabilité")
st.write("Calculez votre cash-flow et obtenez l'avis d'un expert strict.")

# --- BARRE LATÉRALE : TA CLÉ API ---
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Entre ta clé API Gemini :", type="password")
    st.info("Ta clé est utilisée uniquement pour cette session.")

# --- FORMULAIRE D'ENTRÉE DES DONNÉES ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("💰 Achat & Travaux")
    prix_achat = st.number_input("Prix d'achat (€)", min_value=0, value=150000)
    frais_notaire = st.number_input("Frais de notaire (€)", min_value=0, value=int(prix_achat * 0.075))
    travaux = st.number_input("Montant des travaux (€)", min_value=0, value=0)
    
    st.subheader("🏦 Financement")
    apport = st.number_input("Apport personnel (€)", min_value=0, value=20000)
    taux_interet = st.number_input("Taux d'intérêt (%)", min_value=0.0, value=3.8, step=0.1)
    duree_pret = st.number_input("Durée du prêt (années)", min_value=1, value=20)

with col2:
    st.subheader("📈 Exploitation")
    loyer_mensuel = st.number_input("Loyer mensuel HC (€)", min_value=0, value=800)
    charges_mensuelles = st.number_input("Charges / Taxe foncière (par mois €)", min_value=0, value=150)
    
    st.subheader("📝 Notes de l'utilisateur")
    notes_utilisateur = st.text_area(
        "Détails supplémentaires (Ex: 'Quartier en devenir', 'Locataire en place depuis 5 ans', 'Toiture à refaire')",
        placeholder="Donne plus de contexte à l'IA..."
    )

# --- CALCULS MATHÉMATIQUES ---
montant_total = prix_achat + frais_notaire + travaux
montant_emprunte = montant_total - apport

# Calcul mensualité (formule standard)
if montant_emprunte > 0:
    taux_mensuel = (taux_interet / 100) / 12
    nb_mensualites = duree_pret * 12
    mensualite = montant_emprunte * (taux_mensuel * (1 + taux_mensuel)**nb_mensualites) / ((1 + taux_mensuel)**nb_mensualites - 1)
else:
    mensualite = 0

renta_brute = ((loyer_mensuel * 12) / prix_achat) * 100
renta_nette = (((loyer_mensuel - charges_mensuelles) * 12) / montant_total) * 100
cash_flow = loyer_mensuel - mensualite - charges_mensuelles

# --- AFFICHAGE DES RÉSULTATS ---
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Rentabilité Nette", f"{renta_nette:.2f} %")
c2.metric("Cash-Flow Mensuel", f"{cash_flow:.2f} €", delta=cash_flow)
c3.metric("Coût Total Projet", f"{montant_total:,} €")

# --- INTERVENTION DE L'IA ---
if st.button("🚀 Analyser mon projet avec l'IA"):
    if not api_key:
        st.error("Oups ! Tu as oublié d'entrer ta clé API dans la barre latérale.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Tu es un expert en investissement immobilier extrêmement strict et sincère. 
            Ton critère n°1 est le CASH-FLOW. 
            Voici les chiffres d'un projet :
            - Prix achat : {prix_achat}€
            - Frais notaire : {frais_notaire}€
            - Travaux : {travaux}€
            - Apport : {apport}€
            - Loyer mensuel : {loyer_mensuel}€
            - Charges/Taxes mensuelles : {charges_mensuelles}€
            - Cash-flow net calculé : {cash_flow}€/mois
            - Rentabilité nette : {renta_nette}%

            Notes supplémentaires de l'utilisateur : {notes_utilisateur}

            Ta mission :
            1. Donne un avis détaillé et sans langue de bois sur ce projet. 
            2. Si le cash-flow est faible ou négatif, sois très critique.
            3. Analyse les notes (travaux, locataires) pour identifier des risques ou opportunités cachées.
            4. Donne une note finale de 1 à 10.
            5. Termine par 3 conseils stratégiques pour les futurs biens de cet utilisateur.
            """
            
            with st.spinner("L'expert analyse vos chiffres..."):
                response = model.generate_content(prompt)
                st.subheader("🧐 Analyse de l'Expert IA")
                st.write(response.text)
                
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
