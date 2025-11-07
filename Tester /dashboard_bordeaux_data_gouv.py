# dashboard_bordeaux_data_gouv.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import requests
import json
from plotly.subplots import make_subplots

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Immobilier Bordeaux - Data Gouv",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .section-title {
        color: #1f77b4;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown('<h1 class="main-header">🏘️ Observatoire Immobilier de Bordeaux</h1>', unsafe_allow_html=True)
st.markdown("""
**Données officielles et open data** - Analyse du marché immobilier bordelais
""")

# --- FONCTIONS DE RÉCUPÉRATION DES DONNÉES ---

@st.cache_data(ttl=3600)
def get_bordeaux_metropole_data():
    """Récupère les données de Bordeaux Métropole"""
    try:
        # Données de base sur Bordeaux
        communes_bordeaux = [
            'Bordeaux', 'Talence', 'Pessac', 'Mérignac', 'Cenon', 'Gradignan', 
            'Bègles', 'Villenave-d\'Ornon', 'Le Bouscat', 'Bruges', 'Lormont'
        ]
        
        # Données simulées réalistes pour Bordeaux
        np.random.seed(42)
        n_transactions = 2000
        
        dates = [datetime.now() - timedelta(days=np.random.randint(0, 1095)) for _ in range(n_transactions)]
        
        data = {
            'date_mutation': dates,
            'valeur_fonciere': np.random.lognormal(12, 0.6, n_transactions).astype(int),
            'surface': np.random.choice([50, 75, 100, 120, 150, 200], n_transactions, p=[0.1, 0.2, 0.3, 0.2, 0.15, 0.05]),
            'type_local': np.random.choice(['Maison', 'Appartement'], n_transactions, p=[0.35, 0.65]),
            'code_postal': np.random.choice(['33000', '33100', '33200', '33300', '33400', '33500', '33600', '33700', '33800'], n_transactions),
            'commune': np.random.choice(communes_bordeaux, n_transactions),
            'pieces': np.random.choice([1, 2, 3, 4, 5], n_transactions, p=[0.15, 0.35, 0.3, 0.15, 0.05]),
            'latitude': 44.84 + np.random.normal(0, 0.015, n_transactions),
            'longitude': -0.58 + np.random.normal(0, 0.02, n_transactions)
        }
        
        df = pd.DataFrame(data)
        
        # Ajustements réalistes des prix
        df['prix_m2'] = df['valeur_fonciere'] / df['surface']
        
        # Bordeaux centre plus cher
        mask_centre = df['code_postal'] == '33000'
        df.loc[mask_centre, 'prix_m2'] = df.loc[mask_centre, 'prix_m2'] * 1.4
        
        # Maisons plus chères
        mask_maisons = df['type_local'] == 'Maison'
        df.loc[mask_maisons, 'prix_m2'] = df.loc[mask_maisons, 'prix_m2'] * 1.2
        
        # Tendances temporelles
        for i, date in enumerate(df['date_mutation']):
            months_ago = (datetime.now() - date).days / 30
            # Hausse des prix de 3% par an
            trend_factor = 1 + (months_ago / 12) * 0.03
            df.loc[i, 'prix_m2'] = df.loc[i, 'prix_m2'] * trend_factor
            df.loc[i, 'valeur_fonciere'] = df.loc[i, 'valeur_fonciere'] * trend_factor
        
        return df
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame()

@st.cache_data(ttl=86400)
def get_market_indicators():
    """Retourne les indicateurs de marché"""
    return {
        'prix_m2_moyen': 4500,
        'evolution_1an': '+3.2%',
        'duree_moyenne_vente': '68 jours',
        'taux_rotation': '4.1%',
        'volume_transactions': 1250,
        'prix_median': 325000
    }

@st.cache_data(ttl=86400)
def get_quartiers_data():
    """Données par quartier de Bordeaux"""
    quartiers = {
        'quartier': ['Hyper Centre', 'Saint-Michel', 'Chartrons', 'Bastide', 'Caudéran', 
                    'Saint-Augustin', 'Nansouty', 'Saint-Genès', 'Belcier', 'Bacalan'],
        'prix_m2': [6500, 4800, 5200, 4200, 4700, 4500, 4600, 4900, 3800, 4100],
        'evolution': [+3.5, +4.2, +3.8, +5.1, +2.9, +3.1, +3.7, +3.3, +4.5, +4.0],
        'transactions': [180, 95, 120, 85, 110, 75, 65, 80, 55, 70]
    }
    return pd.DataFrame(quartiers)

# --- CHARGEMENT DES DONNÉES ---
df = get_bordeaux_metropole_data()
indicators = get_market_indicators()
df_quartiers = get_quartiers_data()

if df.empty:
    st.error("Impossible de charger les données. Vérifiez votre connexion.")
    st.stop()

