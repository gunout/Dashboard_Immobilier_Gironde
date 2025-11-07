# dvf_data_fetcher_evolue.py
import requests
import pandas as pd
import os
import pickle
from datetime import datetime, timedelta
import numpy as np
from time import sleep

def fetch_dvf_data_for_bordeaux(limit=5000, use_cache=True):
    """
    Récupère les données DVF enrichies pour la Gironde avec plus de champs.
    """
    cache_file = 'dvf_cache_bordeaux_evolue.pkl'
    cache_valid_duration = timedelta(hours=6)

    # Vérification du cache
    if use_cache and os.path.exists(cache_file):
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - cache_time < cache_valid_duration:
            print(f"📦 Utilisation des données en cache (créé à {cache_time.strftime('%H:%M:%S')})")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

    # Récupération des nouvelles données
    print(f"🔄 Récupération des nouvelles données DVF à {datetime.now().strftime('%H:%M:%S')}...")
    df = _fetch_enriched_data_from_api(limit)

    # Si l'API échoue, utiliser des données sample
    if df.empty:
        st.warning("⚠️ L'API DVF n'est pas accessible. Utilisation de données d'exemple pour la démonstration.")
        df = _generate_sample_data(limit)

    # Sauvegarde du cache
    if use_cache and not df.empty:
        with open(cache_file, 'wb') as f:
            pickle.dump(df, f)
        print(f"💾 Données mises en cache dans {cache_file}")

    return df

def _fetch_enriched_data_from_api(limit):
    """Récupère des données DVF enrichies avec plus de champs."""
    url = "https://api.etalab.gouv.fr/api/records/1.0/search/"
    params = {
        'dataset': 'demandes-de-valeurs-foncieres',
        'rows': limit,
        'sort': '-date_mutation',
        'refine.code_departement': '33'
    }
    
    try:
        # Tentative avec timeout et retry
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                break
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout attempt {attempt + 1}/3")
                if attempt < 2:
                    sleep(2)
                    continue
                else:
                    raise
            except requests.exceptions.ConnectionError:
                print(f"🌐 Connection error attempt {attempt + 1}/3")
                if attempt < 2:
                    sleep(2)
                    continue
                else:
                    raise
        
        records = data.get('records', [])
        if not records:
            print("❌ Aucune donnée trouvée.")
            return pd.DataFrame()

        df = pd.json_normalize(records)
        
        # Sélection des colonnes enrichies
        colonnes_a_garder = [
            'fields.date_mutation', 
            'fields.valeur_fonciere', 
            'fields.surface_terrain',
            'fields.surface_reelle_bati',
            'fields.type_local', 
            'fields.nombre_pieces_principales', 
            'fields.code_postal',
            'fields.nom_commune',
            'fields.nature_mutation',
            'fields.nombre_lots',
            'fields.longitude',
            'fields.latitude'
        ]
        
        # Garder seulement les colonnes disponibles
        colonnes_disponibles = [col for col in colonnes_a_garder if col in df.columns]
        df = df[colonnes_disponibles].copy()
        
        # Renommage
        df.rename(columns={
            'fields.date_mutation': 'date_mutation',
            'fields.valeur_fonciere': 'valeur_fonciere',
            'fields.surface_terrain': 'surface_terrain',
            'fields.surface_reelle_bati': 'surface_bati',
            'fields.type_local': 'type_local',
            'fields.nombre_pieces_principales': 'nombre_pieces',
            'fields.code_postal': 'code_postal',
            'fields.nom_commune': 'nom_commune',
            'fields.nature_mutation': 'nature_mutation',
            'fields.nombre_lots': 'nombre_lots',
            'fields.longitude': 'longitude',
            'fields.latitude': 'latitude'
        }, inplace=True)

        # Nettoyage et conversion des types
        df['date_mutation'] = pd.to_datetime(df['date_mutation'])
        df['valeur_fonciere'] = pd.to_numeric(df['valeur_fonciere'].astype(str).str.replace(',', '.'), errors='coerce')
        df['surface_terrain'] = pd.to_numeric(df['surface_terrain'], errors='coerce')
        df['surface_bati'] = pd.to_numeric(df['surface_bati'], errors='coerce')
        df['nombre_pieces'] = pd.to_numeric(df['nombre_pieces'], errors='coerce')
        df['nombre_lots'] = pd.to_numeric(df['nombre_lots'], errors='coerce')
        
        # Gestion des surfaces nulles ou extrêmes
        df['surface_terrain'] = df['surface_terrain'].fillna(0)
        df = df[df['surface_terrain'] > 0]  # Supprimer les transactions sans surface
        df = df[df['surface_terrain'] < 100000]  # Supprimer les surfaces extrêmes
        
        # Filtrage des données pertinentes
        df.dropna(subset=['valeur_fonciere', 'date_mutation'], inplace=True)
        df = df[df['valeur_fonciere'] > 10000]  # Supprimer les transactions trop faibles
        df = df[df['valeur_fonciere'] < 5000000]  # Supprimer les transactions trop élevées
        
        # Filtrage Bordeaux et alentours
        bordeaux_cp = ['33000', '33100', '33200', '33300', '33400', '33500', '33600', '33700', '33800']
        df_bordeaux = df[df['code_postal'].astype(str).isin(bordeaux_cp)].copy()
        
        print(f"✅ {len(df_bordeaux)} transactions enrichies trouvées pour Bordeaux.")
        return df_bordeaux

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des données : {e}")
        return pd.DataFrame()

