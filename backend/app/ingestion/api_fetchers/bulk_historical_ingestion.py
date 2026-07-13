from pathlib import Path

from app.ingestion.api_fetchers.historical_ingestion_pipeline import (
    HistoricalIngestionPipeline
)


class BulkHistoricalIngestion:

    @staticmethod
    def ingest_ipl_dataset(
        db
    ):

        dataset_path = Path(
            "../data/raw/historical/ipl"
        )

        json_files = list(
            dataset_path.glob("*.json")
        )

        total_files = len(json_files)

        total_inserted = 0

        failed_files = []

        for idx, file_path in enumerate(
            json_files,
            start=1
        ):

            try:

                print(
                    f"[{idx}/{total_files}] "
                    f"Ingesting {file_path.name}"
                )

                result = (
                    HistoricalIngestionPipeline
                    . ingest_match_file(
                        db=db,
                        file_path=str(file_path)
                    )
                )

                total_inserted += (
                    result.get(
                        "balls_inserted",
                        0
                    )
                )

            except Exception as error:

                print(
                    f"Failed: {file_path.name}"
                )

                print(error)

                failed_files.append(
                    file_path.name
                )

        return {
            "total_match_files": total_files,
            "total_balls_inserted": total_inserted,
            "failed_files_count": len(
                failed_files
            ),
            "failed_files": failed_files[:10]
        }