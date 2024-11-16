import os
import json
import tempfile
import git
import functions_framework

from google.cloud import logging
from google.cloud import storage

PROJECT_ID = "doxygen-gcp"
LOCATION = "europe-west1"
BUCKET = "doxygen-gcp-storage"
LOG_NAME = "run_inference-cloudfunction-download-log"

client = logging.Client(project=PROJECT_ID)
client.setup_logging()
logger = client.logger(LOG_NAME)

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET)

@functions_framework.http
def run_inference(request):
    """HTTP Cloud Function.
    Args:
        a GET HTTP request with 'url' query parameter 
    Returns:
        a HTTP response with the storage_uri
    """

    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'url' in request_json:
        url = request_json['url']
    elif request_args and 'url' in request_args:
        url = request_args['url']
    else:
        return json.dumps({"response_text": "No url provided"})

    logger.log(f"URL request for prompt: {url}")

    with tempfile.TemporaryDirectory() as tmpdirname:
        # Cloner le répertoire Git
        repo = git.Repo.clone_from(url, tmpdirname)
        repo_name = os.path.basename(url).replace('.git', '')

        # Référence au bucket
        # Parcourir les fichiers du répertoire local et les télécharger dans GCS
        for root, dirs, files in os.walk(tmpdirname):
            for file in files:
                local_file_path = os.path.join(root, file)
                blob_path = os.path.join(repo_name, os.path.relpath(local_file_path, tmpdirname))
                blob = bucket.blob(blob_path)
                blob.upload_from_filename(local_file_path)
                logger.log(f'Téléchargé {local_file_path} vers gs://{BUCKET}/{blob_path}')

    storage_uri = repo_name

    logger.log(f"Git repository downloaded at : {storage_uri}")

    return json.dumps({"storage_uri": storage_uri})
