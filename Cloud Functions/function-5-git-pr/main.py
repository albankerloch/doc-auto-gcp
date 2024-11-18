import os
import time
import tempfile
import re
import jwt  # PyJWT
from datetime import datetime
from flask import jsonify, request
from github import Github, GithubException, GithubIntegration  # Added GithubIntegration
from google.cloud import logging, storage
from functions_framework import http

# Constants
PROJECT_ID = "doxygen-gcp"
LOG_NAME = "run_inference-cloudfunction-log"
GITHUB_APP_ID = "1061506"  # GitHub App ID
GITHUB_PRIVATE_KEY = (
    "code-documenter.2024-11-17.private-key.pem"  # GitHub App Private Key
)
GCS_BUCKET_NAME = "doxygen-gcp-storage"  # GCS Bucket name

# Set up logging
client = logging.Client(project=PROJECT_ID)
client.setup_logging()
logger = client.logger(LOG_NAME)


@http
def run_inference(request):
    """
    Entry point for the Cloud Function.
    Downloads files from GCS and creates a pull request on a GitHub repository.
    Args:
        request: Flask request object.
    Returns:
        JSON response with a status and PR URL if successful.
    """
    logger.log_text("Received request for run_inference.", severity="INFO")

    try:
        # Step 1: Extract and parse the storage URI
        logger.log_text("Extracting storage URI from the request.", severity="INFO")
        storage_uri = extract_storage_uri(request)
        logger.log_text(f"Storage URI extracted: {storage_uri}", severity="INFO")

        bucket_name, directory_path = parse_storage_uri(storage_uri)
        logger.log_text(
            f"Parsed storage URI. Bucket: {bucket_name}, Directory Path: {directory_path}",
            severity="INFO",
        )

        # Step 2: Extract GitHub repository information from request
        logger.log_text(
            "Extracting GitHub repository information from the request.",
            severity="INFO",
        )
        repo_payload = request.get_json(silent=True)

        if not repo_payload:
            logger.log_text("Request JSON payload is missing.", severity="ERROR")
            raise ValueError("Invalid request: JSON payload is missing.")

        repo_owner = repo_payload.get("repo_owner")
        repo_name = repo_payload.get("repo_name")

        if not repo_owner or not repo_name:
            logger.log_text(
                "Missing repo_owner or repo_name in the request payload.",
                severity="ERROR",
            )
            raise ValueError(
                "repo_owner and repo_name are required in the request payload."
            )

        logger.log_text(
            f"Target repository details extracted. Owner: {repo_owner}, Name: {repo_name}",
            severity="INFO",
        )

        # Step 3: Generate JWT and retrieve private key
        logger.log_text(
            "Generating JWT token and retrieving private key.", severity="INFO"
        )
        jwt_token, private_key = generate_jwt_token(return_private_key=True)
        logger.log_text(
            "JWT token and private key retrieved successfully.", severity="INFO"
        )

        # Step 4: Initialize GitHub Integration
        logger.log_text("Initializing GitHub Integration.", severity="INFO")
        integration = GithubIntegration(GITHUB_APP_ID, private_key)

        # Step 5: Get installation ID
        logger.log_text(
            f"Authenticating GitHub App for repository {repo_owner}/{repo_name}.",
            severity="INFO",
        )
        installation_id = get_installation_id(integration, repo_owner, repo_name)
        logger.log_text(f"Installation ID fetched: {installation_id}", severity="INFO")

        # Step 6: Fetch installation access token
        logger.log_text(
            "Fetching installation access token using installation ID.", severity="INFO"
        )
        installation_token = get_installation_access_token(integration, installation_id)
        logger.log_text(
            "Installation access token retrieved successfully.", severity="INFO"
        )

        # Step 7: Reinitialize GitHub client with installation token
        logger.log_text(
            "Reinitializing GitHub client with the installation token.", severity="INFO"
        )
        github = Github(installation_token)

        # Step 8: Download files from GCS directory
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.log_text(
                f"Preparing to download files from GCS. Directory: {directory_path}, Temporary Path: {temp_dir}",
                severity="INFO",
            )
            download_directory(storage.Client(), bucket_name, directory_path, temp_dir)
            logger.log_text(
                f"Files successfully downloaded to temporary directory: {temp_dir}",
                severity="INFO",
            )

            # Step 9: Create a GitHub Pull Request
            branch_name = f"update-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            logger.log_text(
                f"Creating a new branch and generating pull request. Branch name: {branch_name}",
                severity="INFO",
            )
            pr_url = create_git_pull_request(
                github, repo_owner, repo_name, temp_dir, branch_name
            )
            logger.log_text(
                f"Pull Request created successfully. PR URL: {pr_url}", severity="INFO"
            )

        # Step 10: Return the Pull Request URL
        logger.log_text(
            "Run inference process completed successfully.", severity="INFO"
        )
        return jsonify({"status": "success", "pull_request_url": pr_url})

    except ValueError as ve:
        logger.log_text(f"Validation error: {str(ve)}", severity="ERROR")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logger.log_text(
            f"Unexpected error in run_inference: {str(e)}", severity="ERROR"
        )
        return jsonify({"status": "error", "message": str(e)}), 500


