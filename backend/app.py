from flask import Flask, jsonify
import requests
import json

with open("config.json") as file:
    config = json.load(file)

# API Keys
client_id = config["client_id"]
client_secret = config["client_secret"]
client_access = config["client_access"]
bearer = config["bearer_token"]
headers = {"Authorization": f"Bearer {bearer}"}
app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello from Flask!"


# Get song titles and paths
@app.route("/songs/<name>")
def get_songs(name):
    url = "http://api.genius.com/search?q=" + name
    params = {"per_page": 50, "page": "1"}
    song_data = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        # limited to 500 songs
        if not response or len(song_data) >= 500:
            break
        response = response.json()["response"]
        for song in response["hits"]:
            result = song["result"]
            title = ""
            path = ""
            if result["full_title"]:
                title = result["full_title"]
            if result["path"]:
                path = result["path"]
            song_data.append((title, path))
    params["page"] = str(int(params["page"]) + 1)
    return song_data


if __name__ == "__main__":
    app.run(debug=True)
