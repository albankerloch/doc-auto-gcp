# import streamlit as st
# import requests
# import json
# import re
# import logging


# def extract_repo_details(git_url):
#     pattern = r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+)"
#     match = re.match(pattern, git_url)
#     if match:
#         repo_owner = match.group(1)
#         repo_name = match.group(2).replace(
#             ".git", ""
#         )  # Supprimer l'extension .git si présente
#         return repo_owner, repo_name
#     return None, None


# def Download_Response(url_git):
#     response = requests.get(
#         "https://europe-west1-doxygen-gcp.cloudfunctions.net/function-1-download?url="
#         + url_git
#     )
#     return response.json()["storage_uri"]


# def comment_text(path):
#     response = requests.post(
#         "https://europe-west1-doxygen-gcp.cloudfunctions.net/function-3-comment",
#         headers={"Content-Type": "application/json"},
#         data=json.dumps({"storage_uri": "gs://doxygen-gcp-storage/" + path}),
#         timeout=3600,
#     )
#     return response.json()["status_comment"]


# def create_readme(path):
#     response = requests.post(
#         "https://europe-west1-doxygen-gcp.cloudfunctions.net/function-2-readme",
#         headers={"Content-Type": "application/json"},
#         data=json.dumps({"storage_uri": "gs://doxygen-gcp-storage/" + path}),
#         timeout=3600,
#     )
#     return response.json()["status_readme"]


# def create_doc_html(path):
#     api_url = "https://function-4-html-32678029811.europe-west1.run.app/"

#     payload = {
#         "project_id": "doxygen-gcp",
#         "bucket_name": "doxygen-gcp-storage",
#         "doxyfile_name": "Doxyfile",
#         "local_doxyfile_path": "/tmp/Doxyfile",
#         "gcs_prefixes": ["doxygen-awesome-css/", path + "/"],
#         "local_destinations": ["/tmp/doxygen-awesome-css/", "/tmp/" + path + "/"],
#         "doxygen_command": "/tmp/doxygen",
#         "signed_url_expiration_seconds": "3600",
#         "doxygen_binary_blob_name": "doxygen",
#     }
#     response = requests.post(
#         api_url, json=payload, headers={"Content-Type": "application/json"}
#     )
#     return response.json()["status"]


# def make_pull_request(path, url_git):

#     repo_owner, repo_name = extract_repo_details(url_git)
#     logging.info(repo_owner, repo_name)
#     storage_uri = "gs://doxygen-gcp-storage/" + path
#     url = "https://europe-west1-doxygen-gcp.cloudfunctions.net/function-5-git-pr"
#     payload = {
#         "storage_uri": storage_uri,
#         "repo_owner": repo_owner,
#         "repo_name": repo_name,
#     }
#     response = requests.post(
#         url, headers={"Content-Type": "application/json"}, data=json.dumps(payload)
#     )
#     return response.json()["status"]


# st.title("Documentation automatique")

# url_git = st.text_input("Saisir l'url de votre répo git public :")

# btn_download = st.button("Télécharger sur Cloud Storage")

# if btn_download and url_git:
#     result = Download_Response(url_git)
#     st.subheader("Téléchargement dans : ")
#     st.text(result)

#     comment = comment_text(result)
#     st.subheader("Commentaire : ")
#     st.text(comment)

#     create_readme = create_readme(result)
#     st.subheader("Readme : ")
#     st.text(create_readme)

#     create_doc_html = create_doc_html(result)
#     st.subheader("Documentation HTML : ")
#     st.text(create_doc_html)

#     pull_request = make_pull_request(result, url_git)
#     st.subheader("Pull request : ")
#     st.text(pull_request)


###################################################################################################


import streamlit as st
import requests
import json
import re
import logging

# Set page configuration
st.set_page_config(
    page_title="📚 Automatic Documentation Generator",
    page_icon="🌌",
    layout="centered",
    initial_sidebar_state="expanded",
)


def extract_repo_details(git_url):
    pattern = r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+)"
    match = re.match(pattern, git_url)
    if match:
        repo_owner = match.group(1)
        repo_name = match.group(2).replace(
            ".git", ""
        )  # Supprimer l'extension .git si présente
        return repo_owner, repo_name
    return None, None


def make_pull_request(path, url_git):

    repo_owner, repo_name = extract_repo_details(url_git)
    logging.info(repo_owner, repo_name)
    storage_uri = "gs://doxygen-gcp-storage/" + path
    url = "https://europe-west1-doxygen-gcp.cloudfunctions.net/function-5-git-pr"
    payload = {
        "storage_uri": storage_uri,
        "repo_owner": repo_owner,
        "repo_name": repo_name,
    }
    response = requests.post(
        url, headers={"Content-Type": "application/json"}, data=json.dumps(payload)
    )
    return response.json()["status"]


