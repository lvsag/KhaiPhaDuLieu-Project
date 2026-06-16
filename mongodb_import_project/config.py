from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "DuLieu-KPDL"

RECIPES_FILE_CANDIDATES = ["RAW_recipes.csv", "recipes.csv"]
REVIEWS_FILE_CANDIDATES = ["RAW_interactions.csv", "reviews.csv"]

RECIPES_COLLECTION = "recipes"
REVIEWS_COLLECTION = "reviews"

BATCH_SIZE = 1000
CSV_CHUNKSIZE = 1000

NUTRITION_FIELDS = [
    "calories",
    "total_fat",
    "sugar",
    "sodium",
    "protein",
    "saturated_fat",
    "carbohydrates",
]
