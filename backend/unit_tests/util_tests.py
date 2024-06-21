import unittest
from unittest import mock 
import requests 
from backend.config import unicode_dict 
from backend.utils import split_artist_names, remove_unicode 
from unittest.mock import patch, MagicMock

class TestUtilsFunctions(unittest.TestCase):
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
