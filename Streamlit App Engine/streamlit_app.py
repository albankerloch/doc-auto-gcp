import streamlit as st
import requests

def Download_Response(url_git):
    response = requests.get("https://europe-west1-doxygen-gcp.cloudfunctions.net/function-1-download?url=" + url_git)
    return response.json()["storage_uri"]

st.title("Documentation automatique")

url_git = st.text_input("Saisir l'url de votre répo git public :")

btn_download = st.button("Télécharger sur Cloud Storage")

if btn_download and url_git:
    result = Download_Response(url_git)
    st.subheader("Téléchargement dans : ")
    st.text(result)