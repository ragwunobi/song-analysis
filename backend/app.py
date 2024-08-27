from flask import Flask
from config import headers, unicode_dict
from utils import search, parse_song

app = Flask(__name__)


@app.route("/search/<name>")
def search_song(name):
    response = search(name)
    return response.json()


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
    per_page=10,
    page_limit=3,
    page_increment=1,
    features=True,
    features_limit=5,
):
    """Get a dictionary that maps collaborator names to the names and number of songs they have with input artist
    Parameters:
    name(str): Input string of artist's name
    start_page(int): Optional starting page parameter for request
    per_page(int): Optional # of results per page parameter for request
    page_limit(int): Optional limit on # of pages requested
    page_increment(int): Optional # of pages incrementented by between requests
    features(bool): Optional boolean flag to get featured artist
    features_limit(int): Optional limit on # of collaborators pulled
    Returns:
    artist_count(dict): Dictionary mapping collaborator names to the names and number of songs they have with the input artist
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
            try:
                title = song_data[song_index][0]
                primary_artists = song_data[song_index][2]
                featured_artists = song_data[song_index][1]
            except IndexError:
                raise Exception("Index error. Song data could not be found.")
            except KeyError:
                raise Exception("Key Error. Song data could not be found.")
            except Exception as error:
                raise Exception("Apologies, song data could not be found.")
        # Add primary artist collaborators to dictionary
        generate_collaborator_freq(name, title, primary_artists, collaborator_freq)
        # Add featured artist collaborators to dictionary
        generate_collaborator_freq(name, title, featured_artists, collaborator_freq)
        song_index += 1
    return collaborator_freq


def generate_collaborator_freq(name, title, artists, collaborator_freq):
    """Helper function to convert a list of artists into a dictionary that counts their frequency and lists song titles
    Parameters:
    name(str): Input string of main artist's name
    title(str): Input title of song the artist and collaborator are on
    artist(list): List of artists that collaborated with input name artist
    collaborator_freq: Dictionary of frequency counts of artist's collaborators
    """
    if artists:
        for collaborator in artists:
            # Do not include input artist as a collaborator
            if name == collaborator:
                continue
            # Add collaborator, frequency of collaboration to dictionary
            if collaborator not in collaborator_freq:
                collaborator_freq[collaborator] = [1, [title]]
            else:
                collaborator_freq[collaborator][0] += 1
                collaborator_freq[collaborator][1].append(title)


if __name__ == "__main__":
    app.run(debug=True)
