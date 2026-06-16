from __future__ import annotations

from pathlib import Path

import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib import pyplot as plt

import mining_utils as mining


st.set_page_config(
    page_title="Food Mining",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def cached_recipes(path: str, nrows: int) -> pd.DataFrame:
    return mining.load_recipes(path=path, nrows=nrows)


@st.cache_resource(show_spinner=False)
def cached_knn(path: str, nrows: int, k: int, top_categories: int) -> dict[str, object]:
    recipes = mining.load_recipes(path=path, nrows=nrows)
    return mining.train_knn_model(recipes, k=k, top_categories=top_categories)


st.title("Khai phá dữ liệu công thức món ăn")

with st.sidebar:
    st.header("Dữ liệu")
    recipes_path = st.text_input(
        "File recipes",
        value=str(mining.DEFAULT_DATASET_DIR / "recipes.parquet"),
    )
    nrows = st.slider("Số dòng đọc vào", 5000, 200000, 80000, step=5000)
    st.caption("Dùng Parquet sẽ nhanh hơn CSV với dataset lớn.")

    st.header("Tham số chung")
    top_categories = st.slider("Số loại món phổ biến", 3, 20, 8)

if not Path(recipes_path).exists():
    st.error(f"Không tìm thấy file: {recipes_path}")
    st.stop()

with st.spinner("Đang đọc và tiền xử lý dataset..."):
    recipes = cached_recipes(recipes_path, nrows)

summary = mining.summarize_dataset(recipes)
metric_cols = st.columns(5)
metric_cols[0].metric("Số dòng", f"{summary['so_dong']:,}")
metric_cols[1].metric("Loại món", f"{summary['so_loai_mon']:,}")
metric_cols[2].metric("Có rating", f"{summary['so_mon_co_rating']:,}")
metric_cols[3].metric("Rating TB", f"{summary['rating_trung_binh']:.2f}")
metric_cols[4].metric("Review TB", f"{summary['review_trung_binh']:.1f}")

tab_data, tab_apriori, tab_chi, tab_knn = st.tabs(
    ["Dữ liệu", "Apriori", "Chi-square", "KNN"]
)

with tab_data:
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Mẫu dữ liệu")
        st.dataframe(
            recipes[
                [
                    "RecipeId",
                    "Name",
                    "RecipeCategory",
                    "AggregatedRating",
                    "ReviewCount",
                    "Calories",
                    "ProteinContent",
                    "RecipeIngredientParts",
                ]
            ].head(100),
            use_container_width=True,
        )
    with right:
        st.subheader("Top loại món")
        category_counts = recipes["RecipeCategory"].value_counts().head(12)
        st.bar_chart(category_counts)

with tab_apriori:
    st.subheader("Luật kết hợp nguyên liệu")
    c1, c2, c3, c4 = st.columns(4)
    min_support = c1.slider("Min support", 0.01, 0.20, 0.03, step=0.01)
    min_confidence = c2.slider("Min confidence", 0.10, 0.90, 0.35, step=0.05)
    top_items = c3.slider("Top nguyên liệu", 20, 120, 60, step=10)
    max_transactions = c4.slider("Số giao dịch", 1000, 30000, 12000, step=1000)

    if st.button("Chạy Apriori", type="primary"):
        with st.spinner("Đang tìm tập phổ biến và luật kết hợp..."):
            frequent_itemsets, rules = mining.run_apriori_analysis(
                recipes,
                min_support=min_support,
                min_confidence=min_confidence,
                top_items=top_items,
                max_transactions=max_transactions,
            )
        st.write(f"Số tập phổ biến: {len(frequent_itemsets):,}")
        st.write(f"Số luật kết hợp: {len(rules):,}")
        if rules.empty:
            st.warning("Không có luật nào với bộ tham số hiện tại. Hãy giảm support/confidence.")
        else:
            st.dataframe(rules.head(100), use_container_width=True)

with tab_chi:
    st.subheader("Kiểm định Chi-square")
    table, chi2, p_value, dof, expected = mining.run_chi_square_analysis(
        recipes,
        top_categories=top_categories,
    )
    st.write("Giả thuyết H0: nhóm đánh giá và loại món ăn độc lập với nhau.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Chi-square", f"{chi2:.4f}")
    c2.metric("p-value", f"{p_value:.6f}")
    c3.metric("Bậc tự do", dof)
    if p_value < 0.05:
        st.success("p-value < 0.05: bác bỏ H0, có mối liên hệ có ý nghĩa thống kê.")
    else:
        st.info("p-value >= 0.05: chưa đủ bằng chứng để bác bỏ H0.")

    st.dataframe(table, use_container_width=True)
    if not table.empty:
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.heatmap(table, annot=True, fmt="d", cmap="YlGnBu", ax=ax)
        ax.set_xlabel("Nhóm đánh giá")
        ax.set_ylabel("Loại món")
        st.pyplot(fig)

with tab_knn:
    st.subheader("KNN dự đoán loại món từ dinh dưỡng")
    k = st.slider("Số láng giềng K", 1, 21, 5, step=2)

    with st.spinner("Đang train KNN..."):
        try:
            model_info = cached_knn(recipes_path, nrows, k, top_categories)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

    c1, c2 = st.columns(2)
    c1.metric("Accuracy", f"{model_info['accuracy']:.2%}")
    c2.metric("Số mẫu train/test", f"{model_info['sample_count']:,}")

    with st.expander("Báo cáo phân lớp"):
        st.text(model_info["classification_report"])

    st.write("Nhập thông số dinh dưỡng cho một món ăn mới:")
    values = {}
    cols = st.columns(3)
    defaults = {
        "Calories": 300.0,
        "FatContent": 10.0,
        "SaturatedFatContent": 3.0,
        "CholesterolContent": 40.0,
        "SodiumContent": 400.0,
        "CarbohydrateContent": 35.0,
        "FiberContent": 4.0,
        "SugarContent": 8.0,
        "ProteinContent": 12.0,
    }
    for index, feature in enumerate(model_info["features"]):
        values[feature] = cols[index % 3].number_input(
            feature,
            min_value=0.0,
            value=defaults.get(feature, 0.0),
            step=1.0,
        )

    if st.button("Dự đoán loại món", type="primary"):
        prediction = mining.predict_recipe_category(model_info, values)
        st.success(f"Loại món dự đoán: {prediction}")