def _generate_sample_data(limit=1000):
    """Génère des données d'exemple pour la démonstration quand l'API n'est pas disponible."""
    print("📊 Génération de données d'exemple...")
    
    np.random.seed(42)
    
    # Dates sur les 2 dernières années
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    dates = [start_date + timedelta(days=np.random.randint(0, 730)) for _ in range(limit)]
    
    # Communes de Bordeaux
    communes = ['BORDEAUX', 'TALENCE', 'PESSAC', 'MERIGNAC', 'CENON', 'GRADIGNAN', 'BEGLES', 'VILLENAVE DORNON', 'LE BOUSCAT', 'BORDEAUX CAUDERAN']
    codes_postaux = ['33000', '33100', '33200', '33300', '33400', '33500', '33600', '33700', '33800']
    
    # Types de biens
    types_biens = ['Maison', 'Appartement', 'Local industriel. commercial ou assimilé']
    
    data = {
        'date_mutation': dates,
        'valeur_fonciere': np.random.lognormal(11.5, 0.8, limit).astype(int),
        'surface_terrain': np.random.choice([50, 75, 100, 120, 150, 200, 300, 500, 1000], limit, p=[0.1, 0.2, 0.25, 0.15, 0.1, 0.1, 0.05, 0.03, 0.02]),
        'surface_bati': np.random.choice([30, 50, 70, 90, 110, 130, 150], limit, p=[0.1, 0.2, 0.25, 0.2, 0.15, 0.05, 0.05]),
        'type_local': np.random.choice(types_biens, limit, p=[0.4, 0.55, 0.05]),
        'nombre_pieces': np.random.choice([1, 2, 3, 4, 5, 6], limit, p=[0.1, 0.3, 0.3, 0.2, 0.08, 0.02]),
        'code_postal': np.random.choice(codes_postaux, limit),
        'nom_commune': np.random.choice(communes, limit),
        'nature_mutation': ['Vente'] * limit,
        'nombre_lots': np.random.choice([0, 1, 2, 3], limit, p=[0.7, 0.2, 0.07, 0.03]),
        'longitude': -0.58 + np.random.normal(0, 0.02, limit),
        'latitude': 44.84 + np.random.normal(0, 0.02, limit)
    }
    
    df = pd.DataFrame(data)
    
    # Ajustement des prix selon le type et la localisation
    df['prix_m2'] = df['valeur_fonciere'] / df['surface_terrain']
    
    # Ajustement des prix pour Bordeaux centre
    mask_bordeaux_centre = df['code_postal'] == '33000'
    df.loc[mask_bordeaux_centre, 'valeur_fonciere'] = (df.loc[mask_bordeaux_centre, 'valeur_fonciere'] * 1.3).astype(int)
    
    # Ajustement pour les maisons
    mask_maisons = df['type_local'] == 'Maison'
    df.loc[mask_maisons, 'valeur_fonciere'] = (df.loc[mask_maisons, 'valeur_fonciere'] * 1.2).astype(int)
    
    # Recalcul du prix au m²
    df['prix_m2'] = df['valeur_fonciere'] / df['surface_terrain']
    
    print(f"✅ {len(df)} transactions d'exemple générées.")
    return df