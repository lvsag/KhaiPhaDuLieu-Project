from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pandas as pd
from pandas.errors import ParserError

from config import CSV_CHUNKSIZE, DATA_DIR, RECIPES_FILE_CANDIDATES, REVIEWS_FILE_CANDIDATES


def resolve_data_dir(data_dir: str | Path | None = None) -> Path:
    path = Path(data_dir) if data_dir else DATA_DIR
    return path.resolve()


def get_dataset_files(data_dir: str | Path | None = None) -> dict[str, Path]:
    folder = resolve_data_dir(data_dir)
    if not folder.exists():
        raise FileNotFoundError(f"Khong tim thay thu muc data: {folder}")

    recipes_path = find_first_existing(folder, RECIPES_FILE_CANDIDATES)
    reviews_path = find_first_existing(folder, REVIEWS_FILE_CANDIDATES)

    missing = []
    if recipes_path is None:
        missing.append(" / ".join(RECIPES_FILE_CANDIDATES))
    if reviews_path is None:
        missing.append(" / ".join(REVIEWS_FILE_CANDIDATES))
    if missing:
        raise FileNotFoundError(
            f"Khong tim thay file dataset trong {folder}: " + ", ".join(missing)
        )

    return {
        "recipes": recipes_path,
        "reviews": reviews_path,
    }


def find_first_existing(folder: Path, filenames: list[str]) -> Path | None:
    for filename in filenames:
        path = folder / filename
        if path.exists():
            return path
    return None


def read_csv_in_chunks(path: Path, chunksize: int = CSV_CHUNKSIZE) -> Iterator[pd.DataFrame]:
    try:
        yield from pd.read_csv(path, chunksize=chunksize)
    except UnicodeDecodeError:
        yield from pd.read_csv(path, chunksize=chunksize, encoding="latin1")
    except ParserError as exc:
        raise ValueError(f"File loi dinh dang CSV: {path} - {exc}") from exc
