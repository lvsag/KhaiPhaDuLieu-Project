from pymongo import MongoClient
from datetime import datetime

def get_db():
    client = MongoClient("mongodb://127.0.0.1:27017/")
    return client["QuanLyNhaSach"]

db = get_db()


# THEM: Dong bo collection Categories tu sach hien co de combobox the loai linh hoat hon.
def sync_categories_from_books():
    existing_categories = {
        book.get("category")
        for book in db["Books"].find({}, {"category": 1})
        if book.get("category")
    }
    for category in existing_categories:
        db["Categories"].update_one(
            {"name": category},
            {"$setOnInsert": {"name": category}},
            upsert=True
        )


def get_categories():
    sync_categories_from_books()
    categories = [
        item["name"]
        for item in db["Categories"].find({}).sort("name", 1)
        if item.get("name")
    ]
    return categories or ["Kỹ năng sống", "Truyện tranh", "Tiểu thuyết", "Sách giáo khoa"]


def ensure_category(category_name):
    category_name = (category_name or "").strip()
    if not category_name:
        return None

    db["Categories"].update_one(
        {"name": category_name},
        {"$setOnInsert": {"name": category_name}},
        upsert=True
    )
    return category_name

# Khởi tạo Admin mặc định nếu chưa có
if db["Users"].count_documents({"role": "admin"}) == 0:
    db["Users"].insert_one({
        "username": "admin",
        "name": "Quản Trị Viên Cao Cấp",
        "role": "admin",
        "password": "admin",
        "gender": "Nam", "age": 30, "income": 15000000
    })

# --- Nghiệp vụ Hóa đơn ---
def save_order(user, cart, total_pay):
    # SUA: Kiem tra va tru ton kho truoc khi luu hoa don.
    quantities_by_book = {}
    for item in cart:
        book_id = int(item["_id"])
        quantities_by_book[book_id] = quantities_by_book.get(book_id, 0) + 1

    for book_id, quantity in quantities_by_book.items():
        book = db["Books"].find_one({"_id": book_id})
        if not book:
            raise ValueError("Sách không còn tồn tại trong hệ thống.")
        if int(book.get("stock", 0)) < quantity:
            raise ValueError(f"Sách '{book.get('title')}' không đủ số lượng tồn kho.")

    for book_id, quantity in quantities_by_book.items():
        db["Books"].update_one(
            {"_id": book_id},
            {"$inc": {"stock": -quantity}}
        )

    items_to_save = []
    for item in cart:
        items_to_save.append({
            "book_id": int(item["_id"]),
            "title": item["title"],
            "price": int(item["price"]),
            "quantity": 1
        })
        
    ma_hoa_don = f"HD-{int(datetime.now().timestamp())}"
    ngay_hien_tai = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    new_order = {
        "order_id": ma_hoa_don,
        "date": ngay_hien_tai,
        "customer_username": user["username"], # Lưu để biết hóa đơn của ai
        "customer_name": user["name"],
        "customer_gender": user["gender"],
        "customer_age": int(user["age"]),
        "customer_income": int(user["income"]),
        "main_category": cart[0]["category"],
        "items": items_to_save,
        "total_amount": int(total_pay),
        "deleted_by_user": False # Thuộc tính quan trọng: User xóa thì chuyển thành True
    }
    db["Orders"].insert_one(new_order)
    return new_order

def get_user_orders(username):
    # Khách hàng chỉ lấy những hóa đơn chưa bị họ bấm ẩn (deleted_by_user = False)
    return list(db["Orders"].find({"customer_username": username, "deleted_by_user": False}))

def get_all_orders_for_admin():
    # Admin có quyền cao nhất, lấy TẤT CẢ hóa đơn, bất kể user đã bấm xóa hay chưa
    return list(db["Orders"].find({}))

def soft_delete_order(order_id):
    # Chỉ đánh dấu là đã xóa trên giao diện user, DB vẫn giữ nguyên để khai phá dữ liệu
    db["Orders"].update_one({"order_id": order_id}, {"$set": {"deleted_by_user": True}})

def get_books_by_page(page_number=1, items_per_page=25):
    skips = (page_number - 1) * items_per_page
    cursor = db["Books"].find({}).skip(skips).limit(items_per_page)
    
    # Tính tổng số sách đang có để tính toán tổng số trang ở giao diện
    total_books = db["Books"].count_documents({})
    total_pages = (total_books + items_per_page - 1) // items_per_page
    
    return list(cursor), total_pages


# THEM: Cap nhat thong tin sach tu man hinh admin.
def update_book(book_id, title, category, price, image, stock=0):
    ensure_category(category)
    db["Books"].update_one(
        {"_id": int(book_id)},
        {
            "$set": {
                "title": title,
                "category": category,
                "price": int(price),
                "image": image or "hinh1.jpg",
                "stock": int(stock)
            }
        }
    )


# THEM: Xoa sach trong phan quan tri.
def delete_book(book_id):
    db["Books"].delete_one({"_id": int(book_id)})


# THEM: Doi mat khau tai khoan khach/admin neu mat khau cu dung.
def change_user_password(username, old_password, new_password):
    result = db["Users"].update_one(
        {"username": username, "password": old_password},
        {"$set": {"password": new_password}}
    )
    return result.modified_count == 1