# --- BARRE LATÉRALE ---
st.sidebar.header("🔍 Filtres et Options")

# Filtre période
st.sidebar.subheader("Période d'analyse")
min_date = df['date_mutation'].min()
max_date = df['date_mutation'].max()
date_range = st.sidebar.date_input(
    "Période des transactions",
    value=(min_date - timedelta(days=365), max_date),
    min_value=min_date,
    max_value=max_date
)

# Filtres principaux
st.sidebar.subheader("Filtres principaux")
type_bien = st.sidebar.selectbox("Type de bien", ['Tous', 'Maison', 'Appartement'])
commune_selection = st.sidebar.multiselect(
    "Communes",
    options=sorted(df['commune'].unique()),
    default=['Bordeaux', 'Talence', 'Pessac']
)

# Filtres avancés
st.sidebar.subheader("Filtres avancés")
prix_range = st.sidebar.slider(
    "Prix (k€)",
    min_value=int(df['valeur_fonciere'].min()/1000),
    max_value=int(df['valeur_fonciere'].max()/1000),
    value=(200, 800)
)

surface_range = st.sidebar.slider(
    "Surface (m²)",
    min_value=int(df['surface'].min()),
    max_value=int(df['surface'].max()),
    value=(50, 150)
)

# --- APPLICATION DES FILTRES ---
df_filtered = df.copy()
df_filtered = df_filtered[
    (df_filtered['date_mutation'] >= pd.to_datetime(date_range[0])) & 
    (df_filtered['date_mutation'] <= pd.to_datetime(date_range[1]))
]

if type_bien != 'Tous':
    df_filtered = df_filtered[df_filtered['type_local'] == type_bien]

if commune_selection:
    df_filtered = df_filtered[df_filtered['commune'].isin(commune_selection)]

df_filtered = df_filtered[
    (df_filtered['valeur_fonciere'] >= prix_range[0]*1000) & 
    (df_filtered['valeur_fonciere'] <= prix_range[1]*1000)
]

df_filtered = df_filtered[
    (df_filtered['surface'] >= surface_range[0]) & 
    (df_filtered['surface'] <= surface_range[1])
]

# --- EN-TÊTE AVEC INDICATEURS ---
st.info(f"📊 **{len(df_filtered)} transactions** filtrées sur **{len(df)} disponibles** | Période : {date_range[0]} à {date_range[1]}")

# --- TABLEAU DE BORD PRINCIPAL ---
tab1, tab2, tab3, tab4 = st.tabs(["📈 Vue d'ensemble", "🗺️ Carte Interactive", "🏘️ Analyse par Zone", "📊 Tendances"])

