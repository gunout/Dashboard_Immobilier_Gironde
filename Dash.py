import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Immobilier Gironde",
    page_icon="🏘️",
    layout="wide"
)

# --- Codes INSEE CORRECTS ---
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
    "33059": "Carbon-Blanc",
    "33091": "Martillac",
    "33097": "Pauillac",
    "33103": "Saint-Émilion",
    "33106": "Saint-Loubès",
    "33128": "Yvrac",
    "33003": "Arbanats",
    "33004": "Arcins",
    "33007": "Bassanne",
    "33011": "Artigues-près-Bordeaux",
    "33013": "Asques",
    "33018": "Auros",
    "33022": "Barie",
    "33031": "Béguey",
    "33032": "Beychac-et-Caillau",
    "33033": "Bieujac",
    "33036": "Blésignac",
    "33037": "Bommes",
    "33042": "Bourdelles",
    "33043": "Branne",
    "33044": "Brannens",
    "33045": "Braud-et-Saint-Louis",
    "33048": "Budos",
    "33052": "Cadarsac",
    "33053": "Cadillac",
    "33054": "Cadaujac",
    "33057": "Canéjan",
    "33058": "Capian",
    "33060": "Cardan",
    "33061": "Carignan-de-Bordeaux",
    "33065": "Castelnau-de-Médoc",
    "33066": "Castelviel",
    "33068": "Caudrot",
    "33070": "Cazats",
    "33071": "Cazaugitat",
    "33072": "Cérons",
    "33073": "Cestas",
    "33074": "Chadenac",
    "33076": "Chamadelle",
    "33081": "Les Billaux",
    "33083": "Lignan-de-Bordeaux",
    "33084": "Loupes",
    "33085": "Ludon-Médoc",
    "33086": "Lussac",
    "33087": "Macau",
    "33088": "Madirac",
    "33090": "Marmande",
    "33094": "Naujac-sur-Mer",
    "33095": "Neuillac",
    "33096": "Noaillac",
    "33099": "Peyrat-de-Bellegarde",
    "33100": "Pujols-sur-Ciron",
    "33101": "Queyrac",
    "33102": "Rions",
    "33104": "Saint-Genès-de-Lombaud",
    "33105": "Saint-Laurent-Médoc",
    "33108": "Saint-Pierre-de-Mons",
    "33109": "Saint-Quentin-de-Baron",
    "33110": "Saint-Selve",
    "33111": "Saint-Vincent-de-Paul",
    "33112": "Sallebœuf",
    "33113": "Saumos",
    "33114": "Savignac-de-l'Isle",
    "33115": "Tabanac",
    "33117": "Targon",
    "33120": "Teuillac",
    "33121": "Tizac-de-Lapouyade",
    "33122": "Torcy",
    "33123": "Le Tourne",
    "33124": "Le Tuzan",
    "33125": "Villenave-d'Ornon",
    "33127": "Villeneuve-lès-Bordeaux",
}

# Inverser : Nom -> Code INSEE
NOMS_COMMUNES = {v: k for k, v in COMMUNES_GIRONDE.items()}


