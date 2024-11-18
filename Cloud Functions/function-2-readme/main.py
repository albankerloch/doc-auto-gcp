import os
import json
import functions_framework
import vertexai
import time

from google.cloud import logging, storage
from vertexai.preview.generative_models import GenerativeModel

PROJECT_ID = "doxygen-gcp"
LOCATION = "europe-west1"
BUCKET = "doxygen-gcp-storage"

client = logging.Client(project=PROJECT_ID)
client.setup_logging()

LOG_NAME = "run_inference-cloudfunction-comment-log"
logger = client.logger(LOG_NAME)
storage_client = storage.Client()


def generate_readme(file_analyses):
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel("gemini-1.5-pro")
    readme_prompt = ""
    for file_name, analysis in file_analyses:
        readme_prompt += f"Fichier : {file_name}\n{analysis}\n\n"

    readme_prompt += "Genere moi un fichier README.md pour expliquer ce projet. Je ne veux pas une analyse, pas besoin de donner des recommandations. Il faut qu'il soit bien structuré avec une table des matieres en premier, le titre du projet, une description, comment installer le necessaire si necessaire, comment l'utiliser, les fonctionnalites et un exemple d'utilisation. N'oublie pas de verifier s'il y a un makefile pour la partie utilisation. Si un fichier est necessaire en entree du programme qu'on veut lancer, verifie si ce genre de fichier est fourni dans le projet."
    response = model.generate_content([readme_prompt])
    return response


def read_file_to_variable(blob):
    with blob.open("r") as f:
        file_content = f.read()
        return file_content


def write_variable_to_file(path, content):
    bucket = storage_client.bucket(BUCKET)
    blob = bucket.blob(path)
    with blob.open("w") as f:
        f.write(content)


def list_all_file_paths(bucket_name, directory_path):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    file_paths = []
    queue = [directory_path]
    while queue:
        current_path = queue.pop(0)
        # List blobs within the current path
        blobs = bucket.list_blobs(prefix=current_path)
        for blob in blobs:
            # If it's a file (doesn't end with a slash)
            if not blob.name.endswith("/"):
                file_paths.append(blob.name)
            # If it's a "directory" (ends with a slash)
            else:
                queue.append(blob.name)
    return file_paths


@functions_framework.http
def run_inference(request):
    """HTTP Cloud Function.
    Args:
        a GET HTTP request with 'storage_uri' query parameter
    Returns:
        a HTTP response with the status response
    """

    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and "storage_uri" in request_json:
        storage_uri = request_json["storage_uri"]
    elif request_args and "storage_uri" in request_args:
        storage_uri = request_args["storage_uri"]
    else:
        return json.dumps({"response_text": "No storage_uri provided"})

    logger.log(f"storage_uri for readme : {storage_uri}")

    path_directory = storage_uri.removeprefix("gs://doxygen-gcp-storage/")
    list_files = list_all_file_paths(BUCKET, path_directory)
    file_contents = []
    while len(list_files) > 0:
        file_path = list_files.pop()
        if file_path.endswith(".c") or file_path.endswith(".h"):
            bucket = storage_client.bucket(BUCKET)
            blob = bucket.blob(file_path)
            content = read_file_to_variable(blob)
            file_contents.append((file_path, content))

    response = generate_readme(file_contents)
    if response and hasattr(response, "text"):
        write_variable_to_file(path_directory + "/README.md", response.text)

    status_readme = "OK"

    logger.log(f"README.md created : {status_readme}")

    return json.dumps({"status_readme": status_readme})
