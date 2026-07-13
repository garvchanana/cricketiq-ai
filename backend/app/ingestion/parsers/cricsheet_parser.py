import json


class CricsheetParser:

    @staticmethod
    def load_match_file(
        file_path: str
    ):

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)