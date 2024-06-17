from flask import Flask, jsonify
from bs4 import BeautifulSoup
import requests
import json
import re
import os
from dotenv import load_dotenv

# API Keys
client_id = os.getenv("client_id")
client_secret = os.getenv("client_secret")
client_access = os.getenv("client_access")
bearer = os.getenv("bearer_token")
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
def get_songs(
    name, start_page=3, per_page=2, page_limit=5, page_increment=1, features=True
):
    """Get list of song data - title, features, path, and lyrics for an artist
    Parameters:
    name(str): The artist name for request/search
    start_page(int): Optional starting page parameter for request
    per_page(int): Optional # of results per page parameter for request
    page_limit(int): Optional limit on # of pages requested
    page_increment(int): Optional # of pages incrementented by between requests
    features(bool): T/F flag to get featured artists
    Returns:
    song_data(list(list)): Title, primary artists, featured artists, path, and lyrics for each song found
    """
    params = {"per_page": per_page, "page": start_page}
    song_data = []  # List to store artist's song lyrics and metadata
    page_count = 0
    url = f"http://api.genius.com/search?q={name}"
    while page_count <= page_limit:
        # Search Genius API for artist name
        response = search(name, url, params)
        parse_song(response, song_data, features)
        page_count += 1
        # Increment page parameter for next request
        params["page"] = str(int(params["page"]) + page_increment)
    return song_data


@app.route("/features/<name>")
def get_featured_artists(
    name,
    start_page=1,
    per_page=5,
    page_limit=10,
    page_increment=1,
    features=True,
    features_limit=10,
):
    artist_count = {}
    song_data = get_songs(
        name, start_page, per_page, page_limit, page_increment, features
    )
    song_index = 0
    while len(artist_count) <= features_limit:
        primary_artists = featured_artists = []
        if song_data:
            primary_artists = song_data[song_index][2]
            featured_artists = song_data[song_index][1]
        for artist in primary_artists:
            artist = artist.strip()
            if artist not in artist_count:
                artist_count[artist] = 1
            else:
                artist_count[artist] += 1

        for feature in featured_artists:
            feature = feature.strip()
            if feature not in artist_count:
                artist_count[feature] = 1
            else:
                artist_count[feature] += 1
        song_index += 1

    return artist_count


def parse_song(response, song_data=[], features=True):
    """Parse response object for title, path, and lyrics of each song
    Parameters:
    response(Requests.response): JSON response for song from Genius API GET request
    features(bool): T/F flag to get featured artists
    Returns:
    (song_data(list(list)): Title, primary artists, featured artists, path, and lyrics for each song found
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
        # Get list of primary_artists (sometimes a compound string e.x. Calvin Harris & Lana Del Rey)
        primary_artists = result["primary_artists"]
        artists = []
        for metadata in primary_artists:
            name = metadata["name"]
            if name.find("&") or name.find(","):
                multiple_artists = split_artists(name)
                if multiple_artists:
                    for artist in multiple_artists:
                        artists.append(remove_unicode(artist, unicode))
            else:
                artists.append(name)
        # Get list of featured artists
        if features:
            featured_artists = []
            for artist in result["featured_artists"]:
                featured_artists.append(remove_unicode(artist["name"], unicode))
        lyrics = song_lyrics(path)
        song_data.append([title, featured_artists, artists, path, lyrics])


def split_artists(name, delimiter=["&", ","]):
    """Parse out each artist name from a delimited string
    Parameters:
    name(string): A string of artist name(s)
    delimiter(list): The string of possible characters the string is delimited by
    Returns:
    artists(list): A list of artist names parsed out from string
    """
    for char in delimiter:
        if name.find(char) != -1:
            artists = name.split(char)
            return artists


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
