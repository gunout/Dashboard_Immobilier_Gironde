# dashboard_bordeaux_simple.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Immobilier Bordeaux - Version Simplifiée",
    page_icon="🏘️",
    layout="wide"
)

st.title("🏘️ Dashboard Immobilier Bordeaux")
st.warning("⚠️ Mode démonstration - Données simulées (l'API DVF n'est pas accessible)")

@st.cache_data
def load_sample_data():
    """Charge des données d'exemple"""
    np.random.seed(42)
    n_transactions = 1500
    
    # Génération de données réalistes
    dates = [datetime.now() - timedelta(days=np.random.randint(0, 730)) for _ in range(n_transactions)]
    
    data = {
        'date_mutation': dates,
        'valeur_fonciere': np.random.lognormal(11.8, 0.7, n_transactions).astype(int),
        'surface_terrain': np.random.choice([50, 75, 100, 120, 150, 200, 300], n_transactions, p=[0.1, 0.2, 0.3, 0.15, 0.15, 0.07, 0.03]),
        'type_local': np.random.choice(['Maison', 'Appartement'], n_transactions, p=[0.4, 0.6]),
        'code_postal': np.random.choice(['33000', '33100', '33200', '33300', '33800'], n_transactions),
        'nom_commune': np.random.choice(['BORDEAUX', 'TALENCE', 'PESSAC', 'MERIGNAC', 'CENON'], n_transactions),
        'nombre_pieces': np.random.choice([1, 2, 3, 4, 5], n_transactions, p=[0.1, 0.3, 0.4, 0.15, 0.05])
    }
    
    df = pd.DataFrame(data)
    df['prix_m2'] = df['valeur_fonciere'] / df['surface_terrain']
    
    # Ajout de tendances réalistes
    df.loc[df['code_postal'] == '33000', 'prix_m2'] *= 1.3  # Bordeaux centre plus cher
    df.loc[df['type_local'] == 'Maison', 'prix_m2'] *= 1.1  # Maisons plus chères
    
    return df

df = load_sample_data()

# Interface simplifiée
st.sidebar.header("Filtres")

# Filtres basiques
type_local = st.sidebar.selectbox("Type de bien", ['Tous', 'Maison', 'Appartement'])
code_postal = st.sidebar.multiselect("Code postal", df['code_postal'].unique(), default=df['code_postal'].unique())

# Application des filtres
df_filtre = df.copy()
if type_local != 'Tous':
    df_filtre = df_filtre[df_filtre['type_local'] == type_local]
df_filtre = df_filtre[df_filtre['code_postal'].isin(code_postal)]

# KPIs
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Prix Moyen / m²", f"{df_filtre['prix_m2'].mean():.0f} €")
with col2:
    st.metric("Transactions", len(df_filtre))
with col3:
    st.metric("Prix Médian", f"{df_filtre['valeur_fonciere'].median():.0f} €")

# Graphiques
col1, col2 = st.columns(2)
with col1:
    st.subheader("Prix au m² par Code Postal")
    fig = px.box(df_filtre, x='code_postal', y='prix_m2')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Répartition des Types de Biens")
    fig = px.pie(df_filtre, names='type_local')
    st.plotly_chart(fig, use_container_width=True)

# Données
st.subheader("Détail des Transactions")
st.dataframe(df_filtre.sort_values('date_mutation', ascending=False).head(50))

st.info("ℹ️ Cette version utilise des données simulées pour la démonstration.")