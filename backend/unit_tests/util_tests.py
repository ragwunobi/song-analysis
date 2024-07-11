import unittest
from unittest import mock
import requests
from backend.config import unicode_dict
from backend.utils import (
    split_artist_names,
    remove_unicode,
    insert_spaces,
    remove_end_digits,
)
from unittest.mock import patch, MagicMock


class TestUtilsFunctions(unittest.TestCase):
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

    def test_insert_spaces_two_groups(self):
        """Test input with two groups to insert one space between"""
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

    def test_insert_spaces_empty_string(self):
        """Test input with empty string"""
        regex = [r"([].,!?])([A-Z])", r"([\).,!?])([A-Z])"]
        lyrics = ""
        cleaned_lyrics = insert_spaces(lyrics, regex)
        expected_result = ""
        self.assertEqual(cleaned_lyrics, expected_result)

    def test_insert_spaces_multiple_whitespaces(self):
        """Test input with multiple whitespaces"""
        regex = [r"([].,!?])([A-Z])"]
        lyrics = "     "
        cleaned_lyrics = insert_spaces(lyrics, regex)
        expected_result = ""
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
        """Test input with regex expressions with three groups"""
        regex = [r"([a-z])([A-Z])([a-z])"]
        lyrics = "(Lyrics) Is it that sweetI guess so"
        with self.assertRaises(ValueError):
            cleaned_lyrics = insert_spaces(lyrics, regex)

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

    def test_remove_unicode_empty_string(self):
        """Test input with an empty string"""
        artist_name = ""
        cleaned_artist_name = remove_unicode(artist_name, unicode_dict)
        expected_result = ""
        self.assertEqual(cleaned_artist_name, expected_result)

    def test_remove_unicode_multiple_whitespace(self):
        """Test input with multiple whitespaces"""
        artist_name = "    "
        cleaned_artist_name = remove_unicode(artist_name, unicode_dict)
        expected_result = ""
        self.assertEqual(cleaned_artist_name, expected_result)

    def test_remove_unicode_all_unicode_no_spaces(self):
        """Test input with only unicode expressions and no spaces"""
        artist_name = "\u00a0\u2019\u200b\u0435"
        cleaned_artist_name = remove_unicode(artist_name, unicode_dict)
        expected_result = " ' e"
        self.assertEqual(cleaned_artist_name, expected_result)

    def test_split_artist_names_comma_and_ampersand(self):
        """Test input with three names and comma and ampersand delimters"""
        artists = split_artist_names("Lana Del Rey, Calvin Harris, & Doja Cat")
        expected_result = ["Lana Del Rey", "Calvin Harris", "Doja Cat"]
        self.assertListEqual(artists, expected_result)

    def test_split_artist_names_empty_string(self):
        """Test input of an empty string"""
        artists = split_artist_names(" ")
        expected_result = []
        self.assertListEqual(artists, expected_result)

    def test_split_artist_names_multiple_whitespace(self):
        """Test input with multiple whitespaces"""
        artists = split_artist_names("        ")
        expected_result = []
        self.assertListEqual(artists, expected_result)

    def test_split_artist_names_commas_and_whitespace(self):
        """Test input with whitespace and commas"""
        artists = split_artist_names("    ,   ,  ")
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


if __name__ == "__main__":
    unittest.main()
