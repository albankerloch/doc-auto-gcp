import os
import json
import functions_framework
import vertexai

from google.cloud import logging
from vertexai.preview.generative_models import GenerativeModel, Part

PROJECT_ID = "doxygen-gcp"
LOCATION = "europe-west1"
BUCKET = "doxygen-gcp-storage"

client = logging.Client(project=PROJECT_ID)
client.setup_logging()

LOG_NAME = "run_inference-cloudfunction-download-log"
logger = client.logger(LOG_NAME)

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

    storage_uri = "to do"

    logger.log(f"Git repository downloaded a: {storage_uri}")

    return json.dumps({"storage_uri": storage_uri})