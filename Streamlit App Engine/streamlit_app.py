import streamlit as st
import requests
import json


def Download_Response(url_git):
    response = requests.get(
        "https://europe-west1-doxygen-gcp.cloudfunctions.net/function-1-download?url="
        + url_git
    )
    return response.json()["storage_uri"]


def comment_text(path):
    response = requests.post(
        "https://europe-west1-doxygen-gcp.cloudfunctions.net/function-3-comment",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"storage_uri": "gs://doxygen-gcp-storage/" + path}),
        timeout=3600,
    )
    return response.json()["status_comment"]


def create_readme(path):
    response = requests.post(
        "https://europe-west1-doxygen-gcp.cloudfunctions.net/function-2-readme",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"storage_uri": "gs://doxygen-gcp-storage/" + path}),
        timeout=3600,
    )
    return response.json()["status_readme"]


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


st.title("Documentation automatique")

url_git = st.text_input("Saisir l'url de votre répo git public :")

btn_download = st.button("Télécharger sur Cloud Storage")

if btn_download and url_git:
    result = Download_Response(url_git)
    st.subheader("Téléchargement dans : ")
    st.text(result)

    comment = comment_text(result)
    st.subheader("Commentaire : ")
    st.text(comment)

    create_readme = create_readme(result)
    st.subheader("Readme : ")
    st.text(create_readme)

    create_doc_html = create_doc_html(result)
    st.subheader("Documentation HTML : ")
    st.text(create_doc_html)