def generate_jwt_token(return_private_key=False):
    """
    Generates a JWT for the GitHub App and optionally returns the private key.
    Args:
        return_private_key (bool): Whether to return the private key along with the JWT.
    Returns:
        str: JWT token.
        (Optional) str: Private key if return_private_key is True.
    """
    try:
        logger.log_text("Starting JWT token generation process.", severity="INFO")

        with tempfile.NamedTemporaryFile(suffix=".pem", delete=True) as temp_key_file:
            logger.log_text(
                "Temporary file created for storing the GitHub private key.",
                severity="INFO",
            )

            # Download GitHub private key from GCS
            logger.log_text(
                f"Downloading private key from GCS bucket: {GCS_BUCKET_NAME}, blob: {GITHUB_PRIVATE_KEY}.",
                severity="INFO",
            )
            download_github_private_key(
                storage_client=storage.Client(),
                bucket_name=GCS_BUCKET_NAME,
                blob_name=GITHUB_PRIVATE_KEY,
                local_path=temp_key_file.name,
            )
            logger.log_text(
                f"Private key successfully downloaded to temporary file: {temp_key_file.name}.",
                severity="INFO",
            )

            # Read the private key
            with open(temp_key_file.name, "r") as key_file:
                logger.log_text(
                    "Reading private key from temporary file.", severity="INFO"
                )
                private_key = key_file.read()

            # Generate the JWT token
            payload = {
                "iat": int(time.time()),  # Issued at time
                "exp": int(time.time()) + (10 * 60),  # Expires after 10 minutes
                "iss": GITHUB_APP_ID,  # GitHub App ID
            }
            logger.log_text(
                f"Payload for JWT token created: {payload}", severity="DEBUG"
            )

            jwt_token = jwt.encode(payload, private_key, algorithm="RS256")
            logger.log_text("JWT token successfully generated.", severity="INFO")

            if return_private_key:
                return jwt_token, private_key
            return jwt_token
    except Exception as e:
        logger.log_text(f"Error generating JWT token: {str(e)}", severity="ERROR")
        raise RuntimeError(f"JWT generation failed: {str(e)}")


def create_git_pull_request(github, repo_owner, repo_name, local_path, branch_name):
    """
    Orchestrates the creation of a GitHub Pull Request with the files in the specified local path.
    Args:
        github: Authenticated PyGithub instance.
        repo_owner (str): Owner of the target repository.
        repo_name (str): Name of the target repository.
        local_path (str): Path to the local directory containing files to commit.
        branch_name (str): Name of the branch for the PR.
    Returns:
        str: URL of the created Pull Request.
    """
    try:
        full_repo_name = f"{repo_owner}/{repo_name}"
        repo, default_branch = get_repository(github, full_repo_name)
        create_branch(repo, branch_name, default_branch)
        upload_files_to_branch(repo, local_path, branch_name)
        pr_url = create_pull_request(repo, branch_name, default_branch)
        return pr_url
    except Exception as e:
        logger.log_text(f"Error creating Pull Request: {str(e)}", severity="ERROR")
        raise


def get_installation_id(integration, repo_owner, repo_name):
    """
    Fetches the installation ID for the GitHub App on the specified repository.
    Args:
        integration: Authenticated GithubIntegration instance.
        repo_owner (str): Owner of the repository.
        repo_name (str): Name of the repository.
    Returns:
        int: Installation ID of the GitHub App.
    """
    try:
        installation = integration.get_installation(repo_owner, repo_name)
        return installation.id
    except GithubException as e:
        if e.status == 401:
            raise RuntimeError(f"Authentication failed: {str(e)}")
        elif e.status == 404:
            raise RuntimeError(
                f"GitHub App is not installed on {repo_owner}/{repo_name}."
            )
        else:
            raise RuntimeError(
                f"Unexpected error while fetching installation ID: {str(e)}"
            )
    except Exception as e:
        raise RuntimeError(f"Error fetching installation ID: {str(e)}")


