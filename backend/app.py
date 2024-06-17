from flask import Flask
import requests
import json
import re
from config import headers, unicode_dict 
from utils import search, parse_song 

app = Flask(__name__)



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
    while page_count <= page_limit:
        # Search Genius API for artist name
        response = search(name, params)
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


if __name__ == "__main__":
    app.run(debug=True)
