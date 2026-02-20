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
            
            # On essaie le nom le plus standard
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Tu es un expert en investissement immobilier extrêmement strict et sincère. 
            Ton critère n°1 est le CASH-FLOW (l'argent qui reste dans la poche chaque mois). 
            
            Voici les chiffres du projet :
            - Montant total investi (Achat + Notaire + Travaux) : {montant_total}€
            - Apport : {apport}€
            - Loyer mensuel : {loyer_mensuel}€
            - Mensualité crédit : {mensualite:.2f}€
            - Charges/Taxes mensuelles : {charges_mensuelles}€
            - CASH-FLOW NET : {cash_flow:.2f}€/mois
            - Rentabilité nette : {renta_nette:.2f}%

            Notes de l'utilisateur (travaux, locataires, emplacement) : {notes_utilisateur}

            Ta mission :
            1. Analyse cash-flow : Est-ce que l'investisseur s'enrichit ou s'appauvrit chaque mois ?
            2. Analyse des risques : Que penses-tu des notes sur les travaux ou les locataires ?
            3. Verdict : Donne une note sur 10 (sois sévère).
            4. Conseils futurs : Donne 3 astuces pour améliorer ce projet ou les prochains.
            """
            
            with st.spinner("L'expert analyse vos chiffres..."):
                # On force l'utilisation de la version stable
                response = model.generate_content(prompt)
                st.subheader("🧐 Analyse de l'Expert IA")
                st.write(response.text)
                
        except Exception as e:
            # Si gemini-1.5-flash échoue encore, on essaie le modèle pro par sécurité
            try:
                model_alt = genai.GenerativeModel('gemini-pro')
                response = model_alt.generate_content(prompt)
                st.subheader("🧐 Analyse de l'Expert IA (Mode Secours)")
                st.write(response.text)
            except:
                st.error(f"Erreur persistante : {e}. Vérifie que ta clé API est bien active sur Google AI Studio.")
