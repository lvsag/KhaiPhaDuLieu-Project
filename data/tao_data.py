from pymongo import MongoClient
import random
from datetime import datetime, timedelta

# Kết nối tới MongoDB
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["QuanLyNhaSach"]

db["Books"].drop()
db["Orders"].drop()

print("🔄 Đang khởi tạo dữ liệu sách kèm thuộc tính hình ảnh...")

the_loai_goc = {
    "Kỹ năng sống": ["Đắc nhân tâm", "Đọc vị bất kỳ ai", "Hạt giống tâm hồn", "Tư duy tối ưu", "Thói quen thành công", "Kiên trì là tất cả"],
    "Truyện tranh": ["Doraemon Tập", "Conan Tập", "One Piece Tập", "Naruto Tập", "Dragon Ball Tập"],
    "Tiểu thuyết": ["Nhà giả kim", "Mắt biếc", "Cho tôi một vé đi tuổi thơ", "Rừng Na Uy", "Bố già"],
    "Sách giáo khoa": ["Toán Học", "Ngữ Văn", "Vật Lý", "Hóa Học", "Sinh Học", "Lịch Sử"]
}

danh_sach_sach = []
book_id = 1
SO_LUONG_ANH_MAU = 30  # Bạn có bao nhiêu ảnh trong thư mục hinh_anh_sach thì điền vào đây
SACH_HET_HANG = {3, 17, 42}  # THEM: 1-3 cuon het hang de test nut mua bi disable.

ANH_THEO_TEN_SACH = {
    "Doraemon Tập 1": "hinh14.jpg",
    "Doraemon Tập 2": "hinh15.jpg",
    "Doraemon Tập 3": "hinh16.jpg",
    "Doraemon Tập 4": "hinh17.jpg",
    "Doraemon Tập 5": "hinh18.jpg",
    "Conan Tập 1": "hinh5.jpg",
    "Conan Tập 2": "hinh19.jpg",
    "Conan Tập 3": "hinh20.jpg",
    "Conan Tập 4": "hinh21.jpg",
    "Conan Tập 5": "hinh22.jpg",
    "One Piece Tập 1": "hinh23.jpg",
    "One Piece Tập 2": "hinh24.jpg",
    "One Piece Tập 3": "hinh25.jpg",
    "One Piece Tập 4": "hinh26.jpg",
    "One Piece Tập 5": "hinh27.jpg",
    "Naruto Tập 1": "hinh6.jpg",
    "Naruto Tập 2": "hinh28.jpg",
    "Naruto Tập 3": "hinh29.jpg",
    "Naruto Tập 4": "hinh30.jpg",
    "Đắc nhân tâm": "hinh2.jpg",
    "Đọc vị bất kỳ ai": "hinh3.jpg",
    "Hạt giống tâm hồn": "hinh4.jpg",
    "Tư duy tối ưu": "hinh11.jpg",
    "Thói quen thành công": "hinh12.jpg",
    "Kiên trì là tất cả": "hinh13.jpg",
    "Nhà giả kim": "hinh7.jpg",
    "Mắt biếc": "hinh8.jpg",
    "Vật Lý Lớp 12": "hinh9.jpg",
    "Sinh Học Lớp 12": "hinh10.jpg",
}


def lay_anh_theo_ten(ten_sach):
    return ANH_THEO_TEN_SACH.get(ten_sach, "hinh1.jpg")

for the_loai, cac_tua_de in the_loai_goc.items():
    for tua in cac_tua_de:
        if the_loai == "Truyện tranh":
            for tap in range(1, 6):
                ten_sach = f"{tua} {tap}"
                danh_sach_sach.append({
                    "_id": book_id,
                    "title": ten_sach,
                    "category": the_loai,
                    "price": random.choice([25000, 30000, 35000]),
                    "image": lay_anh_theo_ten(ten_sach),  # SUA: Anh khop voi ten sach, khong random.
                    "stock": 0 if book_id in SACH_HET_HANG else random.randint(10, 20)  # THEM: Ton kho sach.
                })
                book_id += 1
        elif the_loai == "Sách giáo khoa":
            for lop in [10, 11, 12]:
                ten_sach = f"{tua} Lớp {lop}"
                danh_sach_sach.append({
                    "_id": book_id,
                    "title": ten_sach,
                    "category": the_loai,
                    "price": random.randint(15000, 22000),
                    "image": lay_anh_theo_ten(ten_sach),  # SUA: Vi du Sinh Hoc Lop 12 dung hinh10.jpg.
                    "stock": 0 if book_id in SACH_HET_HANG else random.randint(10, 20)  # THEM: Ton kho sach.
                })
                book_id += 1
        else:
            danh_sach_sach.append({
                "_id": book_id,
                "title": tua,
                "category": the_loai,
                "price": random.randint(50000, 120000),
                "image": lay_anh_theo_ten(tua),  # SUA: Anh khop voi ten sach, khong random.
                "stock": 0 if book_id in SACH_HET_HANG else random.randint(10, 20)  # THEM: Ton kho sach.
            })
            book_id += 1

db["Books"].insert_many(danh_sach_sach)
print(f"✅ Đã nạp {len(danh_sach_sach)} sách kèm tên ảnh ngẫu nhiên (hinhX.jpg) vào MongoDB!")

