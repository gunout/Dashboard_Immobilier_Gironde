# dashboard_gironde_multi_communes.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import requests
import io
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Immobilier Gironde",
    page_icon="🏘️",
    layout="wide"
)

# --- Dictionnaire des communes de la Gironde (Code INSEE -> Nom) ---
# NOTE : Pour un usage en production, il faudrait la liste complète des 535 communes.
# Vous pouvez trouver cette liste sur des sites comme data.gouv.fr ou l'INSEE.
# J'inclus ici une liste partielle pour la démonstration.
COMMUNES_GIRONDE = {
    "33001": "Aiguillon",
    "33002": "Ambès",
    "33004": "Arbanats",
    "33007": "Arcins",
    "33009": "Arès",
    "33010": "Argentenac",
    "33011": "Arès",
    "33012": "Artigues-près-Bordeaux",
    "33013": "Asques",
    "33016": "Audenge",
    "33018": "Auros",
    "33020": "Balan",
    "33022": "Barie",
    "33023": "Barsac",
    "33024": "Bassanne",
    "33026": "Baujan",
    "33028": "Bégadan",
    "33030": "Bègles",
    "33031": "Béguey",
    "33032": "Beychac-et-Caillau",
    "33033": "Bieujac",
    "33034": "Biganos",
    "33035": "Blanquefort",
    "33036": "Blésignac",
    "33037": "Bommes",
    "33038": "Bordeaux",
    "33039": "Boudran",
    "33040": "Bouliac",
    "33041": "Le Bouscat",
    "33042": "Bourdelles",
    "33043": "Branne",
    "33044": "Brannens",
    "33045": "Braud-et-Saint-Louis",
    "33046": "Breton",
    "33047": "Bruges",
    "33048": "Budos",
    "33049": "Bujan",
    "33050": "Buran",
    "33051": "Cabara",
    "33052": "Cadarsac",
    "33053": "Cadillac",
    "33054": "Cadaujac",
    "33055": "Camiac-et-Saint-Denis",
    "33056": "Camiran",
    "33057": "Canéjan",
    "33058": "Capian",
    "33059": "Carbon-Blanc",
    "33060": "Cardan",
    "33061": "Carignan-de-Bordeaux",
    "33062": "Carmen",
    "33063": "Cars",
    "33064": "Casseuil",
    "33065": "Castelnau-de-Médoc",
    "33066": "Castelviel",
    "33067": "Castillon-de-Castets",
    "33068": "Caudrot",
    "33069": "Caujac",
    "33070": "Cazats",
    "33071": "Cazaugitat",
    "33072": "Cérons",
    "33073": "Cestas",
    "33074": "Chadenac",
    "33075": "Chambon",
    "33076": "Chamadelle",
    "33077": "Le Chapus",
    "33078": "Le Pian-Médoc",
    "33079": "Le Pout",
    "33080": "Le Taillan-Médoc",
    "33081": "Les Billaux",
    "33082": "Les Essarts",
    "33083": "Lignan-de-Bordeaux",
    "33084": "Loupes",
    "33085": "Ludon-Médoc",
    "33086": "Lussac",
    "33087": "Macau",
    "33088": "Madirac",
    "33089": "Maignaut-Tauzia",
    "33090": "Marmande",
    "33091": "Martillac",
    "33092": "Mérignac",
    "33093": "Moulon-en-Médoc",
    "33094": "Naujac-sur-Mer",
    "33095": "Neuillac",
    "33096": "Noaillac",
    "33097": "Pauillac",
    "33098": "Pessac",
    "33099": "Peyrat-de-Bellegarde",
    "33100": "Pujols-sur-Ciron",
    "33101": "Queyrac",
    "33102": "Rions",
    "33103": "Saint-Émilion",
    "33104": "Saint-Genès-de-Lombaud",
    "33105": "Saint-Laurent-Médoc",
    "33106": "Saint-Loubès",
    "33107": "Saint-Médard-en-Jalles",
    "33108": "Saint-Pierre-de-Mons",
    "33109": "Saint-Quentin-de-Baron",
    "33110": "Saint-Selve",
    "33111": "Saint-Vincent-de-Paul",
    "33112": "Sallebœuf",
    "33113": "Saumos",
    "33114": "Savignac-de-l'Isle",
    "33115": "Tabanac",
    "33116": "Talence",
    "33117": "Targon",
    "33118": "Le Taillan-Médoc",
    "33119": "Tauriac",
    "33120": "Teuillac",
    "33121": "Tizac-de-Lapouyade",
    "33122": "Torcy",
    "33123": "Le Tourne",
    "33124": "Le Tuzan",
    "33125": "Villenave-d'Ornon",
    "33126": "Villeneuve-de-Marsan",
    "33127": "Villeneuve-lès-Bordeaux",
    "33128": "Yvrac",
    # ... Ajoutez les autres communes ici
}

# Inverser le dictionnaire pour avoir Nom -> Code INSEE (plus pratique pour le selectbox)
NOMS_COMMUNES = {v: k for k, v in COMMUNES_GIRONDE.items()}

