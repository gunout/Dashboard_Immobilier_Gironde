# Dashboard_Immobilier_Gironde // 2 METHODE - HTTP ou LOCAL ( Données Année 2024 ) 
🏘️ Dashboard Immobilier Gironde  ℹ️ Données réelles DVF 2024 pour la commune de Aiguillon (INSEE 33001), provenant de data.gouv.fr

<img width="662" height="465" alt="Screenshot_2025-10-15_02-06-59" src="https://github.com/user-attachments/assets/6e9a38a5-6a2d-4524-9a6d-bf3d19c85eab" />

# EXAMPLE 
<img width="1280" height="1024" alt="Screenshot_2025-10-15_02-04-08" src="https://github.com/user-attachments/assets/41ad2181-0f14-4e55-ae02-6f00a275209c" />
<img width="1280" height="1024" alt="Screenshot_2025-10-15_02-04-22" src="https://github.com/user-attachments/assets/43f8239c-7728-41b8-85dc-76646686c1e3" />

# INSTALL DEPENDENCIES

    pip install beautifulsoup4 streamlit pandas requests plotly

# RUN PROGRAM ( GIRONDE - 535 communes.) METHODE HTTP

    streamlit run Dashboard_Bordeaux.py

# RUN PROGRAM ( GIRONDE - PESSAC ) METHODE HTTP

    streamlit run dashboard_bordeaux_pessac.py

<img width="1280" height="1024" alt="Screenshot_2025-10-15_01-57-37" src="https://github.com/user-attachments/assets/0848fd23-3f80-464e-8328-fd37b84e1f6b" />
<img width="1280" height="1024" alt="Screenshot_2025-10-15_01-59-16" src="https://github.com/user-attachments/assets/1c052645-f4ac-4148-b5da-cb8ec48243fe" />


# RUN PROOGRAM ( GIRONDE - 535 communes ) METHODE LOCAL

    streamlit run Dash.py

PS : pour la methode local s'assurer d'avoir le fichier : dvf_2024.csv dans le meme dossier que Dash.py 

# TÉLÉCHARGEMENT " dvf_2024.csv " avec CURL 

    curl -L -o dvf_2024.csv.gz "https://files.data.gouv.fr/geo-dvf/latest/csv/2024/full.csv.gz"

By Gleaphe 2025 .
