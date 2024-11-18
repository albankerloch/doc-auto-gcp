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


def read_file_to_variable_intern(file_path):
    """Reads a file from the same directory as the script."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()
        return file_content
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None


# Assuming 'test.c' and 'test2.c' are in the same directory as this script
INPUT_1 = read_file_to_variable_intern("test.c")
OUTPUT_1 = read_file_to_variable_intern("test2.c")
INPUT_2 = read_file_to_variable_intern("user_manager.h")
OUTPUT_2 = read_file_to_variable_intern("user_manager2.h")
INPUT_3 = read_file_to_variable_intern("ft_atoi.c")
OUTPUT_3 = read_file_to_variable_intern("ft_atoi2.c")
INPUT_4 = read_file_to_variable_intern("philo_one.h")
OUTPUT_4 = read_file_to_variable_intern("philo_one2.h")
INPUT_5 = read_file_to_variable_intern("struct.c")
OUTPUT_5 = read_file_to_variable_intern("struct2.c")


def read_file_to_variable(blob):
    with blob.open("r") as f:
        file_content = f.read()
        return file_content


def useGemini(file_content, delay=2):
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel("gemini-1.5-pro")
    try:
        response = model.generate_content(
            f"""
            Voici un fichier contenant du code source. Analyse le code pour identifier les signatures des structures, fonctions, typedef, définitions et énumérations.
            Ton objectif est simplement d'ajouter des commentaires explicatifs au-dessus de ces signatures pour les documenter, en utilisant un format compatible avec Doxygen. Ne modifie pas le code source lui-même.
            Instructions pour les commentaires :
            - Chaque commentaire doit être au format Doxygen.
            - Inclure uniquement les balises nécessaires comme @file au début du fichier.
            - Trés important de rajouter la balise @file dans chaque fichier.
            - Ne pas utiliser les balises @author, @var ou @date.
            - Place les commentaires **au-dessus de chaque signature concernée**.
            - Ne donne pas de recommandations.
            - quand tu écrit ne rajoute pas de ```cpp ``` ou ```c``` devant le code source car aprés je réécris tous dans un fichier .c ou .h
            Code source à analyser :
            {file_content}
            Je te donne des exemples:
            INPUT {INPUT_1} OUTPUT {OUTPUT_1}
            INPUT {INPUT_2} OUTPUT {OUTPUT_2}
            INPUT {INPUT_3} OUTPUT {OUTPUT_3}
            INPUT {INPUT_4} OUTPUT {OUTPUT_4}
            INPUT {INPUT_5} OUTPUT {OUTPUT_5}
            """
        )
        time.sleep(delay)
        return response.text
    except ValueError as e:
        time.sleep(delay)  # Attendre avant de réessayer
        return None
        # return useGemini(file_content)


def write_file_to_variable(path, content):
    bucket = storage_client.bucket(BUCKET)
    blob = bucket.blob(path)
    with blob.open("w") as f:
        f.write(content)


def delete_file_from_bucket(path):
    bucket = storage_client.bucket(BUCKET)
    blob = bucket.blob(path)
    blob.delete()
    print(f"File {path} deleted from bucket {BUCKET}")


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
        lala
    """

    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and "storage_uri" in request_json:
        storage_uri = request_json["storage_uri"]
    elif request_args and "storage_uri" in request_args:
        storage_uri = request_args["storage_uri"]
    else:
        return json.dumps({"status_comment": "no_storage_uri_provided"})

    logger.log(f"storage_uri for comment : {storage_uri}")

    status_comment = "to do"

    path_directory = storage_uri.removeprefix("gs://doxygen-gcp-storage/")

    list_files = list_all_file_paths(BUCKET, path_directory)
    while len(list_files) > 0:
        file_path = list_files.pop()
        if file_path.endswith(".c") or file_path.endswith(".h"):
            bucket = storage_client.bucket(BUCKET)
            blob = bucket.blob(file_path)
            file_content = read_file_to_variable(blob)
            response = useGemini(file_content)
            if response is not None:
                delete_file_from_bucket(file_path)
                write_file_to_variable(file_path, response)
    # logger.log(f"Comments created : {response.text}")
    status_comment = "ok"

    return json.dumps({"status_comment": status_comment})