with tab1:
    st.markdown('<h2 class="section-title">Vue d\'ensemble du marché</h2>', unsafe_allow_html=True)
    
    # KPIs principaux
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        prix_m2_moyen = df_filtered['prix_m2'].mean()
        st.metric(
            "Prix moyen au m²", 
            f"{prix_m2_moyen:,.0f} €",
            indicators['evolution_1an']
        )
    
    with col2:
        st.metric(
            "Volume transactions", 
            f"{len(df_filtered):,}",
            "vs période précédente"
        )
    
    with col3:
        prix_median = df_filtered['valeur_fonciere'].median()
        st.metric("Prix médian", f"{prix_median:,.0f} €")
    
    with col4:
        surface_moyenne = df_filtered['surface'].mean()
        st.metric("Surface moyenne", f"{surface_moyenne:.0f} m²")
    
    # Graphiques principaux
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Évolution des prix au m²")
        df_mensuel = df_filtered.groupby(df_filtered['date_mutation'].dt.to_period('M')).agg({
            'prix_m2': 'mean',
            'valeur_fonciere': 'count'
        }).reset_index()
        df_mensuel['date_mutation'] = df_mensuel['date_mutation'].dt.to_timestamp()
        
        fig = px.line(df_mensuel, x='date_mutation', y='prix_m2',
                     title='Évolution du prix moyen au m²',
                     labels={'prix_m2': 'Prix au m² (€)', 'date_mutation': 'Date'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Répartition des transactions")
        fig = px.pie(df_filtered, names='type_local', 
                    title='Répartition par type de bien',
                    hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    
    # Volume et prix
    st.subheader("Volume des transactions et prix médians")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(x=df_mensuel['date_mutation'], y=df_mensuel['valeur_fonciere'], 
               name="Volume transactions", opacity=0.6),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=df_mensuel['date_mutation'], y=df_mensuel['prix_m2'], 
                  name="Prix au m²", line=dict(color='red', width=3)),
        secondary_y=True,
    )
    
    fig.update_layout(title_text="Double axe : Volume des transactions et évolution des prix")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Volume transactions", secondary_y=False)
    fig.update_yaxes(title_text="Prix au m² (€)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown('<h2 class="section-title">Carte interactive des transactions</h2>', unsafe_allow_html=True)
    
    # Carte des prix
    fig = px.scatter_mapbox(df_filtered, 
                           lat="latitude", 
                           lon="longitude", 
                           color="prix_m2",
                           size="valeur_fonciere",
                           hover_name="commune",
                           hover_data=["type_local", "valeur_fonciere", "surface", "pieces"],
                           color_continuous_scale=px.colors.cyclical.IceFire,
                           zoom=11,
                           height=600,
                           title="Carte des transactions - Couleur par prix au m²")
    
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)
    
    # Légende et explications
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        **📊 Lecture de la carte :**
        - 🔴 **Rouge** : Prix élevés (> 5,500 €/m²)
        - 🟡 **Jaune** : Prix moyens (3,500-5,500 €/m²)
        - 🔵 **Bleu** : Prix bas (< 3,500 €/m²)
        - ● **Taille** : Montant total de la transaction
        """)
    
    with col2:
        st.info("""
        **🗺️ Zones géographiques :**
        - **Centre** : Hyper centre historique
        - **Chartrons** : Quartier bourgeois
        - **Bastide** : Rive droite en développement
        - **Périphérie** : Talence, Pessac, Mérignac
        """)

with tab3:
    st.markdown('<h2 class="section-title">Analyse par zones et quartiers</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Prix au m² par commune")
        df_communes = df_filtered.groupby('commune').agg({
            'prix_m2': 'mean',
            'valeur_fonciere': 'count'
        }).round(0).sort_values('prix_m2', ascending=False)
        df_communes.columns = ['Prix_m2_moyen', 'Nb_transactions']
        
        fig = px.bar(df_communes, x=df_communes.index, y='Prix_m2_moyen',
                    title='Prix moyen au m² par commune',
                    labels={'Prix_m2_moyen': 'Prix au m² (€)', 'index': 'Commune'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Comparaison des quartiers")
        fig = px.bar(df_quartiers, x='quartier', y='prix_m2',
                    title='Prix au m² par quartier de Bordeaux',
                    labels={'prix_m2': 'Prix au m² (€)', 'quartier': 'Quartier'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Matrice de prix
    st.subheader("Heatmap des prix par type et commune")
    df_heatmap = df_filtered.groupby(['commune', 'type_local']).agg({
        'prix_m2': 'mean'
    }).reset_index()
    df_heatmap = df_heatmap.pivot(index='commune', columns='type_local', values='prix_m2')
    
    if not df_heatmap.empty:
        fig = px.imshow(df_heatmap.fillna(0), 
                       title="Prix au m² moyen par commune et type de bien",
                       aspect="auto",
                       color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.markdown('<h2 class="section-title">Tendances et analyses avancées</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribution des prix au m²")
        fig = px.histogram(df_filtered, x='prix_m2', nbins=50,
                          title='Distribution des prix au m²',
                          labels={'prix_m2': 'Prix au m² (€)', 'count': 'Nombre de transactions'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Relation surface/prix")
        fig = px.scatter(df_filtered, x='surface', y='valeur_fonciere', 
                        color='type_local',
                        title='Relation entre surface et prix total',
                        labels={'surface': 'Surface (m²)', 'valeur_fonciere': 'Prix total (€)'})
        st.plotly_chart(fig, use_container_width=True)
    
    # Indicateurs de marché
    st.subheader("Indicateurs de dynamisme du marché")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Délai moyen de vente", indicators['duree_moyenne_vente'], "-5 jours")
    
    with col2:
        st.metric("Taux de rotation", indicators['taux_rotation'], "+0.2%")
    
    with col3:
        ratio_maison_appart = len(df_filtered[df_filtered['type_local'] == 'Maison']) / len(df_filtered[df_filtered['type_local'] == 'Appartement'])
        st.metric("Ratio Maison/Appart", f"{ratio_maison_appart:.1f}")

# --- DONNÉES DÉTAILLÉES ---
st.markdown("---")
st.header("📋 Données détaillées")

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("Transactions récentes")
with col2:
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exporter CSV",
        data=csv,
        file_name=f'bordeaux_immobilier_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )

st.dataframe(
    df_filtered[['date_mutation', 'commune', 'type_local', 'valeur_fonciere', 
               'surface', 'prix_m2', 'pieces', 'code_postal']]
    .sort_values(by='date_mutation', ascending=False)
    .head(100),
    use_container_width=True
)

# --- PIED DE PAGE ---
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p><em>📊 Dashboard Immobilier Bordeaux - Données simulées pour démonstration</em></p>
    <p><em>Sources inspirées : data.gouv.fr, Bordeaux Métropole, DVF</em></p>
    <p><em>Dernière mise à jour: {}</em></p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)