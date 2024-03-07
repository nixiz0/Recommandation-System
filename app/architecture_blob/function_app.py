from io import BytesIO
import json
import os
import pickle
import azure.functions as func
import numpy as np
import pandas as pd
import logging
from operator import itemgetter
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv


app = func.FunctionApp()
load_dotenv('.azure_secret')
secret_key = os.getenv("CO_BLOB_STORAGE")

class ArticleRecommender:
    # Initialize the class with article embeddings
    def __init__(self, embeddings, df_clicks):
        self.embeddings = embeddings
        self.df_clicks = df_clicks

    # Method to recommend articles
    def recommend_articles(self, article_index, n_recommendations):
        # List to store similarity scores
        similarity_scores = []

        # Loop through all embeddings
        for i in range(len(self.embeddings)):
            # Don't compare the article with itself
            if i != article_index:
                # Compute the cosine similarity between the given article and the current article
                similarity = np.dot(self.embeddings[article_index], self.embeddings[i]) / (np.linalg.norm(self.embeddings[article_index]) * np.linalg.norm(self.embeddings[i]))
                # Add the similarity score to the list
                similarity_scores.append(similarity)

        # Associate each score with its index
        indexed_scores = list(enumerate(similarity_scores))
        # Sort the scores (and their indices) in descending order
        sorted_scores = sorted(indexed_scores, key=itemgetter(1), reverse=True)
        # Get the indices of the top n_recommendations scores
        top_scores_indices = [score[0] for score in sorted_scores[:n_recommendations]]

        # Return the indices of the recommended articles
        return top_scores_indices
    
    def get_recommended_articles(self, user_id):
        # Filter clicks from the specified user
        user_clicks = self.df_clicks[self.df_clicks['user_id'] == int(user_id)]

        # Check if user_clicks is not empty
        if not user_clicks.empty:
            # Get the last clicked article
            last_clicked_article = user_clicks.iloc[-1]['click_article_id']

            # Use the recommendation feature to get recommended articles
            recommended_articles = self.recommend_articles(last_clicked_article, n_recommendations=5)
            return recommended_articles
        else:
            # Return an appropriate message or action when there are no clicks for the user
            return "No clicks found for the specified user"

@app.route(route="http_reco_system")
def http_reco_system(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    user_id = req.params.get('user_id')

    if not user_id:
        return func.HttpResponse(
             "Please pass a user_id on the query string or in the request body",
             status_code=400
        )
    else:
        logging.info(f"Function triggered with user_id: {user_id}")

        # Create a blob service client
        blob_service_client = BlobServiceClient.from_connection_string(secret_key)

        # Get the blob client for the embeddings
        embeddings_blob_client = blob_service_client.get_blob_client("embed-csv", "articles_embed_pca.pickle")

        # Download the embeddings
        embeddings_blob = embeddings_blob_client.download_blob().readall()
        embeddings = pickle.loads(embeddings_blob)

        # Get the blob client for the clicks DataFrame
        df_clicks_blob_client = blob_service_client.get_blob_client("embed-csv", "click_sample_info.csv")

        # Download the clicks DataFrame
        df_clicks_blob = df_clicks_blob_client.download_blob().readall()
        df_clicks = pd.read_csv(BytesIO(df_clicks_blob))

        # Initialize your ArticleRecommender here with your embeddings and df_clicks
        recommender = ArticleRecommender(embeddings, df_clicks)

        # Get the recommended articles for the user
        recommended_articles = recommender.get_recommended_articles(user_id)

        # Return the recommended articles
        return func.HttpResponse(json.dumps(recommended_articles))