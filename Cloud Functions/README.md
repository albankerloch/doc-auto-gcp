Dans Google Cloud, créer une Cloud Run Fonction :

Mémoire allouée : 2 Go (au lieu de 256 Mo)
Autoriser tous le traffic externe
Choisir l'environnement d'exécution (Python 3.12)
main.py : contenu du fichier
requirements.txt : contenu du fichier
Déployer

Tester avec :

curl -m 70 -X POST https://europe-west1-doxygen-gcp.cloudfunctions.net/function-1-download -H "Content-Type: application/json" -d '{"url": "test"}'