def get_installation_access_token(integration, installation_id):
    """
    Generates an access token for the specified installation ID.
    Args:
        integration: Authenticated GithubIntegration instance.
        installation_id (int): Installation ID of the GitHub App.
    Returns:
        str: Installation access token.
    """
    try:
        access_token = integration.get_access_token(installation_id)
        logger.log_text(
            f"Retrieved installation token for installation ID {installation_id}"
        )
        return access_token.token
    except Exception as e:
        logger.error(f"Error generating installation token: {e}")
        raise


def get_repository(github, full_repo_name):
    """
    Retrieves the target repository and checks write access.
    Args:
        github: Authenticated PyGithub instance.
        full_repo_name (str): Full name of the repository (owner/repo).
    Returns:
        tuple: (Repository object, default branch name)
    """
    try:
        repo = github.get_repo(full_repo_name)
        default_branch = repo.default_branch
        logger.log_text(
            f"Access confirmed for repository: {full_repo_name}", severity="INFO"
        )
        return repo, default_branch
    except GithubException as e:
        logger.log_text(
            f"Error accessing repository {full_repo_name}: {str(e)}", severity="ERROR"
        )
        raise RuntimeError(f"Error accessing repository {full_repo_name}: {str(e)}")


def create_branch(repo, branch_name, default_branch):
    """
    Creates a new branch in the repository based on the default branch.
    Args:
        repo: PyGithub repository object.
        branch_name (str): Name of the branch to create.
        default_branch (str): Name of the default branch to base the new branch on.
    """
    try:
        branch_ref = f"refs/heads/{branch_name}"
        sha = repo.get_branch(default_branch).commit.sha
        repo.create_git_ref(ref=branch_ref, sha=sha)
        logger.log_text(
            f"Created new branch: {branch_name} in repository: {repo.full_name}"
        )
    except GithubException as e:
        raise RuntimeError(f"Error creating branch {branch_name}: {str(e)}")


def validate_and_sanitize_path(relative_path):
    """
    Validates and sanitizes the relative path to ensure it complies with GitHub's requirements.
    Args:
        relative_path (str): The file path relative to the repository root.
    Returns:
        str: A sanitized path if valid.
    Raises:
        ValueError: If the path is invalid.
    """
    # Define a regex pattern for valid GitHub paths
    # This pattern allows alphanumeric characters, underscores, hyphens, dots, and slashes
    pattern = re.compile(r"^(?!.*//)(?!/)(?!.*\.\./)(?!\.git/)[A-Za-z0-9_\-./ ]+$")

    if not pattern.match(relative_path):
        raise ValueError(f"Invalid file path: {relative_path}")

    # Additional sanitization if needed
    sanitized_path = relative_path.replace("\\", "/")

    return sanitized_path


def upload_files_to_branch(repo, local_path, branch_name):
    """
    Uploads files from the local path to the specified branch in the repository.
    Excludes hidden directories (e.g., .git) to prevent uploading Git's internal files.
    """
    try:
        for root, dirs, files in os.walk(local_path):
            # Exclude hidden directories (starting with a dot)
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for file_name in files:
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, local_path)

                # Skip hidden files (starting with a dot)
                if relative_path.startswith(".") or "/." in relative_path:
                    logger.log_text(
                        f"Skipping hidden file: {relative_path}", severity="INFO"
                    )
                    continue  # Skip hidden files

                # Validate and sanitize the path
                try:
                    relative_path = validate_and_sanitize_path(relative_path)
                except ValueError as ve:
                    logger.log_text(
                        f"Skipping invalid file path: {relative_path}. Reason: {ve}",
                        severity="WARNING",
                    )
                    continue  # Skip invalid paths

                # Log the sanitized path
                logger.log_text(
                    f"Uploading file with sanitized relative path: {relative_path}",
                    severity="DEBUG",
                )

                # Read the file content
                with open(file_path, "rb") as file:
                    content = file.read()

                # Proceed with upload as before...
                try:
                    existing_file = repo.get_contents(relative_path, ref=branch_name)
                    # Update the existing file
                    repo.update_file(
                        path=relative_path,
                        message=f"Update {relative_path}",
                        content=content,
                        sha=existing_file.sha,
                        branch=branch_name,
                    )
                    logger.log_text(
                        f"Updated file in branch {branch_name}: {relative_path}"
                    )
                except GithubException as e:
                    if e.status == 404:
                        repo.create_file(
                            path=relative_path,
                            message=f"Add {relative_path}",
                            content=content,
                            branch=branch_name,
                        )
                        logger.log_text(
                            f"Created new file in branch {branch_name}: {relative_path}"
                        )
                    else:
                        raise
    except GithubException as e:
        raise RuntimeError(f"Error uploading files to branch {branch_name}: {str(e)}")


