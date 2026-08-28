import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

st.set_page_config(
    page_title="Dashboard Immobilier Gironde",
    page_icon="🏘️",
    layout="wide"
)

# ✅ CODES INSEE CORRECTS (vérifiés)
COMMUNES_GIRONDE = {
    "33063": "Bordeaux",
    "33039": "Bègles",
    "33064": "Le Bouscat",
    "33075": "Cenon",
    "33069": "Bruges",
    "33119": "Eysines",
    "33192": "Gradignan",
    "33200": "Gujan-Mestras",
    "33249": "Lormont",
    "33273": "Mérignac",
    "33281": "Pessac",
    "33312": "Saint-Médard-en-Jalles",
    "33318": "Talence",
    "33449": "Villenave-d'Ornon",
    "33056": "Blanquefort",
    "33162": "Floirac",
    "33243": "Libourne",
    "33522": "Arcachon",
    "33529": "La Teste-de-Buch",
    "33550": "Cestas",
    "33001": "Aiguillon",
    "33002": "Ambès",
    "33009": "Arès",
    "33016": "Audenge",
    "33023": "Barsac",
    "33028": "Bégadan",
    "33034": "Biganos",
    "33040": "Bouliac",
    "33047": "Bruges",
    "33059": "Carbon-Blanc",
    "33091": "Martillac",
    "33097": "Pauillac",
    "33103": "Saint-Émilion",
    "33106": "Saint-Loubès",
    "33128": "Yvrac",
}

# Inverser : Nom -> Code INSEE
NOMS_COMMUNES = {v: k for k, v in COMMUNES_GIRONDE.items()}


@st.cache_data
def load_all_data():
    """Charge les données DVF depuis le fichier local."""
    file_path = "dvf_2024.csv"
    
    if not os.path.exists(file_path):
        st.error(f"❌ Fichier {file_path} introuvable.")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path, sep=',', low_memory=False)
        
        if df.empty:
            return pd.DataFrame()

        # Conversions
        df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors='coerce')
        df["valeur_fonciere"] = pd.to_numeric(df["valeur_fonciere"], errors='coerce')
        df["surface_reelle_bati"] = pd.to_numeric(df["surface_reelle_bati"], errors='coerce')

        # ✅ FILTRE ADAPTÉ : selon le format de vos données
        if "type_local" in df.columns:
            # Si vos données ont "Maison"/"Appartement"
            df = df[df["type_local"].isin(['Maison', 'Appartement'])]
        elif "libtypbien" in df.columns:
            # Si vos données DVF+ ont "UNE MAISON"/"UN APPARTEMENT"
            df = df[df["libtypbien"].str.contains("MAISON|APPARTEMENT", case=False, na=False)]

        df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati", "date_mutation"])

        if df.empty:
            return pd.DataFrame()

        # Prix m²
        df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
        df = df[(df['prix_m2'] > 200) & (df['prix_m2'] < 15000)]

        # ✅ Normaliser le code commune
        if "code_commune" in df.columns:
            df["code_commune"] = df["code_commune"].astype(str).str.zfill(5)
        elif "l_codinsee" in df.columns:
            df["code_commune"] = df["l_codinsee"].astype(str).str.zfill(5)

        return df

    except Exception as e:
        st.error(f"❌ Erreur chargement : {e}")
        return pd.DataFrame()


# === INTERFACE ===
st.title("🏘️ Dashboard Immobilier Gironde")

# Sélection commune
st.sidebar.header("Sélection de la commune")
selected_commune_name = st.sidebar.selectbox(
    "Choisissez une commune :",
    options=sorted(NOMS_COMMUNES.keys())
)
selected_insee_code = NOMS_COMMUNES[selected_commune_name]

st.info(f"ℹ️ Données DVF pour **{selected_commune_name}** (INSEE {selected_insee_code})")

# Chargement
with st.spinner("Chargement des données..."):
    all_data = load_all_data()

if all_data.empty:
    st.warning("Aucune donnée valide.")
    st.stop()

# Debug : montrer les codes INSEE présents dans le fichier
with st.sidebar.expander("🔍 Diagnostic"):
    if "code_commune" in all_data.columns:
        codes_present = all_data["code_commune"].unique()[:20]
        st.write(f"Codes INSEE dans le fichier (20 premiers) :")
        st.write(sorted(codes_present))
        st.write(f"Code recherché : {selected_insee_code}")
        st.write(f"Trouvé : {selected_insee_code in all_data['code_commune'].values}")

