from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable

from pymongo import ASCENDING, TEXT
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, PyMongoError
from tqdm import tqdm

from config import (
    BATCH_SIZE,
    RECIPES_COLLECTION,
    REVIEWS_COLLECTION,
)
from data_cleaner import clean_recipe_row, clean_review_row
from data_loader import get_dataset_files, read_csv_in_chunks


@dataclass
class ImportStats:
    recipes_imported: int = 0
    reviews_imported: int = 0
    errors: int = 0
    elapsed_seconds: float = 0.0


def create_indexes(db) -> None:
    recipes = db[RECIPES_COLLECTION]
    reviews = db[REVIEWS_COLLECTION]

    recipes.create_index([("id", ASCENDING)], name="idx_recipes_id")
    recipes.create_index([("recipe_id", ASCENDING)], name="idx_recipes_recipe_id")
    recipes.create_index([("name", ASCENDING)], name="idx_recipes_name")
    recipes.create_index([("ingredients", ASCENDING)], name="idx_recipes_ingredients")
    recipes.create_index([("tags", ASCENDING)], name="idx_recipes_tags")

    reviews.create_index([("recipe_id", ASCENDING)], name="idx_reviews_recipe_id")
    reviews.create_index([("user_id", ASCENDING)], name="idx_reviews_user_id")
    reviews.create_index([("rating", ASCENDING)], name="idx_reviews_rating")

    recipes.create_index(
        [
            ("name", TEXT),
            ("description", TEXT),
            ("steps", TEXT),
            ("ingredients", TEXT),
        ],
        name="text_recipes_search",
    )
    reviews.create_index([("review", TEXT)], name="text_reviews_review")


def clear_old_data(db) -> None:
    db[RECIPES_COLLECTION].delete_many({})
    db[REVIEWS_COLLECTION].delete_many({})


def insert_batch(collection: Collection, documents: list[dict]) -> tuple[int, int]:
    if not documents:
        return 0, 0

    try:
        result = collection.insert_many(documents, ordered=False)
        return len(result.inserted_ids), 0
    except BulkWriteError as exc:
        inserted = exc.details.get("nInserted", 0)
        errors = len(exc.details.get("writeErrors", []))
        return inserted, errors
    except PyMongoError:
        return 0, len(documents)


def import_csv_file(
    collection: Collection,
    path: Path,
    cleaner: Callable[[dict], dict],
    batch_size: int,
    label: str,
) -> tuple[int, int]:
    imported = 0
    errors = 0
    batch: list[dict] = []

    for chunk in tqdm(read_csv_in_chunks(path, chunksize=batch_size), desc=f"Import {label}"):
        for row in chunk.to_dict(orient="records"):
            try:
                batch.append(cleaner(row))
            except Exception:
                errors += 1
                continue

            if len(batch) >= batch_size:
                ok, failed = insert_batch(collection, batch)
                imported += ok
                errors += failed
                batch.clear()

    ok, failed = insert_batch(collection, batch)
    imported += ok
    errors += failed
    return imported, errors


def import_food_dataset(
    db,
    data_dir: str | Path | None = None,
    drop_old: bool = False,
    batch_size: int = BATCH_SIZE,
) -> ImportStats:
    start = perf_counter()
    stats = ImportStats()

    files = get_dataset_files(data_dir)

    if drop_old:
        clear_old_data(db)

    stats.recipes_imported, recipe_errors = import_csv_file(
        collection=db[RECIPES_COLLECTION],
        path=files["recipes"],
        cleaner=clean_recipe_row,
        batch_size=batch_size,
        label="recipes",
    )

    stats.reviews_imported, review_errors = import_csv_file(
        collection=db[REVIEWS_COLLECTION],
        path=files["reviews"],
        cleaner=clean_review_row,
        batch_size=batch_size,
        label="reviews",
    )

    stats.errors = recipe_errors + review_errors
    create_indexes(db)
    stats.elapsed_seconds = perf_counter() - start
    return stats
