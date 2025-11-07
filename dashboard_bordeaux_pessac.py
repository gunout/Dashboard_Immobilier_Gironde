# dashboard_pessac_final.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import requests
import io
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Immobilier Pessac - Données DVF 2024",
    page_icon="🏘️",
    layout="wide"
)

st.title("🏘️ Dashboard Immobilier Pessac")
st.info("ℹ️ Données réelles DVF 2024 pour la commune de Pessac (INSEE 33555), provenant de data.gouv.fr")

@st.cache_data
def load_pessac_data():
    """
    Charge les données DVF 2024 pour la commune de Pessac (INSEE 33555)
    depuis le fichier CSV direct sur data.gouv.fr.
    Version corrigée pour utiliser les bons noms de colonnes.
    """
    url = "https://files.data.gouv.fr/geo-dvf/latest/csv/2024/communes/33/33555.csv"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text), sep=',', low_memory=False)
        
        if df.empty:
            st.warning("Le fichier de données pour Pessac est vide.")
            return pd.DataFrame()

        # Nettoyage et préparation des données avec les NOUVEAUX noms de colonnes
        # Conversion des dates
        df["date_mutation"] = pd.to_datetime(df["date_mutation"], format='%Y-%m-%d', errors='coerce')
        
        # Conversion de la valeur foncière en numérique
        df["valeur_fonciere"] = pd.to_numeric(df["valeur_fonciere"], errors='coerce')
        
        # Filtrage des types de locaux pertinents
        df = df[df["type_local"].isin(['Maison', 'Appartement'])]
        
        # VÉRIFICATION CRUCIALE : Le DataFrame est-il vide après le filtrage ?
        if df.empty:
            st.warning("Aucune transaction pour 'Maison' ou 'Appartement' n'a été trouvée dans le fichier 2024 pour Pessac.")
            st.info("Le fichier contient peut-être uniquement des ventes de terrains, locaux commerciaux, etc.")
            return pd.DataFrame()

        # Suppression des valeurs manquantes critiques
        df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati", "code_postal", "date_mutation"])
        
        # Conversion de la surface en numérique
        df["surface_reelle_bati"] = pd.to_numeric(df["surface_reelle_bati"], errors='coerce')
        df = df.dropna(subset=["surface_reelle_bati"])

        if df.empty:
            st.warning("Les données sont devenues vides après la conversion de la surface.")
            return pd.DataFrame()

        # Calcul du prix au m²
        df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
        
        # Filtrage des valeurs aberrantes
        df = df[(df['prix_m2'] > 200) & (df['prix_m2'] < 15000)]
        
        if df.empty:
            st.warning("Les données sont devenues vides après le filtrage des prix aberrants.")
            return pd.DataFrame()

        # Le renommage n'est plus nécessaire car on utilise déjà les bons noms
        # df = df.rename(columns({...}))
        
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à data.gouv.fr : {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")
        return pd.DataFrame()

# Chargement des données
df = load_pessac_data()

if df.empty:
    st.warning("Le tableau de bord ne peut pas être affiché car aucune donnée valide n'a été trouvée.")
    st.stop()

# Interface de filtrage
st.sidebar.header("Filtres")
codes_postaux_disponibles = sorted(df['code_postal'].unique())
code_postal_selectionne = st.sidebar.multiselect("Code postal", codes_postaux_disponibles, default=codes_postaux_disponibles)
type_local = st.sidebar.selectbox("Type de bien", ['Tous', 'Maison', 'Appartement'])
prix_min = st.sidebar.number_input("Prix minimum (€)", value=0, step=10000)
prix_max = st.sidebar.number_input("Prix maximum (€)", value=int(df['valeur_fonciere'].max()), step=10000)

# Application des filtres
df_filtre = df[
    (df['code_postal'].isin(code_postal_selectionne)) &
    (df['valeur_fonciere'] >= prix_min) &
    (df['valeur_fonciere'] <= prix_max)
].copy()

if type_local != 'Tous':
    df_filtre = df_filtre[df_filtre['type_local'] == type_local]

if df_filtre.empty:
    st.warning("Aucune transaction ne correspond à vos filtres.")
    st.stop()

# KPIs
st.header("Indicateurs Clés pour Pessac")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Prix Moyen / m²", f"{df_filtre['prix_m2'].mean():.0f} €")
with col2:
    st.metric("Prix Médian", f"{df_filtre['valeur_fonciere'].median():.0f} €")
with col3:
    st.metric("Nombre de Transactions", f"{len(df_filtre):,}")
with col4:
    surface_moyenne = df_filtre['surface_reelle_bati'].mean()
    st.metric("Surface Moyenne", f"{surface_moyenne:.0f} m²")

# Graphiques
st.header("Visualisations pour Pessac")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Répartition des Prix au m²")
    fig = px.histogram(df_filtre, x='prix_m2', nbins=50, color='type_local', marginal="box")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("Répartition des Types de Biens")
    fig = px.pie(df_filtre, names='type_local', title='Répartition par type')
    st.plotly_chart(fig, use_container_width=True)

# Carte des transactions
st.subheader("Carte des Transactions à Pessac")
if 'latitude' in df_filtre.columns and 'longitude' in df_filtre.columns:
    df_carte = df_filtre.sample(min(5000, len(df_filtre)))
    fig = px.scatter_mapbox(df_carte, lat="latitude", lon="longitude", color="prix_m2", size="surface_reelle_bati", hover_data=["valeur_fonciere", "type_local", "date_mutation"], color_continuous_scale=px.colors.sequential.Viridis, size_max=15, zoom=11, mapbox_style="open-street-map", title=f"Carte de {len(df_carte)} transactions (échantillon)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Les données de localisation (latitude/longitude) ne sont pas disponibles pour afficher la carte.")

# Données détaillées
st.subheader("Détail des Transactions (dernières)")
st.dataframe(df_filtre.sort_values('date_mutation', ascending=False).head(100).drop(columns=['latitude', 'longitude'], errors='ignore'))