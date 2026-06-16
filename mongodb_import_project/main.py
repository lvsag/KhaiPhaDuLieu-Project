from __future__ import annotations

import argparse
import sys

from config import BATCH_SIZE, DATA_DIR, MONGO_URI
from import_to_mongo import import_food_dataset
from mongo_connection import get_database, get_mongo_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Food.com Recipes and Reviews CSV files into MongoDB."
    )
    parser.add_argument(
        "--data-dir",
        default=str(DATA_DIR),
        help="Thu muc chua RAW_recipes.csv va RAW_interactions.csv.",
    )
    parser.add_argument(
        "--drop-old",
        action="store_true",
        help="Xoa du lieu cu trong recipes va reviews truoc khi import.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help="So document moi batch insert.",
    )
    parser.add_argument(
        "--mongo-uri",
        default=MONGO_URI,
        help="MongoDB URI.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        client = get_mongo_client(args.mongo_uri)
        db = get_database(client)
        stats = import_food_dataset(
            db=db,
            data_dir=args.data_dir,
            drop_old=args.drop_old,
            batch_size=args.batch_size,
        )
    except Exception as exc:
        print(f"Loi: {exc}")
        return 1

    print("\nThong ke import")
    print(f"So recipe da import: {stats.recipes_imported}")
    print(f"So review da import: {stats.reviews_imported}")
    print(f"So loi: {stats.errors}")
    print(f"Thoi gian xu ly: {stats.elapsed_seconds:.2f} giay")
    return 0


if __name__ == "__main__":
    sys.exit(main())