def create_pull_request(repo, branch_name, default_branch):
    """
    Creates a pull request in the repository.
    Args:
        repo: PyGithub repository object.
        branch_name (str): Source branch for the pull request.
        default_branch (str): Target branch for the pull request.
    Returns:
        str: URL of the created pull request.
    """
    try:
        pr = repo.create_pull(
            title=f"Update from {branch_name}",
            body="Automated update from run_inference function.",
            head=branch_name,  # Since we are pushing to the same repo, head is just the branch name
            base=default_branch,
        )
        logger.log_text(f"Pull Request created: {pr.html_url}")
        return pr.html_url
    except GithubException as e:
        raise RuntimeError(f"Error creating pull request: {str(e)}")


# Utility Functions
def extract_storage_uri(request):
    """
    Extracts 'storage_uri' from the request JSON or query parameters.
    Args:
        request: Flask request object.
    Returns:
        str: The 'storage_uri' value.
    """
    request_json = request.get_json(silent=True)
    storage_uri = (
        request_json.get("storage_uri")
        if request_json
        else request.args.get("storage_uri")
    )

    if not storage_uri:
        logger.log_text("No storage_uri provided in request.", severity="ERROR")
        raise ValueError("storage_uri parameter is required.")
    return storage_uri


def parse_storage_uri(storage_uri):
    """
    Parses the storage URI into bucket name and directory path.
    Args:
        storage_uri (str): The GCS URI.
    Returns:
        tuple: (bucket_name, directory_path)
    """
    try:
        if not storage_uri.startswith("gs://"):
            raise ValueError(
                "Invalid storage_uri format. Expected format: gs://bucket_name/path/to/object"
            )
        parts = storage_uri.split("/")
        bucket_name = parts[2]
        directory_path = "/".join(parts[3:])
        return bucket_name, directory_path
    except IndexError:
        logger.log_text(f"Invalid storage_uri format: {storage_uri}", severity="ERROR")
        raise ValueError(
            "Invalid storage_uri format. Expected format: gs://bucket_name/path/to/object"
        )


def download_github_private_key(
    storage_client: storage.Client, bucket_name: str, blob_name: str, local_path: str
) -> None:
    """
    Downloads the specified GitHub private key file from a Google Cloud Storage (GCS) bucket.
    Args:
        storage_client (storage.Client): The Google Cloud Storage client instance.
        bucket_name (str): The name of the GCS bucket.
        blob_name (str): The name of the blob (file) to download.
        local_path (str): The local file path where the private key will be saved.
    Raises:
        RuntimeError: If there is an error during the download process.
    """
    try:
        logger.log_text(
            f"Initiating download of GitHub private key: {blob_name} from bucket: {bucket_name}."
        )

        # Access the bucket
        bucket = storage_client.bucket(bucket_name)

        # Access the blob (file) within the bucket
        blob = bucket.blob(blob_name)

        # Download the blob to the specified local file path
        blob.download_to_filename(local_path)

        logger.log_text(
            f"GitHub private key file successfully downloaded to {local_path}."
        )
    except Exception as e:
        logger.error(
            f"Failed to download GitHub private key: {blob_name} from bucket: {bucket_name}."
        )
        raise RuntimeError(
            f"Error downloading GitHub private key {blob_name}: {str(e)}"
        )


def download_directory(storage_client, bucket_name, gcs_prefix, local_destination):
    """
    Downloads all files from a GCS directory to a local destination.
    Args:
        storage_client (google.cloud.storage.Client): The GCS storage client.
        bucket_name (str): Name of the GCS bucket.
        gcs_prefix (str): Prefix of the directory to download.
        local_destination (str): Local path where files should be downloaded.
    """
    try:
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=gcs_prefix)

        for blob in blobs:
            if blob.name.endswith("/"):
                continue  # Skip directories
            relative_path = os.path.relpath(blob.name, gcs_prefix)
            local_path = os.path.join(local_destination, relative_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            blob.download_to_filename(local_path)
            logger.log_text(f"Downloaded {blob.name} to {local_path}")
    except Exception as e:
        logger.log_text(f"Failed to download directory: {str(e)}", severity="ERROR")
        raise RuntimeError(
            f"Error downloading directory with prefix {gcs_prefix}: {str(e)}"
        )
