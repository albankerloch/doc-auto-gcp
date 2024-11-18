import os
import subprocess
import uuid
import shutil
import json
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import List

from google.cloud import storage
from flask import Request, jsonify
import functions_framework

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    project_id: str
    bucket_name: str
    doxyfile_name: str = 'Doxyfile'
    local_doxyfile_path: str = '/tmp/Doxyfile'
    gcs_prefixes: List[str] = field(default_factory=lambda: ['doxygen-awesome-css/', 'examples/'])
    local_destinations: List[str] = field(default_factory=lambda: ['/tmp/doxygen-awesome-css/', '/tmp/examples/'])
    doxygen_command: str = '/tmp/doxygen'  # Absolute path to the included binary
    signed_url_expiration_seconds: int = 3600
    doxygen_binary_blob_name: str = 'doxygen'
    docs_output_dir: str = '/tmp/docs'  # Directory where Doxygen outputs documentation
    zip_output_path: str = '/tmp/docs.zip'  # Path to store the zipped documentation
    gcs_docs_prefix: str = 'generated_docs/'  # GCS prefix for uploaded documentation
    service_account_key_blob_name: str = 'doxygen-gcp-cc505b0f3449.json'

def generate_signed_url_with_key(bucket_name: str, blob_name: str, key_file_path: str, expiration: int = 3600) -> str:
    """
    Generates a signed URL using the provided service account key.
    """
    try:
        storage_client = storage.Client.from_service_account_json(key_file_path)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        signed_url = blob.generate_signed_url(expiration=timedelta(seconds=expiration))
        return signed_url
    except Exception as e:
        raise RuntimeError(f"Error generating signed URL for {blob_name}: {str(e)}")

def download_service_account_key(storage_client: storage.Client, bucket_name: str, blob_name: str, local_path: str) -> None:
    """
    Downloads the specified JSON service account key file from GCS.
    """
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(local_path)
        logger.info(f"Service account key file downloaded to {local_path}.")
    except Exception as e:
        raise RuntimeError(f"Error downloading service account key {blob_name}: {str(e)}")

def download_blob(storage_client: storage.Client, bucket_name: str, blob_name: str, local_path: str) -> None:
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(local_path)
    except Exception as e:
        raise RuntimeError(f"Error downloading blob {blob_name}: {str(e)}")

def download_directory(storage_client: storage.Client, bucket_name: str, gcs_prefix: str, local_destination: str) -> None:
    try:
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=gcs_prefix)

        for blob in blobs:
            if blob.name.endswith('/'):
                continue  # Skip directories
            relative_path = os.path.relpath(blob.name, gcs_prefix)
            local_path = os.path.join(local_destination, relative_path)
            local_dir = os.path.dirname(local_path)
            os.makedirs(local_dir, exist_ok=True)
            blob.download_to_filename(local_path)
    except Exception as e:
        raise RuntimeError(f"Error downloading directory with prefix {gcs_prefix}: {str(e)}")

def download_doxygen_binary(storage_client: storage.Client, bucket_name: str, blob_name: str, local_path: str) -> None:
    """
    Downloads the Doxygen binary from GCS and saves it to /tmp, setting execute permissions.
    """
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(local_path)
        # Set execute permissions
        os.chmod(local_path, 0o755)
        logger.info(f"Doxygen binary downloaded to {local_path} and made executable.")
    except Exception as e:
        raise RuntimeError(f"Error downloading Doxygen binary: {str(e)}")

