from flask import Flask, jsonify
from bs4 import BeautifulSoup
import requests
import json
import re

with open("config.json") as file:
    config = json.load(file)

# API Keys
client_id = config["client_id"]
client_secret = config["client_secret"]
client_access = config["client_access"]
bearer = config["bearer_token"]
headers = {"Authorization": f"Bearer {bearer}"}
app = Flask(__name__)


# Get song titles and paths
@app.route("/songs/<name>")
def get_songs(name):
    url = "http://api.genius.com/search?q=" + name
    params = {"per_page": 50, "page": "1"}
    song_data = []
    try:
        requests_count = 0
        while requests_count <= 10:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            response = response.json()["response"]
            for song in response["hits"]:
                result = song["result"]
                title = ""
                path = ""
                if result["full_title"]:
                    title = result["full_title"]
                if result["path"]:
                    path = result["path"]
                lyrics = song_lyrics(path)
                if lyrics:
                    song_data.append([title, path, lyrics])
                else:
                    song_data.append([title, path, "Lyrics not found."])
                requests_count += 1
            params["page"] = str(int(params["page"]) + 1)
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)
    except:
        raise Exception(
            name + " discography could not be found. Please try another request."
        )
    return song_data


# Get song lyrics from path
def song_lyrics(path):
    url = "https://genius.com" + path
    try:
        response = requests.get(url, headers=headers)
    except:
        raise Exception("Lyrics not found")
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.get_text()
    if content.find("Lyrics["):
        start = content.find("Lyrics[")
    else:
        start = 0
    end = re.search(r"[0-9][\w\s]+Embed", content)
    if end:
        end = len(content) if end == -1 else end.start()
    else:
        return
    return content[start:end]


if __name__ == "__main__":
    app.run(debug=True)
