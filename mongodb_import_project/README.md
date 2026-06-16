# MongoDB Import Project

Project import dataset Food.com Recipes and Reviews tu Kaggle vao MongoDB.

## Cau truc

```text
mongodb_import_project/
  data/
    RAW_recipes.csv
    RAW_interactions.csv
  main.py
  config.py
  mongo_connection.py
  data_loader.py
  data_cleaner.py
  import_to_mongo.py
  test_query.py
  requirements.txt
  README.md
```

## Dataset

Dat 2 file CSV vao thu muc `data/`.

Voi dataset ban dang co:

- `recipes.csv`
- `reviews.csv`


Code khong hard-code duong dan tuyet doi. Mac dinh no doc tu thu muc `data/` nam cung project.

## Cai dat

```powershell
cd D:\Python\DoAn-KhaiPhaDuLieu\mongodb_import_project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Chay import

Can dam bao MongoDB dang chay tai:

```text
mongodb://localhost:27017/
```

Chay import:

```powershell
python main.py
```

Xoa du lieu cu truoc khi import:

```powershell
python main.py --drop-old
```

Chi dinh thu muc data khac:

```powershell
python main.py --data-dir "D:\Download\food-com-recipes-and-user-interactions"
```

## Database

Database duoc lay bang cu phap:

```python
db = client["DuLieu-KPDL"]
```

Collections:

- `recipes`
- `reviews`

## Xu ly du lieu

- `ingredients`, `tags`, `steps` duoc chuyen thanh list.
- `nutrition` duoc chuyen thanh object neu du 7 gia tri dinh duong.
- `NaN` duoc chuyen thanh `None`.
- `submitted` va `date` duoc chuyen thanh datetime neu parse duoc.
- Du lieu duoc insert theo batch 1000 document.
- Co index thuong va text index theo yeu cau.

## Kiem tra sau import

```powershell
python test_query.py
```
