from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from scipy.stats import chi2_contingency
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


DEFAULT_DATASET_DIR = Path(__file__).resolve().parents[1] / "data" / "dataset_food"
NUTRITION_FEATURES = [
    "Calories",
    "FatContent",
    "SaturatedFatContent",
    "CholesterolContent",
    "SodiumContent",
    "CarbohydrateContent",
    "FiberContent",
    "SugarContent",
    "ProteinContent",
]


@dataclass(frozen=True)
class DatasetPaths:
    recipes: Path = DEFAULT_DATASET_DIR / "recipes.parquet"
    reviews: Path = DEFAULT_DATASET_DIR / "reviews.parquet"


def _read_table(path: Path, columns: list[str] | None = None, nrows: int | None = None) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Khong tim thay file dataset: {path}")

    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path, columns=columns)
        return df.head(nrows) if nrows else df

    return pd.read_csv(path, usecols=columns, nrows=nrows)


def load_recipes(path: str | Path | None = None, nrows: int | None = 80000) -> pd.DataFrame:
    columns = [
        "RecipeId",
        "Name",
        "RecipeCategory",
        "Keywords",
        "RecipeIngredientParts",
        "AggregatedRating",
        "ReviewCount",
        *NUTRITION_FEATURES,
    ]
    recipes_path = Path(path) if path else DatasetPaths().recipes
    df = _read_table(recipes_path, columns=columns, nrows=nrows)
    return clean_recipes(df)


def load_reviews(path: str | Path | None = None, nrows: int | None = 100000) -> pd.DataFrame:
    reviews_path = Path(path) if path else DatasetPaths().reviews
    return _read_table(reviews_path, nrows=nrows)


def clean_recipes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.dropna(subset=["RecipeId", "Name", "RecipeCategory", "RecipeIngredientParts"])
    df["RecipeId"] = df["RecipeId"].astype(int)
    df["RecipeCategory"] = df["RecipeCategory"].astype(str).str.strip()
    df["Name"] = df["Name"].astype(str).str.strip()
    df["AggregatedRating"] = pd.to_numeric(df["AggregatedRating"], errors="coerce")
    df["ReviewCount"] = pd.to_numeric(df["ReviewCount"], errors="coerce").fillna(0)

    for column in NUTRITION_FEATURES:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        df[column] = df[column].replace([np.inf, -np.inf], np.nan)

    return df


def normalize_item(value: object) -> str:
    return str(value).strip().lower()


def parse_list_column(value: object) -> list[str]:
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, list):
        return [normalize_item(item) for item in value if normalize_item(item)]
    if pd.isna(value):
        return []

    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        text = text.strip("[]")
    return [normalize_item(part.strip("'\" ")) for part in text.split(",") if part.strip("'\" ")]


def prepare_transactions(
    recipes: pd.DataFrame,
    min_items: int = 2,
    top_items: int = 60,
    max_transactions: int = 12000,
) -> pd.DataFrame:
    ingredient_lists = recipes["RecipeIngredientParts"].apply(parse_list_column)
    ingredient_lists = ingredient_lists[ingredient_lists.apply(len) >= min_items]

    if max_transactions:
        ingredient_lists = ingredient_lists.head(max_transactions)

    item_counts = ingredient_lists.explode().value_counts()
    selected_items = set(item_counts.head(top_items).index)
    rows = []
    for ingredients in ingredient_lists:
        rows.append({item: item in ingredients for item in selected_items})

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).fillna(False).astype(bool)


def run_apriori_analysis(
    recipes: pd.DataFrame,
    min_support: float = 0.03,
    min_confidence: float = 0.35,
    top_items: int = 60,
    max_transactions: int = 12000,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    basket = prepare_transactions(
        recipes,
        top_items=top_items,
        max_transactions=max_transactions,
    )
    if basket.empty:
        return pd.DataFrame(), pd.DataFrame()

    frequent_itemsets = apriori(basket, min_support=min_support, use_colnames=True)
    if frequent_itemsets.empty:
        return frequent_itemsets, pd.DataFrame()

    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=min_confidence,
    )
    rules = rules[["antecedents", "consequents", "support", "confidence", "lift"]]
    rules = rules.sort_values(["lift", "confidence"], ascending=False).reset_index(drop=True)
    rules["antecedents"] = rules["antecedents"].apply(format_itemset)
    rules["consequents"] = rules["consequents"].apply(format_itemset)
    return frequent_itemsets.sort_values("support", ascending=False), rules


