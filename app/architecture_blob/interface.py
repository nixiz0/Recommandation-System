import os
import pandas as pd
import streamlit as st
import requests
import json
from io import BytesIO
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv


load_dotenv("secret_url")
blob_key = os.getenv("BLOB_STORAGE")

# URL Azure function
azure_function_url = os.getenv("AZURE_FUNCTION_URL")
# azure_function_url = 'http://localhost:7071/api/http_reco_system'

# Create a blob service client
blob_service_client = BlobServiceClient.from_connection_string(blob_key)

# Get the blob client for the CSV file
csv_blob_client = blob_service_client.get_blob_client("embed-csv", "click_sample_info.csv")

# Download the CSV file
csv_blob = csv_blob_client.download_blob().readall()
df = pd.read_csv(BytesIO(csv_blob))

# Display the list of all user_id in a select box
user_id = st.selectbox('Select your user_id', df['user_id'].unique())

if user_id:
    # Send user_id to the URL
    response = requests.post(f'{azure_function_url}&user_id={user_id}')

    # Check if the request was successful
    if response.status_code == 200:
        # Get the returned values
        data = response.json()

        # If the data is a list, display each item as a recommended article
        if isinstance(data, list):
            st.write("## Recommended Articles")
            for i, article in enumerate(data):
                st.write(f"Article : {article}")
        else:
            # If the data is not a list, display it as formatted JSON
            st.write(json.dumps(data, indent=4))
    else:
        st.write("An error occurred while retrieving data.")