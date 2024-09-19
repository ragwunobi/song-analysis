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
    """
    Get an artist's songs. Returns the title, artists, path, and lyrics for each song.
    Parameters:
    - name(str): An artist's name.
    - start_page(int, optional): A starting page number.
    - per_page(int, optional): The number of results per page.
    - page_limit(int, optional): The number of pages to limit to.
    - page_increment(int, optional): The number of pages to increment by.
    - features(bool, optional): A flag to get featured artists.

    Returns:
    - song_data(list(list)): The title, primary artists, featured artists, path, and lyrics for each song.
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
    """
    Get a dictionary of collaborator names (key) and the songs (value) they have with an artist.
    Parameters:
    - name(str): An artist's name.
    - start_page(int, optional): A starting page number.
    - per_page(int, optional): The number of results per page.
    - page_limit(int, optional): The number of pages to limit to.
    - page_increment(int, optional): The number of pages to increment by.
    - features(bool, optional): OA flag to get featured artists.
    - features_limit(int, optional: The number of collaborators to limit to.

    Returns:
    - collaborator_freq(dict): A dictionary mapping collaborator names to a list, where the first item is the number of songs (n) with the input artist, followed by the names of the n songs.

    Raises:
    - IndexError: If song data cannot be indexed for title, primary artists, or featured artists.
    - KeyError: If the song data dictionary is accessed with invalid keys.
    - Exception: If an unexpected error occurs.
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
            except IndexError as index_error:
                raise Exception(
                    f"Index error: {index_error}. Song data could not be indexed for title, primary artists, or featured_artists."
                )
            except KeyError as key_error:
                raise Exception(
                    f"Key Error: {key_error}. Key used to access song data was invalid."
                )
            except Exception as error:
                raise Exception(f"An unexpected error occurred: {error}.")
        # Add primary artist collaborators to dictionary
        generate_collaborator_freq(name, title, primary_artists, collaborator_freq)
        # Add featured artist collaborators to dictionary
        generate_collaborator_freq(name, title, featured_artists, collaborator_freq)
        song_index += 1
    return collaborator_freq


def generate_collaborator_freq(name, title, artists, collaborator_freq):
    """
    A helper function to generate a dictionary of collaborator names (key) and the songs (value) they have with an artist.
    Parameters:
    - name(str):  An artist's name.
    - title(str): A song title featuring the artist and their collaborator.
    - artists(list): A list of artists that collaborated to create the song with the input name artist.
    - collaborator_freq: A dictionary mapping collaborator names to a list, where the first item is the number of songs (n) with the input artist, followed by the names of the n songs.
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
