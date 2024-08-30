import requests
from requests.exceptions import HTTPError, Timeout, TooManyRedirects, RequestException
from config import headers, unicode_dict
from bs4 import BeautifulSoup
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def search(keyword, search_params=None):
    """
    Search the Genius API for a keyword (e.x. artist name)
    Parameters:
    - keyword(str): The input search string.
    - search_params(dict,optional): Dictionary of parameters (e.x. page number, results per page). Default is None.

    Returns:
    - requests.Response: A response object from the requests library.

    Raises:
    - ValueError: If the keyword parameter is empty.
    - HTTPError: If there is a client or server HTTPError.
    - Timeout: If the request times out.
    - TooManyRedirects: If the request is redirected too many times.
    - RequestException: If an unexpected request exception occurs.
    """
    if not keyword:
        logger.error("Attempted search with an empty keyword.")
        raise ValueError(
            "The keyword cannot be empty. Please provide a valid keyword and try the request again."
        )
    url = f"http://api.genius.com/search?q={keyword}"
    try:
        logger.info(f"Attempting search request for '{keyword}'.")
        response = requests.get(url, headers=headers, params=search_params)
        response.raise_for_status()
        logger.info(f"Successfully completed search request for keyword: '{keyword}'.")
        return response

    except HTTPError as http_error:
        status_code = http_error.response.status_code
        logger.error(f"HTTP Error {status_code}: {http_error}. URL: {url}.")
        if 400 <= status_code < 500:
            exception_message = "Client error. The request contains invalid syntax or cannot be fulfilled. Please check URL and parameters and try the request again."
        elif status_code >= 500:
            exception_message = "Server error. The request appears valid but the server is unable to fulfill it. Please wait a moment and try the request again."
        else:
            exception_message = "Unexpected error occurred. Please check URL and parameters and try the request again."
        raise Exception(
            f"HTTP {status_code} Error: {http_error}. URL: {url}. {exception_message}"
        ) from http_error

    except Timeout as timeout_error:
        logger.error(f"Timeout Error: {timeout_error}. URL: {url}.")
        raise Exception(
            f"Timeout Error: {timeout_error}. URL: {url}. The request timed out. Please check your internet connection and try again."
        ) from timeout_error

    except TooManyRedirects as redirects_error:
        logger.error(f"Too Many Redirects: {redirects_error}. URL: {url}.")
        raise Exception(
            f"Too Many Redirects: {redirects_error}. URL: {url}. The request was redirected too many times. Please clear cookies and browser cache and try again."
        ) from redirects_error

    except RequestException as error:
        logger.error(f"Request Exception: {error}. URL: {url}.")
        raise Exception(
            f"Request Exception: {error}. URL: {url}. Unexpected request exception occurred. Please check URL and parameters and try the request again."
        ) from error


def split_artist_names(artist_names, delimiters=r",|&"):
    """Split a delimited string of artist names into an array of individual artists
    Parameters:
    artist_names(string): An input string of artist name(s)
    delimiter(str): Regex string of delimiters to split on
    Returns:
    cleaned_artist_names(list): A list of individual artist names parsed from input string
    """
    if len(artist_names) == 0 or artist_names.isspace():
        return []
    # Split a string of artist names into a list
    split_artist_names = re.split(r"\s*" + delimiters + r"\s*", artist_names.strip())
    # Clean empty or whitespace elements from the list
    cleaned_artist_names = [name.strip() for name in split_artist_names if name.strip()]
    return cleaned_artist_names


def parse_song(response, song_data=[], features_flag=True):
    """Get a list of title, path, lyrics, primary artists, and featured artists (optional) for each song in a response object
    Parameters:
    response(Requests.response): JSON response from Genius API GET request
    features(bool): Boolean flag (T/F) to get a song's featured artists
    Returns:
    song_data(list(list)): A list of lists (title, path, lyrics, primary artists, and featured artists (optional)) for each song
    """
    try:
        if "response" in response.json():
            response = response.json()["response"]
            # Iterate through each song in response
            for song in response["hits"]:
                result = song["result"]
                title = path = ""
                primary_artists = featured_artists = []
                # Get song title
                if result["full_title"]:
                    # Replace unicode expressions from the title
                    title = remove_unicode(result["full_title"], unicode_dict)
                # Get song path
                if result["path"]:
                    path = result["path"]
                # Get list of primary artists
                if result["primary_artists"]:
                    primary_artists = get_artist_list(result["primary_artists"])
                # Get list of featured artists
                if features_flag and result["featured_artists"]:
                    featured_artists = get_artist_list(result["featured_artists"])
                # Get song lyrics using path
                lyrics = song_lyrics(path)
                song_data.append(
                    [title, featured_artists, primary_artists, path, lyrics]
                )
            return song_data
        else:
            raise ValueError(
                'Value Error: JSON response object does not contain "response". Please review the response object provided.'
            )
    except KeyError as key_error:
        raise KeyError(
            f"Key Error: {key_error}. Please review response contains hits, result, full_title, path, primary_artists, and featured_artists keys if possible"
        )


