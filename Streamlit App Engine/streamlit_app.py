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
