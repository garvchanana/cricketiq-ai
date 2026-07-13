import json
from pathlib import Path
from datetime import datetime


class RawDataSaver:

    @staticmethod
    def save_json(
        data: dict,
        folder: str,
        filename_prefix: str
    ):

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        base_path = Path("data/raw") / folder
        base_path.mkdir(parents=True, exist_ok=True)

        file_path = (
            base_path /
            f"{filename_prefix}_{timestamp}.json"
        )

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        return str(file_path)