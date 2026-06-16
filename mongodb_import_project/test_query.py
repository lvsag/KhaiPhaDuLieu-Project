from pprint import pprint

from config import RECIPES_COLLECTION, REVIEWS_COLLECTION
from mongo_connection import get_database, get_mongo_client


def main() -> None:
    client = get_mongo_client()
    db = get_database(client)

    print("Tong so recipes:", db[RECIPES_COLLECTION].count_documents({}))
    print("Tong so reviews:", db[REVIEWS_COLLECTION].count_documents({}))

    print("\nMot recipe co chicken:")
    recipe = db[RECIPES_COLLECTION].find_one({"ingredients": "chicken"})
    pprint(recipe)

    print("\nTop 5 review rating cao:")
    for review in db[REVIEWS_COLLECTION].find({"rating": 5}).limit(5):
        pprint(review)

    print("\nText search recipe voi tu khoa salad:")
    for recipe in db[RECIPES_COLLECTION].find({"$text": {"$search": "salad"}}).limit(5):
        pprint({"recipe_id": recipe.get("recipe_id"), "name": recipe.get("name")})


if __name__ == "__main__":
    main()