def preprocess_doxyfile(storage_client: storage.Client, bucket_name: str, doxyfile_blob_name: str, local_path: str) -> str:
    try:
        # Download the Doxyfile from GCS
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(doxyfile_blob_name)
        blob.download_to_filename(local_path)
        
        # Read the Doxyfile
        with open(local_path, 'r') as file:
            doxyfile_contents = file.readlines()
        
        # Modify paths in the Doxyfile
        updated_contents = []
        for line in doxyfile_contents:
            # Skip comments and empty lines
            stripped_line = line.strip()
            if stripped_line.startswith('#') or stripped_line == '':
                updated_contents.append(line)
                continue
            
            # Split the line into key and value
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # List of Doxygen tags that may contain paths
                path_tags = [
                    'INPUT',
                    'OUTPUT_DIRECTORY',
                    'HTML_HEADER',
                    'HTML_FOOTER',
                    'LAYOUT_FILE',
                    'IMAGE_PATH',
                    'EXAMPLE_PATH',
                    'INCLUDE_PATH',
                    'STRIP_FROM_PATH',
                    'STRIP_FROM_INC_PATH',
                    'DOT_FONTNAME',
                    'MSCGEN_PATH',
                    'PLANTUML_JAR_PATH',
                    'FILTER_PATTERNS',
                    'FILTER_SOURCE_FILES',
                    'SOURCE_BROWSER',
                    'HTML_EXTRA_STYLESHEET',
                    'HTML_EXTRA_FILES'
                ]
                
                if key in path_tags:
                    # Handle multiple paths separated by spaces
                    paths = value.split()
                    new_paths = []
                    for path in paths:
                        # If path is not absolute, prepend '/tmp/'
                        if not os.path.isabs(path):
                            new_path = os.path.join('/tmp', path)
                            new_paths.append(new_path)
                        else:
                            new_paths.append(path)
                    # Reconstruct the line with updated paths
                    new_value = ' '.join(new_paths)
                    new_line = f'{key} = {new_value}\n'
                    updated_contents.append(new_line)
                else:
                    updated_contents.append(line)
            else:
                updated_contents.append(line)
        
        # Write the modified Doxyfile back to local_path
        with open(local_path, 'w') as file:
            file.writelines(updated_contents)
        
        logger.info(f"Preprocessed Doxyfile saved to {local_path}")
        return local_path
    except Exception as e:
        raise RuntimeError(f"Error during Doxyfile preprocessing: {str(e)}")

def validate_environment(doxygen_cmd: str) -> None:
    if not os.path.isfile(doxygen_cmd) or not os.access(doxygen_cmd, os.X_OK):
        raise EnvironmentError(f"{doxygen_cmd} is not installed or not executable.")
    logger.info(f"Doxygen executable found at {doxygen_cmd}.")

def run_doxygen_command(doxygen_cmd: str, doxyfile_path: str) -> subprocess.CompletedProcess:
    process = subprocess.run(
        [doxygen_cmd, doxyfile_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process

def zip_directory(source_dir: str, zip_path: str) -> None:
    try:
        if os.path.exists(zip_path):
            os.remove(zip_path)  # Remove existing zip if any
        shutil.make_archive(base_name=zip_path.replace('.zip', ''), format='zip', root_dir=source_dir)
        logger.info(f"Directory {source_dir} zipped to {zip_path}.")
    except Exception as e:
        raise RuntimeError(f"Error zipping directory {source_dir}: {str(e)}")

def upload_blob(storage_client: storage.Client, bucket_name: str, source_file: str, destination_blob_name: str) -> None:
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file)
        logger.info(f"File {source_file} uploaded to {destination_blob_name}.")
    except Exception as e:
        raise RuntimeError(f"Error uploading {source_file} to {destination_blob_name}: {str(e)}")

def run_doxygen(config: Config) -> dict:
    try:
        # Initialize the storage client with the project ID
        storage_client = storage.Client(project=config.project_id)

        # Download the Doxygen binary
        doxygen_local_path = '/tmp/doxygen'
        download_doxygen_binary(storage_client, config.bucket_name, config.doxygen_binary_blob_name, doxygen_local_path)
        config.doxygen_command = doxygen_local_path  # Update the command to use the binary in /tmp

        key_local_path = '/tmp/doxygen-gcp-cc505b0f3449.json'
        download_service_account_key(
            storage_client,
            config.bucket_name,
            'doxygen-gcp-cc505b0f3449.json',
            key_local_path
        )

        # Validate environment
        validate_environment(config.doxygen_command)

        # Download specified directories
        for gcs_prefix, local_destination in zip(config.gcs_prefixes, config.local_destinations):
            download_directory(storage_client, config.bucket_name, gcs_prefix, local_destination)

        # Preprocess the Doxyfile
        local_doxyfile_path = preprocess_doxyfile(
            storage_client,
            config.bucket_name,
            config.doxyfile_name,
            config.local_doxyfile_path
        )

        # Run the Doxygen command
        process = run_doxygen_command(config.doxygen_command, local_doxyfile_path)

        # Check for command success
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, config.doxygen_command, output=process.stdout, stderr=process.stderr)

        # Zip the generated documentation
        zip_directory(config.docs_output_dir, config.zip_output_path)

        # Generate a unique name for the zip file in GCS
        unique_id = str(uuid.uuid4())
        gcs_blob_name = f"{config.gcs_docs_prefix}{unique_id}.zip"

        # Upload the zip file to GCS
        upload_blob(storage_client, config.bucket_name, config.zip_output_path, gcs_blob_name)

        # Generate a signed URL for the uploaded zip file
        signed_url = generate_signed_url_with_key(
            bucket_name=config.bucket_name,
            blob_name=gcs_blob_name,
            key_file_path=key_local_path,
            expiration=config.signed_url_expiration_seconds
        )

        return {
            "status": "success",
            "stdout": process.stdout,
            "stderr": process.stderr,
            "docs_signed_url": signed_url
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"Doxygen failed with return code {e.returncode}",
            "stdout": e.output,
            "stderr": e.stderr
        }
    except EnvironmentError as e:
        return {
            "status": "error",
            "message": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }

