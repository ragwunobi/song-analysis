import os
from dotenv import load_dotenv

# Get API keys from environment variables 
client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
client_access = os.getenv("client_access")
bearer = os.getenv("bearer_token")
headers = {"Authorization": f"Bearer {bearer}"}

# Dictionary of unicode expressions : plaintext values 
unicode_dict = {"\u00a0": " ", "\u2019": "'", "\u200b": " ", "\u0435": "e"}

