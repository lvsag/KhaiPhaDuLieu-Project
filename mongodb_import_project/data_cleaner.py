from __future__ import annotations

import ast
import re
from datetime import datetime
from typing import Any

import pandas as pd

from config import NUTRITION_FIELDS


def parse_python_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)

    try:
        if pd.isna(value):
            return []
    except (TypeError, ValueError):
        pass

    if isinstance(value, list):
        return value

    text = str(value).strip()
    if not text:
        return []

    if text.startswith("c(") and text.endswith(")"):
        return parse_r_vector(text)

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except (SyntaxError, ValueError):
        return [item.strip() for item in text.split(",") if item.strip()]


def parse_r_vector(text: str) -> list[str]:
    inner = text[2:-1].strip()
    quoted_items = re.findall(r'"((?:\\.|[^"\\])*)"', inner)
    if quoted_items:
        return [item.replace('\\"', '"').strip() for item in quoted_items]

    quoted_items = re.findall(r"'((?:\\.|[^'\\])*)'", inner)
    if quoted_items:
        return [item.replace("\\'", "'").strip() for item in quoted_items]

    return [item.strip() for item in inner.split(",") if item.strip()]


def parse_nutrition(value: Any) -> dict[str, Any] | list[Any]:
    values = parse_python_list(value)
    if len(values) == len(NUTRITION_FIELDS):
        return dict(zip(NUTRITION_FIELDS, values))
    return values


def build_food_recipe_nutrition(row: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "calories": "Calories",
        "fat": "FatContent",
        "saturated_fat": "SaturatedFatContent",
        "cholesterol": "CholesterolContent",
        "sodium": "SodiumContent",
        "carbohydrate": "CarbohydrateContent",
        "fiber": "FiberContent",
        "sugar": "SugarContent",
        "protein": "ProteinContent",
    }
    return {name: none_if_nan(row.get(source)) for name, source in fields.items()}


def parse_datetime(value: Any) -> datetime | None:
    if value is None or pd.isna(value):
        return None

    converted = pd.to_datetime(value, errors="coerce")
    if pd.isna(converted):
        return None
    return converted.to_pydatetime()


def none_if_nan(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "item") and callable(value.item):
        try:
            value = value.item()
        except (TypeError, ValueError):
            pass
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def clean_document(document: dict[str, Any]) -> dict[str, Any]:
    cleaned = {}
    for key, value in document.items():
        if isinstance(value, float) and pd.isna(value):
            cleaned[key] = None
        else:
            cleaned[key] = none_if_nan(value)
    return cleaned


def clean_recipe_row(row: dict[str, Any]) -> dict[str, Any]:
    if "RecipeId" in row:
        return clean_food_recipe_row(row)

    recipe_id = none_if_nan(row.get("id"))
    document = {
        "id": recipe_id,
        "recipe_id": recipe_id,
        "name": none_if_nan(row.get("name")),
        "minutes": none_if_nan(row.get("minutes")),
        "contributor_id": none_if_nan(row.get("contributor_id")),
        "submitted": parse_datetime(row.get("submitted")),
        "tags": parse_python_list(row.get("tags")),
        "nutrition": parse_nutrition(row.get("nutrition")),
        "n_steps": none_if_nan(row.get("n_steps")),
        "steps": parse_python_list(row.get("steps")),
        "description": none_if_nan(row.get("description")),
        "ingredients": parse_python_list(row.get("ingredients")),
        "n_ingredients": none_if_nan(row.get("n_ingredients")),
    }
    return clean_document(document)


def clean_review_row(row: dict[str, Any]) -> dict[str, Any]:
    if "ReviewId" in row or "DateSubmitted" in row:
        return clean_food_review_row(row)

    document = {
        "user_id": none_if_nan(row.get("user_id")),
        "recipe_id": none_if_nan(row.get("recipe_id")),
        "date": parse_datetime(row.get("date")),
        "rating": none_if_nan(row.get("rating")),
        "review": none_if_nan(row.get("review")),
    }
    return clean_document(document)


def clean_food_recipe_row(row: dict[str, Any]) -> dict[str, Any]:
    recipe_id = none_if_nan(row.get("RecipeId"))
    instructions = parse_python_list(row.get("RecipeInstructions"))
    ingredients = parse_python_list(row.get("RecipeIngredientParts"))
    keywords = parse_python_list(row.get("Keywords"))

    document = {
        "id": recipe_id,
        "recipe_id": recipe_id,
        "name": none_if_nan(row.get("Name")),
        "minutes": none_if_nan(row.get("TotalTime")),
        "contributor_id": none_if_nan(row.get("AuthorId")),
        "author_name": none_if_nan(row.get("AuthorName")),
        "submitted": parse_datetime(row.get("DatePublished")),
        "tags": keywords,
        "nutrition": build_food_recipe_nutrition(row),
        "n_steps": len(instructions),
        "steps": instructions,
        "description": none_if_nan(row.get("Description")),
        "ingredients": ingredients,
        "n_ingredients": len(ingredients),
        "category": none_if_nan(row.get("RecipeCategory")),
        "rating": none_if_nan(row.get("AggregatedRating")),
        "review_count": none_if_nan(row.get("ReviewCount")),
        "servings": none_if_nan(row.get("RecipeServings")),
        "yield": none_if_nan(row.get("RecipeYield")),
        "ingredient_quantities": parse_python_list(row.get("RecipeIngredientQuantities")),
        "images": parse_python_list(row.get("Images")),
        "cook_time": none_if_nan(row.get("CookTime")),
        "prep_time": none_if_nan(row.get("PrepTime")),
        "total_time": none_if_nan(row.get("TotalTime")),
    }
    return clean_document(document)


def clean_food_review_row(row: dict[str, Any]) -> dict[str, Any]:
    document = {
        "review_id": none_if_nan(row.get("ReviewId")),
        "user_id": none_if_nan(row.get("AuthorId")),
        "user_name": none_if_nan(row.get("AuthorName")),
        "recipe_id": none_if_nan(row.get("RecipeId")),
        "date": parse_datetime(row.get("DateSubmitted")),
        "date_modified": parse_datetime(row.get("DateModified")),
        "rating": none_if_nan(row.get("Rating")),
        "review": none_if_nan(row.get("Review")),
    }
    return clean_document(document)
