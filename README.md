# DoAn-KhaiPhaDuLieu - Food Recipes Mining

Project khai pha du lieu mon an su dung dataset trong `D:\Download\dataset_food`.

## Chuc nang

- Doc va tien xu ly dataset recipes/reviews dang Parquet hoac CSV.
- Apriori: tim luat ket hop giua cac nguyen lieu mon an.
- Chi-square: kiem dinh moi lien he giua nhom danh gia va loai mon an.
- KNN: du doan `RecipeCategory` tu cac chi so dinh duong.
- Giao dien Streamlit de xem du lieu, chay thuat toan va nhap mau du doan.

## Cau truc

```text
DoAn-KhaiPhaDuLieu/
  src/
    app.py
    mining_utils.py
  data/
  outputs/
  requirements.txt
  README.md
```

## Cai dat

```powershell
cd D:\Python\DoAn-KhaiPhaDuLieu
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Chay ung dung

```powershell
streamlit run src\app.py
```

Neu muon chay nhanh tren terminal:

```powershell
python src\mining_utils.py
```

## Dataset mac dinh

Ung dung mac dinh doc:

- `D:\Download\dataset_food\recipes.parquet`
- `D:\Download\dataset_food\reviews.parquet`

Co the doi duong dan trong sidebar cua Streamlit.
