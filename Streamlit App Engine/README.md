Dans Google Cloud Cloud shell :

Créer les fichiers :

requirements.txt
streamlit_app.py
app.yaml

Pour tester, lancer les commandes suivantes : 
python3 -m venv 
streamlit-env source
streamlit-env/bin/activate 
pip install -r requirements.txt 
streamlit run streamlit_app.py
--browser.serverAddress=localhost
--server.enableCORS=false
--server.enableXsrfProtection=false
--server.port 8080

Pour déployer, lancer les commandes suivantes : gcloud app deploy

Tester avec l'URL dans : gcloud app browse

Pour utiliser Cloud Run : https://www.cloudskillsboost.google/course_templates/978/labs/488167

Bonus : activer l'authification pour certains compte google

Source :

https://medium.com/bitstrapped/step-by-step-guide-deploying-streamlit-apps-on-google-cloud-platform-gcp-96fca6a4f331
https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/sample-apps/gemini-streamlit-cloudrun/app.py