@st.cache_data
def load_all_data():
    """Charge les données DVF depuis le fichier local."""
    file_path = "dvf_2024.csv"

    if not os.path.exists(file_path):
        st.error(f"Le fichier {file_path} n'existe pas dans le répertoire.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path, sep=',', low_memory=False)

        if df.empty:
            return pd.DataFrame()

        # Conversions dates et numériques
        df["date_mutation"] = pd.to_datetime(df["date_mutation"], errors='coerce')
        df["valeur_fonciere"] = pd.to_numeric(df["valeur_fonciere"], errors='coerce')
        df["surface_reelle_bati"] = pd.to_numeric(df["surface_reelle_bati"], errors='coerce')

        # Filtrer par type de bien (adapte selon format DVF ou DVF+)
        if "type_local" in df.columns:
            df = df[df["type_local"].isin(['Maison', 'Appartement'])]
        elif "libtypbien" in df.columns:
            df = df[df["libtypbien"].str.contains("MAISON|APPARTEMENT", case=False, na=False)]

        # Supprimer les lignes sans données essentielles
        df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati", "date_mutation"])

        if df.empty:
            return pd.DataFrame()

        # Calcul prix au m²
        df['prix_m2'] = df['valeur_fonciere'] / df['surface_reelle_bati']
        df = df[(df['prix_m2'] > 200) & (df['prix_m2'] < 15000)]

        if df.empty:
            return pd.DataFrame()

        # Normaliser le code commune
        if "code_commune" in df.columns:
            df["code_commune"] = df["code_commune"].astype(str).str.zfill(5)
        elif "l_codinsee" in df.columns:
            df["code_commune"] = df["l_codinsee"].astype(str).str.zfill(5)
        else:
            st.error("Colonne code_commune ou l_codinsee manquante.")
            return pd.DataFrame()

        return df

    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        return pd.DataFrame()


# === INTERFACE UTILISATEUR ===
st.title("🏘️ Dashboard Immobilier Gironde")

# Sélection de la commune
st.sidebar.header("Sélection de la commune")
selected_commune_name = st.sidebar.selectbox(
    "Choisissez une commune :",
    options=sorted(NOMS_COMMUNES.keys())
)
selected_insee_code = NOMS_COMMUNES[selected_commune_name]

st.info(f"Données DVF pour **{selected_commune_name}** (INSEE {selected_insee_code})")

# Chargement des données
with st.spinner("Chargement des données..."):
    all_data = load_all_data()

if all_data.empty:
    st.warning("Aucune donnée valide trouvée.")
    st.stop()

# Diagnostic
with st.sidebar.expander("Diagnostic"):
    if "code_commune" in all_data.columns:
        st.write(f"Code recherché : {selected_insee_code}")
        present = selected_insee_code in all_data["code_commune"].values
        st.write(f"Trouvé dans le fichier : {'OUI' if present else 'NON'}")
        if not present:
            st.write("Codes présents (exemples) :")
            st.write(sorted(all_data["code_commune"].unique())[:30])

# Filtrer pour la commune sélectionnée
df = all_data[all_data['code_commune'] == selected_insee_code].copy()

if df.empty:
    st.warning(f"Aucune donnée pour {selected_commune_name} (code {selected_insee_code}).")
    st.info("Vérifiez que ce code INSEE existe dans votre fichier.")
    st.stop()

# === FILTRES ===
st.sidebar.header("Filtres")

# Code postal
if "code_postal" in df.columns and not df["code_postal"].isna().all():
    cp_disp = sorted(df['code_postal'].astype(str).unique())
    cp_sel = st.sidebar.multiselect("Code postal", cp_disp, default=cp_disp)
    df_filtre = df[df['code_postal'].astype(str).isin(cp_sel)].copy()
else:
    df_filtre = df.copy()

# Type de bien
types_dispo = ["Tous"]
if "type_local" in df_filtre.columns:
    types_dispo.extend(sorted(df_filtre["type_local"].dropna().unique()))
type_local = st.sidebar.selectbox("Type de bien", types_dispo)

# Prix
prix_min = st.sidebar.number_input("Prix minimum (€)", value=0, step=10000)
prix_max = st.sidebar.number_input("Prix maximum (€)", value=int(df['valeur_fonciere'].max()), step=10000)

# Appliquer les filtres
df_filtre = df_filtre[
    (df_filtre['valeur_fonciere'] >= prix_min) &
    (df_filtre['valeur_fonciere'] <= prix_max)
].copy()

if type_local != 'Tous' and "type_local" in df_filtre.columns:
    df_filtre = df_filtre[df_filtre['type_local'] == type_local]

if df_filtre.empty:
    st.warning("Aucune transaction ne correspond à vos filtres.")
    st.stop()

# === KPIs ===
st.header(f"Indicateurs pour {selected_commune_name}")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Prix/m² moyen", f"{df_filtre['prix_m2'].mean():.0f} €")
col2.metric("Prix médian", f"{df_filtre['valeur_fonciere'].median():.0f} €")
col3.metric("Transactions", f"{len(df_filtre):,}")
col4.metric("Surface moyenne", f"{df_filtre['surface_reelle_bati'].mean():.0f} m²")

# === GRAPHIQUES ===
st.header(f"Visualisations pour {selected_commune_name}")
col1, col2 = st.columns(2)

color_col = "type_local" if "type_local" in df_filtre.columns else None

with col1:
    st.subheader("Distribution Prix/m²")
    fig = px.histogram(df_filtre, x='prix_m2', nbins=40, color=color_col, marginal="box")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Répartition par type")
    if color_col:
        fig = px.pie(df_filtre, names='type_local', title='Types de biens')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pas de colonne type_local disponible.")

# === CARTE ===
st.subheader(f"Carte des Transactions à {selected_commune_name}")

if 'latitude' in df_filtre.columns and 'longitude' in df_filtre.columns:
    # Préparer les données pour la carte
    df_carte = df_filtre[['latitude', 'longitude', 'prix_m2', 'surface_reelle_bati']].copy()
    df_carte['latitude'] = pd.to_numeric(df_carte['latitude'], errors='coerce')
    df_carte['longitude'] = pd.to_numeric(df_carte['longitude'], errors='coerce')
    df_carte = df_carte.dropna()

    # Vérifier que les coordonnées sont valides (WGS84)
    valid = (
        df_carte['latitude'].between(-90, 90) &
        df_carte['longitude'].between(-180, 180)
    )

    if valid.any():
        carte = df_carte[valid].copy()
        if len(carte) > 2000:
            carte = carte.sample(2000, random_state=42)
            st.caption(f"Affichage de {len(carte)} transactions (échantillon)")

        # st.map() - Pas besoin de token Mapbox
        st.map(
            carte,
            latitude="latitude",
            longitude="longitude",
            size="surface_reelle_bati",
            color="prix_m2"
        )
    else:
        st.warning("Les coordonnées semblent être en Lambert 93 (non converties en WGS84).")
        with st.expander("Diagnostic coordonnées"):
            st.dataframe(df_carte.describe())
else:
    st.info("Les colonnes latitude/longitude ne sont pas disponibles.")

# === TABLEAU DES TRANSACTIONS ===
st.subheader("Détail des Transactions (dernières)")

cols_afficher = [
    "date_mutation",
    "valeur_fonciere",
    "surface_reelle_bati",
    "prix_m2",
    "type_local",
    "code_postal"
]
cols_disponibles = [c for c in cols_afficher if c in df_filtre.columns]

if cols_disponibles:
    df_affichage = df_filtre.sort_values('date_mutation', ascending=False).head(100).copy()

    # Formater les colonnes
    if "valeur_fonciere" in df_affichage.columns:
        df_affichage["valeur_fonciere"] = df_affichage["valeur_fonciere"].apply(
            lambda x: f"{x:,.0f} €"
        )
    if "prix_m2" in df_affichage.columns:
        df_affichage["prix_m2"] = df_affichage["prix_m2"].apply(
            lambda x: f"{x:,.0f} €/m²"
        )

    st.dataframe(
        df_affichage[cols_disponibles],
        hide_index=True,
        use_container_width=True
    )

# Pied de page
st.markdown("---")
st.caption(f"Dashboard Immobilier Gironde – {datetime.now().strftime('%d/%m/%Y %H:%M')}")
