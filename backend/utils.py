import requests
from backend.config import headers, unicode_dict
from bs4 import BeautifulSoup
import re


def search(keyword, search_params={}):
    """Search the Genius API for a keyword (e.x. artist name)
    Parameters:
    keyword(str): The input search string. 
    search_params(dict): Optional parameters dictionary (e.x. page number, results per page) 
    Returns:
    A response object or raises a request exception
    """
    try:
        url = f"http://api.genius.com/search?q={keyword}"
        response = requests.get(url, headers=headers, params=search_params)
        return response
    except requests.exceptions.Timeout:
        raise Exception("Timeout error. Please try your request again.")
    except requests.exceptions.TooManyRedirects:
        raise Exception("Too many redirects. Please review the path provided.")
    except requests.exceptions.RequestException as error:
        raise SystemExit(
            f"Request Exception: {error}. Please try again with a different keyword."
        )


def split_artist_names(artist_name, delimiters=r",|&"):
    """Split a delimited string of artists names into an array
    Parameters:
    artist_name(string): An input string of artist name(s)
    delimiter(str): Regex string of delimiters to split on
    Returns:
    artists(list): A list of individual artist names parsed from input string
    """
    if len(artist_name) == 0 or artist_name.isspace():
        return []
    # Split a string of artist names into a list
    individual_artists = re.split(r"\s*" + delimiters + r"\s*", artist_name.strip())
    # Clean empty or whitespace elements from the list
    cleaned_artist_names = [name.strip() for name in individual_artists if name.strip()]
    return cleaned_artist_names


def parse_song(response, song_data=[], features=True):
    """Get title, path, and lyrics for each song in a response object
    Parameters:
    response(Requests.response): JSON response from Genius API GET request
    features(bool): Input boolean flag to get a song's featured_artists
    Returns:
    song_data(list(list)): Title, primary artists, featured artists (opt), path, and lyrics for each song found
    """
    response = response.json()["response"]
    # Iterate through each song in response
    for song in response["hits"]:
        result = song["result"]
        title = path = ""
        # Get song title from response
        if result["full_title"]:
            # Replace unicode expressions from the title
            title = remove_unicode(result["full_title"], unicode_dict)
        # Get song's path
        if result["path"]:
            path = result["path"]
        primary_artists = []
        # Get list of primary_artists
        if result["primary_artists"]:
            primary_artists = get_artist_list(result["primary_artists"])
        featured_artists = []
        # Get list of featured artists
        if features and result["featured_artists"]:
            featured_artists = get_artist_list(result["featured_artists"])
        # Get song lyrics using song path
        lyrics = song_lyrics(path)
        song_data.append([title, featured_artists, primary_artists, path, lyrics])


def get_artist_list(artists_data):
    """Convert primary or featured artists JSON data to list of cleaned artists names.
    Parameters:
    artist_data(dict): Primary or featured artist JSON data (e.x. result["featured_artists"])
    Returns:
    aritst_names_list(list): A list of cleaned artist names
    """
    artists_names_list = []
    for metadata in artists_data:
        multiple_artist_names = metadata["name"]
        # Clean name by removing unicode and splitting strings of multiple artists (e.x. "Calvin Harris & Lana Del Rey")
        cleaned_artist_names = split_artist_names(
            remove_unicode(multiple_artist_names, unicode_dict)
        )
        for individual_name in cleaned_artist_names:
            artists_names_list.append(individual_name)
    return artists_names_list


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


def clean_lyrics(response, start_pattern=r"Lyrics[", end_pattern=r"Embed"):
    """Parse and clean lyrics from Response object
    Remove digits at the end of lyrics, replace unicode expressions with plaintext, insert spaces
    Parameters:
    response(Requests.response): Response object from GET Request
    start_pattern(str): Optional string pattern to match start of lyrics
    end_pattern(str): Optional string pattern to match end of lyrics
    Returns:
    lyrics(str): String of cleaned lyrics
    """
    soup = BeautifulSoup(response.text, "html.parser")
    # Get plain text from response
    lyrics = soup.get_text()
    # Find index where lyrics start
    start = lyrics.find(start_pattern)
    if start == -1:
        start = 0
    # Find index where lyrics end
    end = lyrics.find(end_pattern)
    if end == -1:
        end = len(lyrics) - 1
    # Call helper functions to clean lyrics
    lyrics = lyrics[start:end]
    # Remove digits at the end of lyrics
    lyrics = remove_end_digits(lyrics)
    # Replace unicode expressions with plaintext
    lyrics = remove_unicode(lyrics, unicode_dict)
    # Use Regex matching to insert spaces
    lyrics = insert_spaces(
        lyrics, regex=[r"([a-z])([A-Z])", r"(])([A-Z])", r"(\))([A-Z])"]
    )
    return lyrics


def remove_end_digits(content):
    """Cleans digits at the end of a string
    Parameters:
    content(str): Input string
    Returns:
    content(str): Input string with digits at the end removed
    """
    # Last index of input string
    end = len(content) - 1
    # Remove digits at the end of the string
    while content[end].isdigit():
        content = content[0:end]
        # Recalculate last index
        end = len(content) - 1
    return content


def insert_spaces(content, regex=[]):
    """Insert space betweeen two regex groups
    Parameters:
    content(str): Input string to insert spaces into
    regex(list):  Optional list of regex patterns (each patttern has two groups)
    Returns:
    content(str): Input string with space inserted between each regex pattern
    """
    for pattern in regex:
        # Match regex pattern and insert a space between groups
        content = re.sub(pattern, r"\1 \2", content)
    return content


def remove_unicode(content, unicode_dict={}):
    """Replace unicode expressions from a string with plaintext characters
    Parameters:
    content(str): An input string to remove unicode expressions from
    unicode(dict): Optional dictionary of (target unicode string : replacement plaintext string) pairs
    Returns:
    content(str): The cleaned input string with dictionary's unicode keys replaced with plaintext values
    """
    # Replace each unicode_dict key with value 
    if len(content) == 0 or content.isspace(): 
        return content.strip() 
    for key in unicode_dict:
        content = content.replace(key, unicode_dict[key])
    return content 