# Filtre commune
df = all_data[all_data['code_commune'] == selected_insee_code].copy()

if df.empty:
    st.warning(f"Aucune donnée pour {selected_commune_name} (code {selected_insee_code}).")
    st.info("Vérifiez que le code INSEE est correct dans le fichier.")
    st.stop()

# Filtres
st.sidebar.header("Filtres")

if "code_postal" in df.columns:
    cp_disp = sorted(df['code_postal'].astype(str).unique())
    cp_sel = st.sidebar.multiselect("Code postal", cp_disp, default=cp_disp)
    df_filtre = df[df['code_postal'].astype(str).isin(cp_sel)].copy()
else:
    df_filtre = df.copy()

type_local = st.sidebar.selectbox("Type de bien", ['Tous', 'Maison', 'Appartement'])
prix_min = st.sidebar.number_input("Prix min (€)", value=0, step=10000)
prix_max = st.sidebar.number_input("Prix max (€)", value=int(df['valeur_fonciere'].max()), step=10000)

df_filtre = df_filtre[
    (df_filtre['valeur_fonciere'] >= prix_min) &
    (df_filtre['valeur_fonciere'] <= prix_max)
].copy()

if type_local != 'Tous' and 'type_local' in df_filtre.columns:
    df_filtre = df_filtre[df_filtre['type_local'] == type_local]

if df_filtre.empty:
    st.warning("Aucun résultat avec ces filtres.")
    st.stop()

# KPIs
st.header(f"Indicateurs pour {selected_commune_name}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Prix/m² moyen", f"{df_filtre['prix_m2'].mean():.0f} €")
c2.metric("Prix médian", f"{df_filtre['valeur_fonciere'].median():.0f} €")
c3.metric("Transactions", f"{len(df_filtre):,}")
c4.metric("Surface moy.", f"{df_filtre['surface_reelle_bati'].mean():.0f} m²")

# Graphiques
st.header(f"Visualisations pour {selected_commune_name}")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribution Prix/m²")
    color_col = "type_local" if "type_local" in df_filtre.columns else None
    fig = px.histogram(df_filtre, x='prix_m2', nbins=40, color=color_col, marginal="box")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Types de biens")
    if color_col:
        fig = px.pie(df_filtre, names='type_local', title='Répartition')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pas de colonne type_local")

# ✅ CARTE CORRIGÉE : st.map() au lieu de px.scatter_mapbox
st.subheader(f"🗺️ Carte des Transactions – {selected_commune_name}")

if 'latitude' in df_filtre.columns and 'longitude' in df_filtre.columns:
    df_carte = df_filtre[['latitude', 'longitude', 'prix_m2', 'surface_reelle_bati']].dropna().copy()
    df_carte['latitude'] = pd.to_numeric(df_carte['latitude'], errors='coerce')
    df_carte['longitude'] = pd.to_numeric(df_carte['longitude'], errors='coerce')
    df_carte = df_carte.dropna()

    # Vérifier coordonnées valides
    valid = (df_carte['latitude'].between(-90, 90)) & (df_carte['longitude'].between(-180, 180))

    if valid.any():
        carte = df_carte[valid].copy()
        if len(carte) > 2000:
            carte = carte.sample(2000, random_state=42)
            st.caption(f"📍 {len(carte)} points affichés")
        
        # ✅ st.map() : pas besoin de token Mapbox !
        st.map(carte, latitude='latitude', longitude='longitude',
               size='surface_reelle_bati', color='prix_m2')
    else:
        st.warning("⚠️ Coordonnées hors limites (peut-être en Lambert 93).")
        with st.expander("Diagnostic coordonnées"):
            st.write(df_carte.describe())
else:
    st.info("📍 Pas de colonnes latitude/longitude disponibles.")

# Détail
st.subheader("📋 Dernières transactions")
cols_show = ['date_mutation', 'valeur_fonciere', 'surface_reelle_bati', 
             'prix_m2', 'type_local', 'code_postal']
cols_disp = [c for c in cols_show if c in df_filtre.columns]
if cols_disp:
    st.dataframe(
        df_filtre.sort_values('date_mutation', ascending=False)
        .head(100)[cols_disp],
        hide_index=True,
        use_container_width=True
    )

st.caption(f"📊 DVF Gironde – {datetime.now().strftime('%d/%m/%Y %H:%M')}")