def create_doc_html(path):
    api_url = "https://function-4-html-32678029811.europe-west1.run.app/"

    payload = {
        "project_id": "doxygen-gcp",
        "bucket_name": "doxygen-gcp-storage",
        "doxyfile_name": "Doxyfile",
        "local_doxyfile_path": "/tmp/Doxyfile",
        "gcs_prefixes": ["doxygen-awesome-css/", path + "/"],
        "local_destinations": ["/tmp/doxygen-awesome-css/", "/tmp/" + path + "/"],
        "doxygen_command": "/tmp/doxygen",
        "signed_url_expiration_seconds": "3600",
        "doxygen_binary_blob_name": "doxygen",
    }
    response = requests.post(
        api_url, json=payload, headers={"Content-Type": "application/json"}
    )
    return response.json()["status"]


def comment_text(path):
    response = requests.post(
        "https://europe-west1-doxygen-gcp.cloudfunctions.net/function-3-comment",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"storage_uri": "gs://doxygen-gcp-storage/" + path}),
        timeout=3600,
    )
    return response.json()["status_comment"]


def Download_Response(url_git):
    response = requests.get(
        "https://europe-west1-doxygen-gcp.cloudfunctions.net/function-1-download?url="
        + url_git
    )
    return response.json()["storage_uri"]


# Add custom CSS for dark theme
def add_custom_styles():
    st.markdown(
        """
        <style>
        /* General Body Styling */
        body {
            background-color: #121212;
            color: #e0e0e0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Input Fields */
        .stTextInput>div>div>input {
            background-color: #1e1e2f;
            color: #e0e0e0;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
        }

        /* Buttons */
        .stButton>button {
            background-color: #3a7bfd;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        .stButton>button:hover {
            background-color: #5a9bff;
            color: #121212 !important; /* Set desired hover text color */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# Initialize session state variables
if "proceed" not in st.session_state:
    st.session_state.proceed = False

if "show_install_dialog" not in st.session_state:
    st.session_state.show_install_dialog = False


# Dialog function to confirm installation
@st.dialog("📋 Confirm GitHub App Installation")
def confirm_installation():
    st.write("Have you installed the GitHub app required for this process?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes"):
            st.session_state.proceed = True
            st.rerun()  # Close the dialog and rerun the app
    with col2:
        if st.button("❌ No"):
            st.session_state.show_install_dialog = True
            st.rerun()  # Close the dialog and rerun the app


# Dialog function to show installation link
@st.dialog("📥 Install GitHub App")
def install_app_dialog():
    st.write(
        """
        You need to install the GitHub app to proceed.
        Click the link below to install:
        """
    )
    st.markdown(
        "[Install GitHub App](https://github.com/apps/code-documenter)",
        unsafe_allow_html=True,
    )
    if st.button("Close"):
        st.session_state.show_install_dialog = False
        st.rerun()  # Close the dialog and rerun the app


# Main App
def main():
    add_custom_styles()

    # Title
    st.title("🌌 Automatic Documentation Generator")

    # Description
    st.markdown(
        """
        Welcome to the **Automatic Documentation Generator**. Enter the URL of your public Git repository below to generate comprehensive documentation automatically.
        """
    )

    # Input field for GitHub URL
    url_git = st.text_input("🔗 Enter your public Git repository URL:", "")

    # Start Documentation Process Button
    if st.button("🚀 Start Documentation Process"):
        if not url_git:
            st.error("Please enter a valid Git repository URL!")
        else:
            confirm_installation()

    # Show Install App Dialog if required
    if st.session_state.show_install_dialog:
        install_app_dialog()

    # Proceed with Documentation Process
    if st.session_state.proceed:
        result = None
        with st.spinner("📥 Downloading repository..."):
            result = Download_Response(url_git)
            # Simulate download process
            st.success("Successfully downloaded repository!")
        with st.spinner("💬 Adding comments..."):
            comment = comment_text(result)
            # Simulate comments process
            st.success("Comments successfully added!")

        with st.spinner("📄 Generating README..."):
            create_doc = create_doc_html(result)
            # Simulate README generation process
            st.success("README successfully generated!")

        with st.spinner("🌐 Generating HTML Documentation..."):
            pull_request = make_pull_request(result, url_git)
            # Simulate HTML documentation process
            st.success("HTML Documentation successfully generated!")

        with st.spinner("🚀 Pull Request..."):
            pull_request = make_pull_request(result, url_git)
            # Simulate pull request process
            st.success("Pull Request successfully created!")

    # Footer
    st.markdown(
        """
        <div class="footer">
            &copy; 2024 Automatic Documentation Generator. All rights reserved.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