cac_don_hang = []
ngay_goc = datetime.now()

# Tim sach theo ten thay vi dung index/ID co the sai khi danh sach thay doi.
def tim_sach(tieu_de):
    return next(s for s in danh_sach_sach if s["title"] == tieu_de)


# SUA: Dinh nghia combo dung de Apriori co luat ro rang.
combo_truyen_tranh = [
    tim_sach("Doraemon Tập 1"),
    tim_sach("Conan Tập 1"),
    tim_sach("One Piece Tập 1")
]
combo_ky_nang = [
    tim_sach("Đắc nhân tâm"),
    tim_sach("Đọc vị bất kỳ ai")
]

for i in range(1, 101):
    # Tạo ngày mua ngẫu nhiên trong vòng 30 ngày qua
    ngay_mua = ngay_goc - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
    ma_hd = f"HD-MOCK-{1000 + i}"
    
    # Thiết lập thuộc tính khách hàng ngẫu nhiên
    gioi_tinh = random.choice(["Nam", "Nữ"])
    username_mock = f"khachhang_{i}@gmail.com"
    
    # Tạo quy luật nhân trắc học (Để thuật toán KNN và Chi-Square hoạt động hiệu quả)
    if gioi_tinh == "Nữ":
        # Giả định: Nữ giới trẻ tuổi, thu nhập vừa phải thích Tiểu thuyết/Truyện tranh
        tuoi = random.randint(15, 25)
        thu_nhap = random.randint(2000000, 7000000)
        the_loai_chinh = random.choice(["Tiểu thuyết", "Truyện tranh"])
    else:
        # Giả định: Nam giới lớn tuổi hơn, thu nhập cao hơn thích Kỹ năng sống
        tuoi = random.randint(26, 45)
        thu_nhap = random.randint(8000000, 25000000)
        the_loai_chinh = random.choice(["Kỹ năng sống", "Sách giáo khoa"])
        
    # Cai san mot so hoa don combo de Apriori dat min_support >= 0.05.
    combo_bat_buoc = None
    if i <= 12:
        the_loai_chinh = "Kỹ năng sống"
        combo_bat_buoc = combo_ky_nang
    elif i <= 24:
        the_loai_chinh = "Truyện tranh"
        combo_bat_buoc = combo_truyen_tranh

    # Nhặt đồ vào giỏ hàng dựa trên thể loại chính đã phân lớp
    items_trong_don = []
    sach_theo_the_loai = [s for s in danh_sach_sach if s["category"] == the_loai_chinh]
    
    if combo_bat_buoc:
        # Hoa don combo co nhieu san pham de Apriori sinh luat mua kem.
        for sach in combo_bat_buoc:
            items_trong_don.append({
                "book_id": sach["_id"],
                "title": sach["title"],
                "price": sach["price"],
                "quantity": 1
            })
        sach_chon = combo_bat_buoc[0]
    else:
        # Chọn ngẫu nhiên sách trong thể loại ưa thích
        sach_chon = random.choice(sach_theo_the_loai)
        items_trong_don.append({
            "book_id": sach_chon["_id"],
            "title": sach_chon["title"],
            "price": sach_chon["price"],
            "quantity": 1
        })
    
    # Neu mua Doraemon Tap 1 thi co xac suat mua kem Conan/One Piece Tap 1.
    if combo_bat_buoc is None and sach_chon["title"] == "Doraemon Tập 1" and random.random() < 0.8:
        sach_kem = random.choice(combo_truyen_tranh[1:])
        items_trong_don.append({
            "book_id": sach_kem["_id"], "title": sach_kem["title"],
            "price": sach_kem["price"], "quantity": 1
        })
        
    # Neu mua Dac nhan tam thi mua kem dung sach Doc vi bat ky ai.
    if combo_bat_buoc is None and sach_chon["title"] == "Đắc nhân tâm" and random.random() < 0.75:
        sach_kem = combo_ky_nang[1]
        items_trong_don.append({
            "book_id": sach_kem["_id"], "title": sach_kem["title"],
            "price": sach_kem["price"], "quantity": 1
        })

    # Tính tổng tiền của hóa đơn mẫu này
    tong_tien = sum(item["price"] * item["quantity"] for item in items_trong_don)
    
    don_hang_doc = {
        "order_id": ma_hd,
        "date": ngay_mua.strftime("%d/%m/%Y %H:%M:%S"),
        "customer_username": username_mock,
        "customer_name": f"Khách Hàng Mẫu {i}",
        "customer_gender": gioi_tinh,
        "customer_age": tuoi,
        "customer_income": thu_nhap,
        "main_category": the_loai_chinh,
        "items": items_trong_don,
        "total_amount": tong_tien,
        "deleted_by_user": False # Để hiển thị đầy đủ trên giao diện ban đầu
    }
    cac_don_hang.append(don_hang_doc)

db["Orders"].insert_many(cac_don_hang)
print(f"Đã sinh thành công 100 hóa đơn mẫu vào bộ sưu tập 'Orders'.")
print("Toàn bộ cơ sở dữ liệu NoSQL đã sẵn sàng phục vụ các thuật toán khai phá!")
