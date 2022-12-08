import os
import unittest

from tests import helper

from packages.song_scrounger import util

class TestUtil(unittest.TestCase):
    def test_read_file_contents(self):
        input_file = helper.get_path_to_test_input_file("single_artist_mentioned.txt")

        contents = util.read_file_contents(input_file)

        self.assertEqual(
            "When Don McLean recorded \"American Pie\"\n",
            contents,
            "Uexpected file contents!"
        )