# --- Fonction de chargement des données (générique) ---
@st.cache_data
def load_commune_data(insee_code: str):
    """
    Charge les données DVF 2024 pour une commune donnée par son code INSEE.
    """
    url = f"https://files.data.gouv.fr/geo-dvf/latest/csv/2024/communes/33/{insee_code}.csv"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text), sep=',', low_memory=False)
        
        if df.empty:
            return pd.DataFrame()

        # Nettoyage (identique à la version précédente)
        df["date_mutation"] = pd.to_datetime(df["date_mutation"], format='%Y-%m-%d', errors='coerce')
        df["valeur_fonciere"] = pd.to_numeric(df["valeur_fonciere"], errors='coerce')
        df = df[df["type_local"].isin(['Maison', 'Appartement'])]
        
        if df.empty:
            return pd.DataFrame()

        df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati", "code_postal", "date_mutation"])
        df["surface_reelle_bati"] = pd.to_numeric(df["surface_reelle_bati"], errors='coerce')
        df = df.dropna(subset=["surface_reelle_bati"])

        if df.empty:
            return pd.DataFrame()

        df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
        df = df[(df['prix_m2'] > 200) & (df['prix_m2'] < 15000)]
        
        if df.empty:
            return pd.DataFrame()
        
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion pour la commune {insee_code} : {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Une erreur est survenue : {e}")
        return pd.DataFrame()

# --- Interface Utilisateur ---
st.title("🏘️ Dashboard Immobilier Gironde")

# Sélection de la commune dans la barre latérale
st.sidebar.header("Sélection de la commune")
selected_commune_name = st.sidebar.selectbox(
    "Choisissez une commune :",
    options=sorted(NOMS_COMMUNES.keys())
)

# Récupérer le code INSEE correspondant
selected_insee_code = NOMS_COMMUNES[selected_commune_name]

# Afficher un message d'information dynamique
st.info(f"ℹ️ Données réelles DVF 2024 pour la commune de **{selected_commune_name}** (INSEE {selected_insee_code}), provenant de data.gouv.fr")

# --- Chargement et Traitement des Données ---
df = load_commune_data(selected_insee_code)

if df.empty:
    st.warning(f"Aucune donnée de vente (Maison/Appartement) valide trouvée pour {selected_commune_name} en 2024.")
    st.stop()

# --- Filtres ---
st.sidebar.header("Filtres")
codes_postaux_disponibles = sorted(df['code_postal'].astype(str).unique())
code_postal_selectionne = st.sidebar.multiselect("Code postal", codes_postaux_disponibles, default=codes_postaux_disponibles)
type_local = st.sidebar.selectbox("Type de bien", ['Tous', 'Maison', 'Appartement'])
prix_min = st.sidebar.number_input("Prix minimum (€)", value=0, step=10000)
prix_max = st.sidebar.number_input("Prix maximum (€)", value=int(df['valeur_fonciere'].max()), step=10000)

# Application des filtres
df_filtre = df[
    (df['code_postal'].astype(str).isin(code_postal_selectionne)) &
    (df['valeur_fonciere'] >= prix_min) &
    (df['valeur_fonciere'] <= prix_max)
].copy()

if type_local != 'Tous':
    df_filtre = df_filtre[df_filtre['type_local'] == type_local]

if df_filtre.empty:
    st.warning("Aucune transaction ne correspond à vos filtres.")
    st.stop()

# --- KPIs et Visualisations ---
st.header(f"Indicateurs Clés pour {selected_commune_name}")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Prix Moyen / m²", f"{df_filtre['prix_m2'].mean():.0f} €")
with col2:
    st.metric("Prix Médian", f"{df_filtre['valeur_fonciere'].median():.0f} €")
with col3:
    st.metric("Transactions", f"{len(df_filtre):,}")
with col4:
    surface_moyenne = df_filtre['surface_reelle_bati'].mean()
    st.metric("Surface Moyenne", f"{surface_moyenne:.0f} m²")

st.header(f"Visualisations pour {selected_commune_name}")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Répartition des Prix au m²")
    fig = px.histogram(df_filtre, x='prix_m2', nbins=50, color='type_local', marginal="box")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("Répartition des Types de Biens")
    fig = px.pie(df_filtre, names='type_local', title='Répartition par type')
    st.plotly_chart(fig, use_container_width=True)

st.subheader(f"Carte des Transactions à {selected_commune_name}")
if 'latitude' in df_filtre.columns and 'longitude' in df_filtre.columns:
    df_carte = df_filtre.sample(min(5000, len(df_filtre)))
    fig = px.scatter_mapbox(df_carte, lat="latitude", lon="longitude", color="prix_m2", size="surface_reelle_bati", hover_data=["valeur_fonciere", "type_local", "date_mutation"], color_continuous_scale=px.colors.sequential.Viridis, size_max=15, zoom=11, mapbox_style="open-street-map", title=f"Carte de {len(df_carte)} transactions (échantillon)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Les données de localisation (latitude/longitude) ne sont pas disponibles pour afficher la carte.")

st.subheader("Détail des Transactions (dernières)")
st.dataframe(df_filtre.sort_values('date_mutation', ascending=False).head(100).drop(columns=['latitude', 'longitude'], errors='ignore'))