def get_artist_list(artist_data):
    """Convert primary or featured artists JSON data to a list of cleaned artists names.
    Parameters:
    artist_data(dict): Primary or featured artist JSON data (e.x. result["featured_artists"])
    Returns:
    aritst_names_list(list): A list of cleaned artist names
    """
    artist_names = []
    for metadata in artist_data:
        if "name" in metadata and metadata["name"]:
            raw_artist_names = metadata["name"]
            # Remove unicode and split strings of multiple artists (e.x. "Calvin Harris & Lana Del Rey")
            individual_artist_names = split_artist_names(
                remove_unicode(raw_artist_names, unicode_dict)
            )
            for name in individual_artist_names:
                artist_names.append(name)
    return artist_names


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
    except Timeout as timeout_error:
        raise Exception(f"Timeout error: {timeout_error}. Please review your request.")
    except TooManyRedirects as redirects_error:
        raise Exception(
            f"Too many redirects: {redirects_error}. Please review the path provided."
        )
    except RequestException as error:
        raise SystemExit(f"Exception: {error}. Please review your request.")


def clean_lyrics(response, start_pattern=r"Lyrics[", end_pattern=r"Embed"):
    """Clean and format the lyrics from a Response object.
    Remove digits at the end of lyrics, replace unicode expressions with plaintext, and insert spaces between lines.
    Parameters:
    response(Requests.response): Response object from GET Request.
    start_pattern(str): Optional string pattern to match start of lyrics.
    end_pattern(str): Optional string pattern to match end of lyrics.
    Returns:
    lyrics(str): String of cleaned lyrics.
    """
    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as error:
        raise ValueError(
            f"Exception: {error}. Please review and confirm your response object is valid."
        )
    try:
        lyrics = soup.get_text()
        if len(lyrics) == 0:
            return ""

        # Find index where lyrics start
        start = lyrics.find(start_pattern)
        if start == -1:
            start = 0
        else:
            start += len(start_pattern)
        # Find index where lyrics end
        end = lyrics.find(end_pattern)
        if end == -1:
            end = len(lyrics)
        # Get lyrics section of the response (exclude other page information)
        lyrics = lyrics[start:end]

        # Clean lyrics
        # Remove digits at the end of lyrics
        lyrics = remove_end_digits(lyrics)
        # Replace unicode expressions with plaintext
        lyrics = remove_unicode(lyrics, unicode_dict)

        # Format lyrics
        # Use regex matching to insert spaces between lines
        lyrics = insert_spaces(
            lyrics,
            regex=[r"([a-z.,!?])([A-Z])", r"([\).,!?])([A-Z])", r"([].,!?])([A-Z])"],
        )
    except Exception as error:
        raise ValueError(
            f"Exception: {error}. Could not clean and format lyrics, please review your response."
        )
    return lyrics


def remove_end_digits(content):
    """Cleans digits at the end of a string.
    Parameters:
    content(str): An input string of lyrics.
    Returns:
    content(str): An input string with digits at the end removed.
    """
    if len(content) == 0:
        return ""
    end = len(content) - 1
    while end >= 0 and content[end].isdigit():
        content = content[0:end]
        end -= 1
    return content


def insert_spaces(content, regex=[]):
    """Insert a space between the two groups in each matching regex pattern
    Parameters:
    content(str): Input string to insert spaces into
    regex(list):  Optional list of regex patterns (each pattern has 2 groups)
    Returns:
    cleaned_content(str): Input string with space inserted between each regex pattern
    """
    if len(content) == 0 or content.isspace():
        return content
    cleaned_content = content
    for pattern in regex:
        # Match regex pattern and insert a space between groups
        try:
            num_groups = re.compile(pattern).groups
            if num_groups > 2:
                raise ValueError(
                    f"Regex error. Please confirm your regular expression has exactly two groups."
                )
            cleaned_content = re.sub(pattern, r"\1 \2", cleaned_content)
        except re.error as re_error:
            raise ValueError(
                f"Regex error: {re_error}. Please review your regular expressions."
            )
        except TypeError as type_error:
            raise TypeError(
                f"Type error: {type_error}. Please review your regular expressions."
            )
        except Exception as error:
            raise Exception(
                f"Exception: {error}. Please review your regular expressions."
            )
    return cleaned_content


def remove_unicode(content, unicode_dict={}):
    """Replace unicode expressions with plaintext in an input string
    Parameters:
    content(str): An input string to remove unicode expressions from
    unicode_dict(dict): Optional dictionary of (target unicode string : replacement plaintext string) pairs
    Returns:
    content(str): The cleaned input string with dictionary's unicode keys replaced with plaintext values
    """
    if len(content) == 0 or content.isspace():
        return content
    # Replace unicode expression (key) with plaintext (value)
    for key in unicode_dict:
        content = content.replace(key, unicode_dict[key])
    return content
