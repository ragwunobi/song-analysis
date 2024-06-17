from flask import Flask
from config import headers, unicode_dict
from utils import search, parse_song

app = Flask(__name__)


@app.route("/songs/<name>")
def get_songs(
    name, start_page=3, per_page=2, page_limit=5, page_increment=1, features=True
):
    """Get an artist's song data as a list - title, features, path, and lyrics
    Parameters:
    name(str): Input string of artist's name
    start_page(int): Optional starting page parameter for request
    per_page(int): Optional # of results per page parameter for request
    page_limit(int): Optional limit on # of pages requested
    page_increment(int): Optional # of pages incrementented by between requests
    features(bool): Optional boolean flag to get featured artis
    Returns:
    song_data(list(list)): Title, primary artists, featured artists, path, and lyrics for each song found
    """
    params = {"per_page": per_page, "page": start_page}
    # List to store artist's song data
    song_data = []
    page_count = 0
    # Return song data when page limit is reached
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
    """Get a dictionary of frequency counts of artist's collaborators
    Parameters:
    name(str): Input string of artist's name
    start_page(int): Optional starting page parameter for request
    per_page(int): Optional # of results per page parameter for request
    page_limit(int): Optional limit on # of pages requested
    page_increment(int): Optional # of pages incrementented by between requests
    features(bool): Optional boolean flag to get featured artist
    features_limit(int): Optional limit on # of collaborators pulled
    Returns:
    artist_count(dict): Dictionary mapping collaborator names to the number of songs they have with the input artist
    """
    # Dictionary to store collaboration frequency
    collaborator_freq = {}
    # Get song data for input artist
    song_data = get_songs(
        name, start_page, per_page, page_limit, page_increment, features
    )
    # Keep track of current song index
    song_index = 0

    while len(collaborator_freq) <= features_limit:
        primary_artists = featured_artists = []
        if song_data:
            primary_artists = song_data[song_index][2]
            featured_artists = song_data[song_index][1]
        # Add primary artist collaborators to dictionary
        for primary in primary_artists:
            primary = primary.strip()
            if primary not in collaborator_freq:
                collaborator_freq[primary] = 1
            else:
                collaborator_freq[primary] += 1
        # Add featured artist collaborators to dictionary
        for feature in featured_artists:
            feature = feature.strip()
            if feature not in collaborator_freq:
                collaborator_freq[feature] = 1
            else:
                collaborator_freq[feature] += 1
        song_index += 1
    return collaborator_freq


if __name__ == "__main__":
    app.run(debug=True)
