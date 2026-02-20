import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="IA Immo Pro", layout="wide")
st.title("🏠 IA Investisseur Pro : Analyse & Rapport")

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Clé API Gemini :", type="password")

# --- FORMULAIRE ---
col_in, col_graph = st.columns([1, 1])

with col_in:
    prix_achat = st.number_input("Prix d'achat (€)", value=150000)
    frais_notaire = st.number_input("Frais de notaire (€)", value=int(prix_achat * 0.075))
    travaux = st.number_input("Travaux (€)", value=0)
    loyer = st.number_input("Loyer mensuel HC (€)", value=800)
    charges = st.number_input("Charges + Taxe foncière / mois (€)", value=150)
    
    # Calcul prêt rapide
    apport = st.number_input("Apport (€)", value=20000)
    montant_pret = (prix_achat + frais_notaire + travaux) - apport
    mensualite = st.number_input("Mensualité crédit estimée (€)", value=650)
    notes = st.text_area("Notes sur le bien (emplacement, état...)")

# --- CALCULS & GRAPHIQUE ---
total_projet = prix_achat + frais_notaire + travaux
cash_flow = loyer - mensualite - charges

with col_graph:
    st.subheader("📊 Répartition Mensuelle")
    if loyer > 0:
        # On évite le bénéfice négatif dans le graphique pour la clarté
        benef_graph = max(0, cash_flow)
        labels = ['Crédit', 'Charges/Taxes', 'Cash-Flow Net']
        values = [mensualite, charges, benef_graph]
        
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3, marker_colors=['#EF553B', '#636EFA', '#00CC96'])])
        st.plotly_chart(fig)
    else:
        st.info("Entrez un loyer pour voir le graphique.")

# --- ANALYSE IA ---
analyse_texte = ""
if st.button("🚀 Lancer l'Analyse Expert"):
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Expert immo strict. Analyse : Total {total_projet}€, Loyer {loyer}€, Cashflow {cash_flow}€/mois. Notes : {notes}. Donne un verdict cash et 3 conseils."
        
        res = model.generate_content(prompt)
        analyse_texte = res.text
        st.markdown(analyse_texte)
    else:
        st.error("Clé API manquante.")

# --- EXPORT PDF ---
if analyse_texte:
    def create_pdf(content):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "Rapport d'Investissement Immobilier", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        pdf.cell(200, 10, f"Projet : {total_projet:,} euros", ln=True)
        pdf.cell(200, 10, f"Cash-flow : {cash_flow} euros/mois", ln=True)
        pdf.ln(5)
        pdf.multi_cell(0, 10, f"Analyse de l'IA :\n{content}")
        return pdf.output(dest='S').encode('latin-1', 'replace')

    st.download_button(label="📥 Télécharger le Rapport PDF", data=create_pdf(analyse_texte), file_name="analyse_immo.pdf", mime="application/pdf")
