import requests
from config import headers, unicode_dict
from bs4 import BeautifulSoup
import re


def search(keyword, params={}):
    """Search Genius API for a keyword (e.x. artist name)
    Parameters:
    keyword(str): The input search string
    params(dict): Optional parameters dictionary (e.x. page number, results per page)
    Returns:
    Response object or raises an exception
    """
    try:
        url = f"http://api.genius.com/search?q={keyword}"
        response = requests.get(url, headers=headers, params=params)
        return response
    except requests.exceptions.Timeout:
        raise Exception("Timeout error. Try again.")
    except requests.exceptions.TooManyRedirects:
        raise Exception("Keyword not found. Bad URL.")
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)


def split_artists(name, delimiter=["&", ","]):
    """Split a delimited string of artists names into an array
    Parameters:
    name(string): An input string of artist name(s)
    delimiter(list): List of characters that could delimit artists names in input string
    Returns:
    artists(list): A list of individual artist names parsed from input string
    """
    # Find which character is used as a delimiter
    for char in delimiter:
        if name.find(char) != -1:
            # Split name into list of individual artist names
            artists = name.split(char)
            return artists


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
        # Get list of primary_artists
        primary_artists = []
        for metadata in result["primary_artists"]:
            name = metadata["name"]
            # Primary artist is sometimes  a string of multiple artists (e.x. Calvin Harris & Lana Del Rey)
            if "&" in name or "," in name:
                multiple_artists = split_artists(name)
                if multiple_artists:
                    for artist in multiple_artists:
                        #  Replace unicode expressions from artist names
                        primary_artists.append(remove_unicode(artist, unicode_dict))
            else:
                primary_artists.append(name)
        # Get list of featured artists
        if features:
            featured_artists = []
            for artist in result["featured_artists"]:
                #  Replace unicode expressions from artist names
                featured_artists.append(remove_unicode(artist["name"], unicode_dict))
        # Get song lyrics using song path
        lyrics = song_lyrics(path)
        song_data.append([title, featured_artists, primary_artists, path, lyrics])


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
    content(str): Input string to remove unicode expressions from
    unicode(dict): Optional dictionary of (target unicode string : replacement plaintext string) pairs
    Returns:
    content(str): Input string with dictionary's unicode keys replaced with plaintext values
    """
    # Replace each unicode_dict key in content with value
    for key in unicode_dict:
        content = content.replace(key, unicode_dict[key])
    return content