def format_itemset(items: Iterable[str]) -> str:
    return ", ".join(sorted(str(item) for item in items))


def rating_group(value: float) -> str:
    if pd.isna(value):
        return "Chua co danh gia"
    if value >= 4.5:
        return "Rat cao"
    if value >= 3.5:
        return "Cao"
    if value >= 2.5:
        return "Trung binh"
    return "Thap"


def run_chi_square_analysis(
    recipes: pd.DataFrame,
    top_categories: int = 10,
) -> tuple[pd.DataFrame, float, float, int, pd.DataFrame]:
    df = recipes.dropna(subset=["RecipeCategory", "AggregatedRating"]).copy()
    df = df[df["ReviewCount"] > 0]
    top = df["RecipeCategory"].value_counts().head(top_categories).index
    df = df[df["RecipeCategory"].isin(top)]
    df["RatingGroup"] = df["AggregatedRating"].apply(rating_group)

    contingency_table = pd.crosstab(df["RecipeCategory"], df["RatingGroup"])
    if contingency_table.empty or contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        return contingency_table, 0.0, 1.0, 0, pd.DataFrame()

    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
    expected_df = pd.DataFrame(
        expected,
        index=contingency_table.index,
        columns=contingency_table.columns,
    )
    return contingency_table, float(chi2), float(p_value), int(dof), expected_df


def prepare_knn_data(
    recipes: pd.DataFrame,
    top_categories: int = 8,
) -> tuple[pd.DataFrame, pd.Series]:
    df = recipes.dropna(subset=["RecipeCategory", *NUTRITION_FEATURES]).copy()
    top = df["RecipeCategory"].value_counts().head(top_categories).index
    df = df[df["RecipeCategory"].isin(top)]
    X = df[NUTRITION_FEATURES]
    y = df["RecipeCategory"]
    return X, y


def train_knn_model(
    recipes: pd.DataFrame,
    k: int = 5,
    top_categories: int = 8,
    test_size: float = 0.25,
    random_state: int = 42,
) -> dict[str, object]:
    X, y = prepare_knn_data(recipes, top_categories=top_categories)
    if len(X) < 20 or y.nunique() < 2:
        raise ValueError("Khong du du lieu de train KNN.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("knn", KNeighborsClassifier(n_neighbors=k)),
        ]
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    return {
        "model": model,
        "features": NUTRITION_FEATURES,
        "accuracy": accuracy_score(y_test, y_pred),
        "classification_report": classification_report(y_test, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=sorted(y.unique())),
        "labels": sorted(y.unique()),
        "sample_count": len(X),
    }


def predict_recipe_category(model_info: dict[str, object], values: dict[str, float]) -> str:
    features = model_info["features"]
    model = model_info["model"]
    row = pd.DataFrame([[values[name] for name in features]], columns=features)
    return str(model.predict(row)[0])


def summarize_dataset(recipes: pd.DataFrame) -> dict[str, object]:
    return {
        "so_dong": len(recipes),
        "so_loai_mon": recipes["RecipeCategory"].nunique(),
        "so_mon_co_rating": int(recipes["AggregatedRating"].notna().sum()),
        "rating_trung_binh": float(recipes["AggregatedRating"].mean()),
        "review_trung_binh": float(recipes["ReviewCount"].mean()),
    }


if __name__ == "__main__":
    df = load_recipes(nrows=50000)
    print("Tong quan:", summarize_dataset(df))
    _, rules_df = run_apriori_analysis(df)
    print("\nTop Apriori rules:")
    print(rules_df.head(10).to_string(index=False))
    table, chi2, p_value, dof, _ = run_chi_square_analysis(df)
    print("\nChi-square contingency table:")
    print(table)
    print(f"chi2={chi2:.4f}, p_value={p_value:.6f}, dof={dof}")
    knn_info = train_knn_model(df)
    print(f"\nKNN accuracy: {knn_info['accuracy']:.4f}")