@functions_framework.http
def run_doxygen_function(request: Request):
    try:
        request_json = request.get_json(silent=True)
        request_args = request.args

        # Extract configuration from the request or use environment variables
        config = Config(
            project_id=request_json.get('project_id') if request_json and 'project_id' in request_json else os.environ.get('PROJECT_ID'),
            bucket_name=request_json.get('bucket_name') if request_json and 'bucket_name' in request_json else os.environ.get('BUCKET_NAME'),
            doxyfile_name=request_json.get('doxyfile_name') if request_json and 'doxyfile_name' in request_json else os.environ.get('DOXYFILE_NAME', 'Doxyfile'),
            local_doxyfile_path=request_json.get('local_doxyfile_path') if request_json and 'local_doxyfile_path' in request_json else os.environ.get('LOCAL_DOXYFILE_PATH', '/tmp/Doxyfile'),
            gcs_prefixes=request_json.get('gcs_prefixes') if request_json and 'gcs_prefixes' in request_json else json.loads(os.environ.get('GCS_PREFIXES', '["doxygen-awesome-css/", "examples/"]')),
            local_destinations=request_json.get('local_destinations') if request_json and 'local_destinations' in request_json else json.loads(os.environ.get('LOCAL_DESTINATIONS', '["/tmp/doxygen-awesome-css/", "/tmp/examples/"]')),
            doxygen_command=request_json.get('doxygen_command') if request_json and 'doxygen_command' in request_json else os.environ.get('DOXYGEN_COMMAND', '/tmp/doxygen'),
            signed_url_expiration_seconds=int(request_json.get('signed_url_expiration_seconds')) if request_json and 'signed_url_expiration_seconds' in request_json else int(os.environ.get('SIGNED_URL_EXPIRATION_SECONDS', '3600')),
            doxygen_binary_blob_name=request_json.get('doxygen_binary_blob_name') if request_json and 'doxygen_binary_blob_name' in request_json else os.environ.get('DOXYGEN_BINARY_BLOB_NAME'),
            docs_output_dir=os.environ.get('DOCS_OUTPUT_DIR', '/tmp/docs'),
            zip_output_path=os.environ.get('ZIP_OUTPUT_PATH', '/tmp/docs.zip'),
            gcs_docs_prefix=os.environ.get('GCS_DOCS_PREFIX', 'generated_docs/')
        )

        # Validate required parameters
        if not config.project_id or not config.bucket_name or not config.doxygen_binary_blob_name or not config.service_account_key_blob_name:
            return jsonify({"status": "error", "message": "Missing required parameters: project_id, bucket_name, doxygen_binary_blob_name, and service_account_key_blob_name"}), 400


        logger.info(f"Starting Doxygen process with config: {config}")

        result = run_doxygen(config)

        if result["status"] == "success":
            logger.info("Doxygen ran successfully.")
            return jsonify({
                "status": "success",
                "message": "Doxygen ran successfully.",
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "docs_signed_url": result["docs_signed_url"]
            }), 200
        else:
            logger.error(f"Doxygen error: {result.get('message')}")
            return jsonify({
                "status": "error",
                "message": result.get("message"),
                "stdout": result.get("stdout"),
                "stderr": result.get("stderr")
            }), 500

    except Exception as e:
        logger.exception("Unhandled error occurred.")
        return jsonify({"status": "error", "message": f"Unhandled error: {str(e)}"}), 500