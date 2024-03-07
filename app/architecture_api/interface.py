import streamlit as st
import requests
import json
from dotenv import load_dotenv


load_dotenv("secret_url")

# Online URL Azure function
# azure_function_url = os.getenv("AZURE_FUNCTION_URL")

# Local Url Azure function
azure_function_url = "http://localhost:7071/api/http_reco_system"

# Get csv file, pickle file and user_id as input
user_id = st.text_input('Enter your user_id')
csv_file = st.file_uploader("Choose your CSV file", type=['csv'])
pickle_file = st.file_uploader("Choose your .pickle file", type=['pickle'])

st.markdown("---")

if csv_file and pickle_file and user_id:
    # Prepare the data to send
    files = {
        'csv_file': csv_file.getvalue(),
        'pickle_file': pickle_file.getvalue(),
    }

    # Send csv file and pickle file to the URL
    response = requests.post(f'{azure_function_url}?user_id={user_id}', files=files)

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