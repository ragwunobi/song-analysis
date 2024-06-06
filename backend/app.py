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

# Unicode : plain text dictionary
unicode = {"\u00a0": " ", "\u2019": "'", "\u200b": " ", "\u0435": "e"}


def search(keyword, url, params={}):
    """Search Genius API for keyword
    Parameters:
    keyword(str): The search string
    url(str): URL of Genius API endpoint
    params(dict): Optional parameters to request Genius API (e.x. page (page number), per_page (results per page))
    Returns:
    Response object or raises an exception
    """
    try:
        response = requests.get(url, headers=headers, params=params)
        return response
    except requests.exceptions.Timeout:
        raise Exception("Timeout error. Try again.")
    except requests.exceptions.TooManyRedirects:
        raise Exception("Keyword not found. Bad URL.")
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)


@app.route("/songs/<name>")
def get_songs(name, start_page=1, per_page=2, page_limit=5, page_increment=1):
    """Get list of song data - title, path, and lyrics for an artist
    Parameters:
    name(str): Artist name for request/search
    start_page(int): Optional starting page parameter for request
    per_page(int): Optional # of results per page parameter for request
    page_limit(int): Optional limit on # of pages requested
    page_increment(int): Optional # of pages incrementented by between requests
    Returns:
    song_data(list(list)): [title(str), path(str), lyrics(str)] for each song found
    """
    params = {"per_page": per_page, "page": start_page}
    song_data = []  # List to store artist's song lyrics and metadata
    page_count = 0
    url = f"http://api.genius.com/search?q={name}"
    while page_count <= page_limit:
        # Search Genius API for artist name
        response = search(name, url, params)
        parse_song(response, song_data)
        page_count += 1
        # Increment page parameter for next request
        params["page"] = str(int(params["page"]) + page_increment)
    return song_data


def parse_song(response, song_data=[]):
    """Parse response object for title, path, and lyrics of each song
    Parameters:
    response(Requests.response): JSON response for song from Genius API GET request
    Returns:
    (song_data(list(list)): [title(str), path(str), lyrics(str)] for each song found
    """
    response = response.json()["response"]
    for song in response["hits"]:
        result = song["result"]
        title = path = ""
        if result["full_title"]:
            # Replace unicode expressions from the title
            title = remove_unicode(result["full_title"], unicode)
        if result["path"]:
            path = result["path"]
        lyrics = song_lyrics(path)
        song_data.append([title, path, lyrics])


def song_lyrics(path):
    """Scrape song lyrics and clean text
    Parameters:
    path(str): Path of song to scrape with GET request
    Returns:
    lyrics(str): Cleaned string of song lyrics or raises an exception
    """
    url = f"https://genius.com{path}"
    try:
        # Scrape song lyrics from Genius site
        response = requests.get(url, headers=headers)
        # Clean lyrics and return
        lyrics = clean_lyrics(response)
        return lyrics
    except requests.exceptions.Timeout:
        raise Exception("Timeout error. Try again.")
    except requests.exceptions.TooManyRedirects:
        raise Exception("Path not found. Bad URL.")
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)


def remove_unicode(content, unicode_dict={}):
    """Replace unicode expressions from a string with plain text characters
    Parameters:
    content(str): String to remove characters from
    unicode(dict): Optional dictionary of (target unicode string : replacement plaintext string) pairs
    Returns:
    content(str): Input string with unicode key values replaced with plaintext dict values
    """
    for key in unicode_dict:
        content = content.replace(key, unicode_dict[key])
    return content


def insert_spaces(content, regex=[]):
    """Insert space betweeen two regex groups
    Parameters:
    content(str): String to insert spaces into
    regex(list):  Optional List of regex patterns, each pattern has two groups
    Returns:
    content(str): Input string with space inserted between each regex pattern
    """
    for pattern in regex:
        content = re.sub(pattern, r"\1 \2", content)
    return content


def remove_end_digits(content):
    """Remove/clean digits at the end of lyrics
    Parameters:
    content(str): String to remove digits from the end of
    Returns:
    content(str): Input string with digits at the end removed
    """
    end = len(content) - 1
    while content[end].isdigit():
        content = content[0:end]
        end = len(content) - 1
    return content


def clean_lyrics(response, start_pattern=r"Lyrics[", end_pattern=r"Embed"):
    """Parse and clean lyrics from response object
    Parameters:
    response(requests.response): Response object from GET Request
    start_pattern(str): Optional string pattern to match start of lyrics
    end_pattern(str): Optional string pattern to match end of lyrics
    Returns:
    content(str): String of cleaned lyrics (digits at the end removed, unicode replaced with plain text, and spaces inserted)
    """
    soup = BeautifulSoup(response.text, "html.parser")
    # Get plain text from response
    content = soup.get_text()
    # Find index where lyrics start
    start = content.find(start_pattern)
    if start == -1:
        start = 0
    # Find index where lyrics end
    end = content.find(end_pattern)
    if end == -1:
        end = len(content) - 1
    # Call helper functions to clean lyrics
    content = content[start:end]
    content = remove_end_digits(content)
    content = remove_unicode(content, unicode)
    content = insert_spaces(
        content, regex=[r"([a-z])([A-Z])", r"(])([A-Z])", r"(\))([A-Z])"]
    )
    return content


if __name__ == "__main__":
    app.run(debug=True)
