import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import unittest
from unittest.mock import Mock
import requests
from backend.config import headers, unicode_dict
from backend.config import unicode_dict
from backend.utils import (
    search,
    split_artist_names,
    remove_unicode,
    insert_spaces,
    remove_end_digits,
    parse_song,
    clean_lyrics,
)
from unittest.mock import patch, MagicMock

#  Import sample GET request response
path = os.path.join(os.path.dirname(__file__), "sample_response.json")
with open(path) as response:
    sample_response = json.load(response)


class TestUtilsFunctions(unittest.TestCase):

    def test_search_empty_keyword(self):
        """Test with an empty keyword"""
        with self.assertRaises(ValueError) as value_error:
            search("")
        self.assertEqual(
            "The keyword cannot be empty. Please provide a valid keyword and try the request again.",
            str(value_error.exception),
        )

    @patch("requests.get")
    def test_search_successful_request(self, mock_get):
        """Test with a valid input artist"""
        self.keyword = "Kacey Musgraves"
        mock_get.return_value.json.return_value = sample_response["response"]
        mock_get.return_value.status_code = sample_response["meta"]["status"]
        response = search(self.keyword)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), mock_get.return_value.json.return_value)

    @patch("requests.get")
    def test_search_404_http_error(self, mock_get):
        """Test input results in 404 HTTP error"""
        self.keyword = "Kendrick"
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.side_effect.response = requests.Response()
        mock_get.side_effect.response.status_code = 404
        with self.assertRaises(Exception) as http_error:
            search(self.keyword)
        self.assertEqual(
            "HTTP 404 Error: 404 Not Found. URL: http://api.genius.com/search?q=Kendrick. Client error. The request contains invalid syntax or cannot be fulfilled. Please check URL and parameters and try the request again.",
            str(http_error.exception),
        )

    @patch("requests.get")
    def test_search_502_http_error(self, mock_get):
        """Test input results in 502 HTTP error"""
        self.keyword = "Sabrina Carpenter"
        mock_get.side_effect = requests.exceptions.HTTPError("502 Bad Gateway")
        mock_get.side_effect.response = requests.Response()
        mock_get.side_effect.response.status_code = 502
        with self.assertRaises(Exception) as http_error:
            search(self.keyword)
        self.assertEqual(
            "HTTP 502 Error: 502 Bad Gateway. URL: http://api.genius.com/search?q=Sabrina Carpenter. Server error. The request appears valid but the server is unable to fulfill it. Please wait a moment and try the request again.",
            str(http_error.exception),
        )

    @patch("requests.get")
    def test_search_timeout_error(self, mock_get):
        """Test input results in Timeout error"""
        self.keyword = "SZA"
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        with self.assertRaises(Exception) as timeout_error:
            search(self.keyword)
        self.assertEqual(
            "Timeout Error: Request timeout. URL: http://api.genius.com/search?q=SZA. The request timed out. Please check your internet connection and try again.",
            str(timeout_error.exception),
        )

    @patch("requests.get")
    def test_search_redirects_error(self, mock_get):
        """Test input results in Too Many Redirects error"""
        self.keyword = "Black Eyed Peas"
        mock_get.side_effect = requests.exceptions.TooManyRedirects("Redirects error")
        with self.assertRaises(Exception) as redirects_error:
            search(self.keyword)
        self.assertEqual(
            "Too Many Redirects: Redirects error. URL: http://api.genius.com/search?q=Black Eyed Peas. The request was redirected too many times. Please clear cookies and browser cache and try again.",
            str(redirects_error.exception),
        )

    @patch("requests.get")
    def test_search_request_exception(self, mock_get):
        """Test input results in Request Exception"""
        self.keyword = "Jimi Hendrix"
        mock_get.side_effect = requests.exceptions.RequestException("Request error")
        with self.assertRaises(Exception) as request_exception:
            search(self.keyword)
        self.assertEqual(
            "Request Exception: Request error. URL: http://api.genius.com/search?q=Jimi Hendrix. Unexpected request exception occurred. Please check URL and parameters and try the request again.",
            str(request_exception.exception),
        )

    def test_parse_song_successful_request(self):
        """Test with a valid response"""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.json = MagicMock(return_value=sample_response)
        song_data = parse_song(mock_response)
        expected_song_name = "Rainbow by Kacey Musgraves"
        expected_featured_artist = []
        expected_path = "/Kacey-musgraves-rainbow-lyrics"
        expected_primary_artist = ["Kacey Musgraves"]
        self.assertEqual(song_data[0][0], expected_song_name)
        self.assertListEqual(song_data[0][1], expected_featured_artist)
        self.assertListEqual(song_data[0][2], expected_primary_artist)
        self.assertEqual(song_data[0][3], expected_path)
        expected_song_name = "Butterflies by Kacey Musgraves"
        expected_path = "/Kacey-musgraves-butterflies-lyrics"
        self.assertEqual(song_data[1][0], expected_song_name)
        self.assertListEqual(song_data[1][1], expected_featured_artist)
        self.assertListEqual(song_data[1][2], expected_primary_artist)
        self.assertEqual(song_data[1][3], expected_path)

    def test_parse_song_value_error(self):
        """Test input results in value error"""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.json = MagicMock(return_value={})
        with self.assertRaises(ValueError) as value_error:
            parse_song(mock_response)
        self.assertEqual(
            'Value Error: JSON response object does not contain "response". Please review the response object provided.',
            str(value_error.exception),
        )

    def test_parse_song_key_error(self):
        """Test input results in key error"""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.json = MagicMock(return_value={"response": {"title": "Espresso"}})
        with self.assertRaises(KeyError) as key_error:
            parse_song(mock_response)

    def test_clean_lyrics_no_start(self):
        """Test input where start pattern does not match"""
        response = Mock()
        response.text = "A town you're just a guest inSo you work your life away just to payFor a time-share down in DestinEmbed930"
        cleaned_lyrics = clean_lyrics(response)
        expected_result = "A town you're just a guest in So you work your life away just to pay For a time-share down in Destin"
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_clean_lyrics_no_end(self):
        """Test input where end pattern does not match"""
        response = Mock()
        response.text = "Lyrics[I'm working late cuz I'm a singer2332"
        cleaned_lyrics = clean_lyrics(response)
        expected_result = "I'm working late cuz I'm a singer"
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_clean_lyrics_start_and_end(self):
        """Test input where start and end pattern matches"""
        response = Mock()
        response.text = "Lyrics[Alien superstarEmbed"
        cleaned_lyrics = clean_lyrics(response)
        expected_result = "Alien superstar"
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_clean_lyrics_no_pattern(self):
        """Test input where neither start nor end pattern matches"""
        response = Mock()
        response.text = "I'm working late cuz I'm a singer"
        cleaned_lyrics = clean_lyrics(response)
        expected_result = "I'm working late cuz I'm a singer"
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_clean_lyrics_unicode(self):
        """Test input with unicode expressions"""
        response = Mock()
        response.text = "\u0435 \u0435 \u2019\u200b"
        cleaned_lyrics = clean_lyrics(response)
        expected_result = "e e ' "
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_remove_end_digits_all_digits(self):
        """Test input of all digits"""
        lyrics = "12345"
        cleaned_lyrics = remove_end_digits(lyrics)
        expected_result = ""
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_remove_end_digits_lyrics_and_digits(self):
        """Test input with lyrics and digits"""
        lyrics = "I'm the bar Alien SuperStar960"
        cleaned_lyrics = remove_end_digits(lyrics)
        expected_result = "I'm the bar Alien SuperStar"
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_remove_end_digits_whitespace_and_digits(self):
        """Test input with whitespace and digits"""
        lyrics = "    932032"
        cleaned_lyrics = remove_end_digits(lyrics)
        expected_result = "    "
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_remove_end_digts_no_digits(self):
        """Test input with no digits"""
        lyrics = "It's so confusing sometimes"
        cleaned_lyrics = remove_end_digits(lyrics)
        # Lyrics are not changed because they do not contain digits.
        self.assertEqual(lyrics, cleaned_lyrics)

    def test_remove_end_digits_empty_input(self):
        """Test empty input"""
        lyrics = ""
        cleaned_lyrics = remove_end_digits(lyrics)
        # Lyrics are not changed because input is empty.
        self.assertEqual(lyrics, cleaned_lyrics)

    def test_insert_spaces_empty_string(self):
        """Test input with empty string"""
        regex = [r"([].,!?])([A-Z])", r"([\).,!?])([A-Z])"]
        lyrics = ""
        cleaned_lyrics = insert_spaces(lyrics, regex)
        expected_result = ""
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_insert_spaces_single_expression(self):
        """Test input with one regex to insert a space between"""
        regex = [r"([a-z])([A-Z])"]
        lyrics = "Is it that sweetI guess so"
        cleaned_lyrics = insert_spaces(lyrics, regex)
        expected_result = "Is it that sweet I guess so"
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_insert_spaces_punctuation(self):
        """Test input with punctuation and uppercase letter"""
        regex = [r"([a-z.,!?])([A-Z])"]
        lyrics = "Is it that sweet?I guess so"
        cleaned_lyrics = insert_spaces(lyrics, regex)
        expected_result = "Is it that sweet? I guess so"
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_insert_spaces_closing_brackets(self):
        """Test input with closing bracket and parentheses"""
        regex = [r"([].,!?])([A-Z])", r"([\).,!?])([A-Z])"]
        lyrics = "[Lyrics]Is it that sweet, I guess so(Chorus)"
        cleaned_lyrics = insert_spaces(lyrics, regex)
        expected_result = "[Lyrics] Is it that sweet, I guess so(Chorus)"
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_insert_spaces_multiple_whitespaces(self):
        """Test input with multiple whitespaces"""
        regex = [r"([].,!?])([A-Z])"]
        lyrics = "     "
        cleaned_lyrics = insert_spaces(lyrics, regex)
        expected_result = "     "
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_insert_spaces_empty_regex(self):
        """Test input with empty regex list"""
        regex = []
        lyrics = "Is it that sweet? I guess so"
        cleaned_lyrics = insert_spaces(lyrics, regex)
        expected_result = "Is it that sweet? I guess so"
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_insert_spaces_invalid_regex(self):
        """Test input with invalid expressions in regex list"""
        regex = [" ", r"([].,!?])([A-Z]"]
        lyrics = "Is it that sweet? I guess so"
        with self.assertRaises(ValueError):
            cleaned_lyrics = insert_spaces(lyrics, regex)

    def test_insert_spaces_whitespace_regex(self):
        """Test input with whitespace in regex list"""
        regex = ["   "]
        lyrics = "Is it that sweet? I guess so"
        with self.assertRaises(ValueError):
            cleaned_lyrics = insert_spaces(lyrics, regex)

    def test_insert_spaces_three_groups(self):
        """Test input with regex with three groups"""
        regex = [r"([a-z])([A-Z])([a-z])"]
        lyrics = "(Lyrics) Is it that sweetI guess so"
        with self.assertRaises(Exception):
            cleaned_lyrics = insert_spaces(lyrics, regex)

    def test_insert_spaces_type_error(self):
        """Test input where regex is not a string"""
        regex = [1234]
        lyrics = "(Lyrics) Is it that sweetI guess so"
        with self.assertRaises(TypeError):
            cleaned_lyrics = insert_spaces(lyrics, regex)

    def test_remove_unicode_empty_string(self):
        """Test input with an empty string"""
        artist_name = ""
        cleaned_artist_name = remove_unicode(artist_name, unicode_dict)
        expected_result = ""
        self.assertEqual(cleaned_artist_name, expected_result)

    def test_remove_unicode_single_replacement(self):
        """Test input with a single unicode expression"""
        artist_name = "\u0435"
        cleaned_artist_name = remove_unicode(artist_name, unicode_dict)
        expected_result = "e"
        self.assertEqual(cleaned_artist_name, expected_result)

    def test_remove_unicode_multiple_replacements(self):
        """Test input with multiple unicode expressions"""
        artist_name = "Fitz\u200band\u00a0the\u00a0Tantrums"
        cleaned_artist_name = remove_unicode(artist_name, unicode_dict)
        expected_result = "Fitz and the Tantrums"
        self.assertEqual(cleaned_artist_name, expected_result)

    def test_remove_unicode_apostrophe(self):
        """Test input with a single apostrophe"""
        artist_name = "The Maria\u2019s"
        cleaned_artist_name = remove_unicode(artist_name, unicode_dict)
        expected_result = "The Maria's"
        self.assertEqual(cleaned_artist_name, expected_result)

    def test_remove_unicode_all_unicode_no_spaces(self):
        """Test input with only unicode expressions and no spaces"""
        artist_name = "\u00a0\u2019\u200b\u0435"
        cleaned_artist_name = remove_unicode(artist_name, unicode_dict)
        expected_result = " ' e"
        self.assertEqual(cleaned_artist_name, expected_result)

    def test_remove_unicode_replace_spaces(self):
        """Test input with unicode spaces"""
        artist_name = " \u200b  \u200b"
        cleaned_artist_name = remove_unicode(artist_name, unicode_dict)
        expected_result = "     "
        self.assertEqual(cleaned_artist_name, expected_result)

    def test_split_artist_names_empty_string(self):
        """Test input of an empty string"""
        artists = split_artist_names("")
        expected_result = []
        self.assertListEqual(artists, expected_result)

    def test_split_artist_names_one_whitespace(self):
        """Test input with one whitespace"""
        artists = split_artist_names(" ")
        expected_result = []
        self.assertListEqual(artists, expected_result)

    def test_split_artist_names_multiple_whitespace(self):
        """Test input with multiple whitespaces"""
        artists = split_artist_names("        ")
        expected_result = []
        self.assertListEqual(artists, expected_result)

    def test_split_artist_names_multiple_commas(self):
        """Test input with commas between artist names"""
        artists = split_artist_names("J. Balvin, Bad Bunny, The Weekend, Rihanna ")
        expected_result = ["J. Balvin", "Bad Bunny", "The Weekend", "Rihanna"]
        self.assertListEqual(artists, expected_result)

    def test_split_artist_names_multiple_ampersands(self):
        """Test input with ampersand between artist names"""
        artists = split_artist_names("J. Balvin & Bad Bunny & The Weekend & Rihanna ")
        expected_result = ["J. Balvin", "Bad Bunny", "The Weekend", "Rihanna"]
        self.assertListEqual(artists, expected_result)

    def test_split_artist_names_commas_and_whitespace(self):
        """Test input with commas and whitespace"""
        artists = split_artist_names("    ,   ,  ")
        expected_result = []
        self.assertListEqual(artists, expected_result)

    def test_split_artist_names_commas_and_ampersand(self):
        """Test input with commas and ampersand between artist names"""
        artists = split_artist_names("Lana Del Rey, Calvin Harris, & Doja Cat")
        expected_result = ["Lana Del Rey", "Calvin Harris", "Doja Cat"]
        self.assertListEqual(artists, expected_result)

    def test_split_artist_names_multiple_commas_and_ampersands(self):
        """Test input with multiple commas and ampersands between artist names"""
        artists = split_artist_names("    Lady Gaga & , & & SZA, Tame Impala")
        expected_result = ["Lady Gaga", "SZA", "Tame Impala"]
        self.assertListEqual(artists, expected_result)


if __name__ == "__main__":
    unittest.main()
