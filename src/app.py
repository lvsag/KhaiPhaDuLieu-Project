import streamlit as st
import pandas as pd
import base64
import re
import importlib
from datetime import datetime, time
from pathlib import Path
import database as db_handler
import mining_untils as mining

# SUA: Ep reload database.py de Streamlit khong giu module cu khi vua them ham moi.
db_handler = importlib.reload(db_handler)

# SUA: Lay duong dan anh theo vi tri file app.py, khong phu thuoc terminal dang chay o dau.
BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "hinh_anh_sach"


# SUA: Gom logic tim anh vao helper de upload/hien thi dung duong dan.
def get_book_image_path(book):
    image_name = book.get("image") or "hinh1.jpg"
    image_path = IMAGE_DIR / image_name
    fallback_path = IMAGE_DIR / "hinh1.jpg"

    if image_path.exists():
        return image_path
    return fallback_path if fallback_path.exists() else None


# THEM: Render anh bang HTML de moi anh sach co cung khung kich thuoc.
def show_book_image(book, caption="Anh sach", compact=False):
    image_path = get_book_image_path(book)
    if not image_path:
        st.warning(f"Khong tim thay thu muc anh: {IMAGE_DIR}")
        return

    image_bytes = image_path.read_bytes()
    image_data = base64.b64encode(image_bytes).decode("utf-8")
    mime_type = {
        ".png": "image/png",
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg"
    }.get(image_path.suffix.lower(), "image/jpeg")
    height = 170 if compact else 300
    st.markdown(
        f"""
        <div class="book-image-frame" style="height:{height}px">
            <img src="data:{mime_type};base64,{image_data}" alt="{caption}">
        </div>
        <div class="book-image-caption">{caption}</div>
        """,
        unsafe_allow_html=True
    )


# THEM: Tao the img base64 dung trong card hoa don.
def get_book_image_tag(book):
    image_path = get_book_image_path(book)
    if not image_path:
        return "<span>Khong co anh</span>"

    image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    mime_type = {
        ".png": "image/png",
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg"
    }.get(image_path.suffix.lower(), "image/jpeg")
    title = book.get("title", "Anh sach")
    return f'<img src="data:{mime_type};base64,{image_data}" alt="{title}">'


# THEM: Luu anh upload vao thu muc hinh_anh_sach va tra ve ten file de luu DB.
def save_uploaded_book_image(uploaded_file, book_title, book_id):
    if uploaded_file is None:
        return None

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
        suffix = ".jpg"

    safe_title = re.sub(r"[^a-zA-Z0-9]+", "_", book_title.strip()).strip("_").lower()
    safe_title = safe_title or f"sach_{book_id}"
    filename = f"{book_id}_{safe_title}{suffix}"
    save_path = IMAGE_DIR / filename
    save_path.write_bytes(uploaded_file.getbuffer())
    return filename


# THEM: Parse ngay hoa don dang dd/mm/YYYY HH:MM:SS de loc theo ngay gio trong admin.
def parse_order_datetime(date_text):
    try:
        return datetime.strptime(date_text, "%d/%m/%Y %H:%M:%S")
    except (TypeError, ValueError):
        return None


# THEM: Dem so luong cua mot sach da nam trong gio hang hien tai.
def count_book_in_cart(book_id):
    return sum(
        1
        for item in st.session_state.get("cart", [])
        if int(item.get("_id")) == int(book_id)
    )


# THEM: Kiem tra sach con co the them vao gio hay khong.
def can_add_to_cart(book):
    stock = int(book.get("stock", 0))
    return stock > count_book_in_cart(book["_id"])

st.set_page_config(
    page_title="VouBook",
    page_icon="📚",
    layout="wide"
)

st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

.stApp {
    background: #f4f7fb;
    color: #1f2937;
}

/* HEADER */
.main-header {
    background: linear-gradient(135deg,#0f766e,#2563eb);
    padding: 24px 28px;
    border-radius: 14px;
    margin-bottom: 20px;
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.16);
}

.main-header h1 {
    color: white;
    margin: 0;
    font-size: 40px;
}

.main-header p {
    color: #e0f2fe;
    margin-top: 5px;
}

/* BUTTON */
.stButton > button {
    width: 100%;
    border-radius: 10px;
    border: none;
    padding: 10px;
    font-weight: 600;
    background-color: #0f766e;
    color: white;
    transition: 0.2s;
}

.stButton > button:hover {
    background-color: #115e59;
    transform: scale(1.02);
}

/* CARD */
.book-card {
    background: white;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 18px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 8px 20px rgba(15,23,42,0.08);
    transition: 0.2s;
}

.book-card:hover {
    transform: translateY(-4px);
}

.book-title {
    font-size: 18px;
    font-weight: bold;
    color: #111827 !important;
    margin-bottom: 8px;
    min-height: 50px;
    overflow: hidden;
}

.book-category {
    background: #ecfeff;
    color: #0f766e;
    padding: 4px 10px;
    border-radius: 999px;
    display: inline-block;
    font-size: 13px;
    margin-bottom: 12px;
}

.book-price {
    color: #dc2626;
    font-size: 20px;
    font-weight: bold;
}

.book-stock {
    color: #374151;
    font-size: 14px;
    font-weight: 600;
    margin-top: 8px;
}

.book-stock.out {
    color: #dc2626;
}

.book-image-frame {
    width: 100%;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.book-image-frame img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

.book-image-caption {
    color: #6b7280;
    font-size: 13px;
    text-align: center;
    margin: 8px 0 12px;
    min-height: 18px;
}

.panel-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 8px 20px rgba(15,23,42,0.06);
}

.order-card {
    background: #ffffff;
    border: 1px solid #dbe4ef;
    border-left: 5px solid #0f766e;
    border-radius: 12px;
    padding: 14px 16px;
    margin: 10px 0;
    color: #1f2937;
    display: grid;
    grid-template-columns: minmax(0, 1fr) 180px;
    gap: 18px;
    align-items: stretch;
}

.order-card h4 {
    margin: 0 0 8px 0;
    color: #0f172a;
}

.order-total {
    color: #dc2626;
    font-size: 20px;
    font-weight: 700;
}

.order-cover {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    min-height: 220px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.order-cover img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

@media (max-width: 800px) {
    .order-card {
        grid-template-columns: 1fr;
    }
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background-color: white;
    border-right: 1px solid #ddd;
}

/* EXPANDER */
div[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid #dbe4ef;
    border-radius: 12px;
}

.streamlit-expanderHeader {
    font-size: 17px;
    font-weight: bold;
    color: #0f172a;
}

/* FORM */
div[data-baseweb="input"] {
    border-radius: 10px;
}

div[data-testid="stDataFrame"] {
    background: white;
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

# SESSION
if "page" not in st.session_state:
    st.session_state.page = "Trang chủ"

if "user" not in st.session_state:
    st.session_state.user = None

if "cart" not in st.session_state:
    st.session_state.cart = []

# THEM: Luu bo loc trong session_state de nut "Xoa bo loc" dua giao dien ve mac dinh.
if "filter_category" not in st.session_state:
    st.session_state.filter_category = "Tất cả"

if "filter_letter" not in st.session_state:
    st.session_state.filter_letter = "Tất cả"

if "filter_search" not in st.session_state:
    st.session_state.filter_search = ""

# HÀM CHUYỂN TRANG
def chyen_trang(page_name):
    st.session_state.page = page_name
    st.rerun()


# THEM: Ham reset bo loc tim sach.
def reset_book_filters():
    st.session_state.filter_category = "Tất cả"
    st.session_state.filter_letter = "Tất cả"
    st.session_state.filter_search = ""

# HEADER
st.markdown("""
<div class='main-header'>
    <h1>📚 VouBook</h1>
    <p>Hệ thống quản lý và bán sách thông minh</p>
</div>
""", unsafe_allow_html=True)

# NAVIGATION
nav1, nav2, nav3, nav4, nav5 = st.columns([3,1,1,1,1])

with nav1:
    if st.button("🏠 Trang chủ"):
        chyen_trang("Trang chủ")

if st.session_state.user and st.session_state.user.get("role") == "admin":
    with nav2:
        if st.button("⚙️ Quản trị"):
            chyen_trang("Admin")
else:
    with nav2:
        if st.button(f"🛒 Giỏ hàng ({len(st.session_state.cart)})"):
            chyen_trang("Giỏ hàng")

if st.session_state.user is None:
    with nav3:
        if st.button("🔐 Đăng nhập"):
            chyen_trang("Đăng nhập")

    with nav4:
        if st.button("📝 Đăng ký"):
            chyen_trang("Đăng ký")
else:
    with nav3:
        st.markdown(f"### 👋 {st.session_state.user['name']}")

    with nav4:
        if st.button("🚪 Đăng xuất"):
            st.session_state.user = None
            st.session_state.cart = []
            chyen_trang("Trang chủ")

    if st.session_state.user.get("role") != "admin":
        with nav5:
            if st.button("Tài khoản"):
                chyen_trang("Tài khoản")

st.markdown("---")

# TRANG CHỦ
if st.session_state.page == "Trang chủ":

    # LỊCH SỬ HÓA ĐƠN
    if st.session_state.user and st.session_state.user.get("role") != "admin":

        st.subheader("📜 Lịch sử hóa đơn")

        my_orders = db_handler.get_user_orders(
            st.session_state.user["username"]
        )

        if not my_orders:
            st.info("Bạn chưa có hóa đơn nào.")
        else:
            for ord_doc in my_orders:

                with st.expander(
                    f"🧾 {ord_doc['order_id']} | {ord_doc['date']} | {ord_doc['total_amount']:,} VNĐ"
                ):

                    for it in ord_doc['items']:
                        st.write(
                            f"• {it['title']} x {it['quantity']} - {it['price']:,} đ"
                        )

                    if st.button(
                        "Xóa khỏi lịch sử",
                        key=f"del_inv_{ord_doc['order_id']}"  # SUA: key rieng cho tung hoa don, tranh trung key Streamlit.
                    ):
                        db_handler.soft_delete_order(ord_doc['order_id'])
                        st.success("Đã xóa hóa đơn.")
                        st.rerun()

    # GỢI Ý KNN
    if st.session_state.user and st.session_state.user.get("role") != "admin":

        try:
            gu_du_doan = mining.predict_customer_group_knn(
                st.session_state.user["age"],
                st.session_state.user["income"]
            )

            st.success(
                f"🎯 Gợi ý theo KNN: {gu_du_doan}"
            )

            rec_books = list(
                db_handler.db["Books"].find(
                    {"category": gu_du_doan}
                )
            )[:3]

            cols = st.columns(3)

            for idx, b in enumerate(rec_books):

                with cols[idx]:
                    
                    # SUA: Hien thi anh bang duong dan tuyet doi tu helper show_book_image().
                    show_book_image(b, caption=b["title"])

                    st.markdown(f"""
                    <div class='book-card'>
                        <div class='book-title'>{b['title']}</div>
                        <div class='book-category'>{b['category']}</div>
                        <div class='book-price'>{b['price']:,} VNĐ</div>
                        <div class='book-stock {"out" if int(b.get("stock", 0)) <= 0 else ""}'>
                            {"Hết hàng" if int(b.get("stock", 0)) <= 0 else f"Còn {int(b.get('stock', 0))} cuốn"}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    can_buy_rec = can_add_to_cart(b)
                    if st.button(
                        "➕ Thêm nhanh",
                        key=f"rec_{b['_id']}",
                        disabled=not can_buy_rec
                    ):
                        st.session_state.cart.append(b)
                        st.rerun()
                    if not can_buy_rec:
                        st.caption("Hết hàng hoặc đã lấy đủ số lượng trong giỏ.")

        except Exception as ex:
            # SUA: Hien loi KNN thay vi bo qua im lang.
            st.warning(f"Khong the tao goi y KNN: {ex}")

    st.subheader("📚 Tất cả sản phẩm")

    left, right = st.columns([1,4])

    with left:

        st.markdown("### 📂 Danh mục")

        selected_cat = st.radio(
            "",
            ["Tất cả"] + db_handler.get_categories(),
            key="filter_category"
        )

        st.markdown("---")
        st.markdown("### 🔤 Tìm theo chữ cái")

        # Danh sách chữ cái A-Z + Tất cả
        alphabet = ["Tất cả"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        selected_letter = st.selectbox("Chữ cái đầu tiên", alphabet, key="filter_letter")

        # Ô tìm kiếm tên sách
        st.markdown("### 🔍 Tìm kiếm")
        search_text = st.text_input("Nhập tên sách...", placeholder="VD: Đắc Nhân Tâm", key="filter_search")
        btn_search = st.button("🔍 Tìm kiếm")
        # THEM: Nut xoa bo loc tim sach ve trang thai ban dau.
        st.button("Xóa bộ lọc", on_click=reset_book_filters)
    with right:

        # Lọc theo danh mục
        q = {} if selected_cat == "Tất cả" else {
            "category": selected_cat
        }

        query_books = list(
            db_handler.db["Books"].find(q)
        )

        # Lọc theo chữ cái đầu tiên
        if selected_letter != "Tất cả":
            query_books = [
                b for b in query_books
                if b.get("title", "").strip().upper().startswith(selected_letter)
            ]

        # Lọc theo ô tìm kiếm
        if search_text.strip():
            query_books = [
                b for b in query_books
                if search_text.strip().lower() in b.get("title", "").lower()
            ]

        total_books = len(query_books)

        # Thông báo bộ lọc đang áp dụng
        filter_info = []
        if selected_cat != "Tất cả":
            filter_info.append(f"danh mục **{selected_cat}**")
        if selected_letter != "Tất cả":
            filter_info.append(f"chữ cái **{selected_letter}**")
        if search_text.strip():
            filter_info.append(f"từ khóa **\"{search_text.strip()}\"**")
        if filter_info:
            st.caption(f"🔎 Đang lọc theo: {', '.join(filter_info)} — Tìm thấy **{total_books}** sách")

        if total_books == 0:
            if filter_info:
                st.info(f"Không tìm thấy sách nào phù hợp với bộ lọc hiện tại.")
            else:
                st.info("Không có sản phẩm nào.")
        else:
            # PHÂN TÁCH TRANG CHUẨN (MỖI TRANG ĐÚNG 25 CUỐN)
            ITEMS_PER_PAGE = 25
            total_pages = (total_books + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
            
            # Tạo thanh chọn trang nhỏ gọn
            col_space, col_page = st.columns([3, 1])
            with col_page:
                current_page = st.selectbox(f"Trang (Tổng số: {total_pages})", list(range(1, total_pages + 1)), index=0)
            
            # Cắt danh sách mảng dựa theo số trang đang đứng
            start_idx = (current_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            books_to_show = query_books[start_idx:end_idx]

            # Hiển thị dạng lưới (Grid) 3 cột kèm ảnh
            for i in range(0, len(books_to_show), 3):

                cols_grid = st.columns(3)

                for j in range(3):

                    if i + j < len(books_to_show):

                        b = books_to_show[i + j]

                        with cols_grid[j]:
                            
                            # SUA: Hien thi anh bang duong dan tuyet doi tu helper show_book_image().
                            show_book_image(b, caption=b["title"])

                            # 2. CHUẨN HÓA CARD THÔNG TIN SÁCH (Đã sửa lỗi hiển thị text thô)
                            st.markdown(f"""
                            <div class='book-card'>
                                <div class='book-title'>
                                    {b['title']}
                                </div>
                                <div class='book-category'>
                                    {b['category']}
                                </div>
                                <div class='book-price'>
                                    {b['price']:,} VNĐ
                                </div>
                                <div class='book-stock {"out" if int(b.get("stock", 0)) <= 0 else ""}'>
                                    {"Hết hàng" if int(b.get("stock", 0)) <= 0 else f"Còn {int(b.get('stock', 0))} cuốn"}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # 3. NÚT CHỌN MUA
                            if st.session_state.user and st.session_state.user.get("role") == "admin":
                                st.warning("Admin không thể mua")
                            else:
                                can_buy = can_add_to_cart(b)
                                if st.button(
                                    "🛒 Chọn mua",
                                    key=f"buy_{b['_id']}",
                                    disabled=not can_buy
                                ):
                                    st.session_state.cart.append(b)
                                    st.success("Đã thêm vào giỏ")
                                    st.rerun()
                                if not can_buy:
                                    st.caption("Hết hàng hoặc đã lấy đủ số lượng trong giỏ.")
                            st.markdown("<br>", unsafe_allow_html=True)

# GIỎ HÀNG
elif st.session_state.page == "Giỏ hàng":

    st.subheader("🛒 Giỏ hàng của bạn")

    if not st.session_state.cart:
        st.info("Giỏ hàng đang trống.")
    else:

        df_cart = pd.DataFrame(st.session_state.cart)

        total_pay = df_cart['price'].sum()

        for idx, item in enumerate(st.session_state.cart):

            col_info, col_del = st.columns([9, 1])

            with col_info:
                current_book = db_handler.db["Books"].find_one({"_id": int(item["_id"])}) or item
                current_stock = int(current_book.get("stock", 0))
                st.markdown(f"""
                <div style="
                    background:white;
                    padding:15px;
                    border-radius:10px;
                    border:2px solid #dcdcdc;
                    box-shadow:0 2px 5px rgba(0,0,0,0.1);
                    margin-bottom:10px;
                ">
                <h4 style="color:black; margin-bottom:10px;">{item['title']}</h4>
                <h3 style="color:red;">{item['price']:,} VNĐ</h3>
                <p style="color:{'#dc2626' if current_stock <= 0 else '#374151'}; font-weight:600;">
                    {"Hết hàng" if current_stock <= 0 else f"Tồn kho hiện tại: {current_stock} cuốn"}
                </p>
                </div>
                """, unsafe_allow_html=True)

            with col_del:
                st.write("")
                st.write("")
                if st.button("❌", key=f"del_{idx}"):
                    st.session_state.cart.pop(idx)
                    st.rerun()
        st.markdown(
            f"""
            <h2 style='color:#ff4b4b'>
                Tổng cộng: {total_pay:,} VNĐ
            </h2>
            """,
            unsafe_allow_html=True
        )

        # APRIORI
        try:

            rules = mining.run_apriori_analysis(0.05, 0.3)

            if not rules.empty:

                for _, row in rules.iterrows():

                    if set(row['antecedents']).issubset(
                        set(df_cart['title'].tolist())
                    ):

                        for sach_k in row['consequents']:

                            if sach_k not in df_cart['title'].tolist():

                                b_k = db_handler.db["Books"].find_one(
                                    {"title": sach_k}
                                )

                                if b_k:

                                    st.info(
                                        f"💡 Khách thường mua thêm: {sach_k}"
                                    )

                                    if st.button(
                                        "➕ Thêm sản phẩm",
                                        key=f"ak_{b_k['_id']}",
                                        disabled=not can_add_to_cart(b_k)
                                    ):
                                        st.session_state.cart.append(b_k)
                                        st.rerun()
                                    if not can_add_to_cart(b_k):
                                        st.caption("Sản phẩm gợi ý đã hết hàng hoặc đã đủ số lượng trong giỏ.")

        except Exception as ex:
            # SUA: Hien loi Apriori thay vi bo qua im lang.
            st.warning(f"Khong the tao goi y Apriori: {ex}")

        if st.button("✅ XÁC NHẬN THANH TOÁN"):

            if st.session_state.user is None:
                st.error("Vui lòng đăng nhập.")
            else:

                try:
                    db_handler.save_order(
                        st.session_state.user,
                        st.session_state.cart,
                        total_pay
                    )

                    st.session_state.cart = []

                    st.success("🎉 Thanh toán thành công!")

                    chyen_trang("Trang chủ")
                except ValueError as ex:
                    st.error(str(ex))

# TAI KHOAN KHACH HANG
elif st.session_state.page == "Tài khoản":

    if st.session_state.user is None:
        st.error("Vui lòng đăng nhập.")
    else:
        user = st.session_state.user
        st.subheader("Thông tin tài khoản")

        info_col, pass_col = st.columns([1, 1])

        with info_col:
            # THEM: Hien thong tin tai khoan khach, khong hien mat khau.
            st.markdown(
                f"""
                <div class="panel-card">
                    <h3>{user.get('name', '')}</h3>
                    <p><b>Tên đăng nhập:</b> {user.get('username', '')}</p>
                    <p><b>Giới tính:</b> {user.get('gender', '')}</p>
                    <p><b>Tuổi:</b> {user.get('age', '')}</p>
                    <p><b>Thu nhập:</b> {int(user.get('income', 0)):,} VNĐ</p>
                    <p><b>Vai trò:</b> {user.get('role', '')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with pass_col:
            st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
            st.markdown("### Đổi mật khẩu")

            with st.form("change_password_form"):
                old_password = st.text_input("Mật khẩu hiện tại", type="password")
                new_password = st.text_input("Mật khẩu mới", type="password")
                confirm_password = st.text_input("Nhập lại mật khẩu mới", type="password")

                if st.form_submit_button("Cập nhật mật khẩu"):
                    if not old_password or not new_password:
                        st.error("Vui lòng nhập đầy đủ mật khẩu.")
                    elif new_password != confirm_password:
                        st.error("Mật khẩu mới không khớp.")
                    elif len(new_password) < 4:
                        st.error("Mật khẩu mới cần ít nhất 4 ký tự.")
                    else:
                        changed = db_handler.change_user_password(
                            user["username"],
                            old_password,
                            new_password
                        )
                        if changed:
                            st.success("Đã đổi mật khẩu.")
                        else:
                            st.error("Mật khẩu hiện tại không đúng.")

            st.markdown("</div>", unsafe_allow_html=True)

# ADMIN
elif st.session_state.page == "Admin":

    if st.session_state.user is None or st.session_state.user.get("role") != "admin":
        st.error("Từ chối truy cập.")
    else:

        st.title("PHÂN HỆ QUẢN TRỊ")

        tab1, tab2 = st.tabs([
            "Quản lý sách",
            "Quản lý hóa đơn"
        ])

        # CRUD
        with tab1:

            st.subheader("Danh sách sách")

            books = list(db_handler.db["Books"].find({}).sort("_id", 1))
            # SUA: Lay the loai dong tu DB, khong hard-code nua.
            categories = db_handler.get_categories()

            if books:
                st.dataframe(
                    pd.DataFrame(books)[['_id', 'title', 'category', 'price', 'stock', 'image']],
                    use_container_width=True
                )
            else:
                st.info("Chưa có sách trong hệ thống.")

            add_col, edit_col = st.columns([1, 1])

            with add_col:
                st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
                st.markdown("### Thêm sách")

                with st.form("add_book"):
                    last_book = db_handler.db["Books"].find_one(sort=[("_id", -1)])

                    # SUA: Sinh ID moi trong form them sach va giu anh mac dinh hop le.
                    n_id = 1 if last_book is None else last_book["_id"] + 1
                    st.text_input("ID sách", value=str(n_id), disabled=True)
                    n_title = st.text_input("Tên sách")
                    n_cat = st.selectbox("Thể loại có sẵn", categories, key="add_book_category")
                    # THEM: Neu nhap the loai moi thi tao category moi; neu bo trong thi dung combobox.
                    n_new_cat = st.text_input("Thể loại mới nếu chưa có", key="add_book_new_category")
                    n_price = st.number_input("Giá", min_value=1000, step=1000)
                    # THEM: So luong ton kho khi them sach.
                    n_stock = st.number_input("Số lượng tồn kho", min_value=0, value=10, step=1)
                    n_image = st.text_input("Tên file ảnh", value="hinh1.jpg")
                    # THEM: Cho phep upload anh khi them sach.
                    n_image_upload = st.file_uploader(
                        "Tải ảnh bìa",
                        type=["jpg", "jpeg", "png", "webp"],
                        key="add_book_image_upload"
                    )

                    if st.form_submit_button("Thêm sách"):
                        if not n_title.strip():
                            st.error("Vui lòng nhập tên sách.")
                        else:
                            final_category = db_handler.ensure_category(n_new_cat) or n_cat
                            uploaded_image_name = save_uploaded_book_image(n_image_upload, n_title, n_id)
                            db_handler.db["Books"].insert_one({
                                "_id": n_id,
                                "title": n_title.strip(),
                                "category": final_category,
                                "price": int(n_price),
                                "stock": int(n_stock),
                                # SUA: Uu tien anh upload, neu khong co thi dung ten file nhap tay.
                                "image": uploaded_image_name or n_image.strip() or "hinh1.jpg"
                            })

                            st.success("Đã thêm sách")
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            with edit_col:
                st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
                st.markdown("### Sửa / xóa sách")

                if books:
                    book_options = {
                        f"{book['_id']} - {book['title']}": book
                        for book in books
                    }
                    selected_label = st.selectbox("Chọn sách", list(book_options.keys()))
                    selected_book = book_options[selected_label]

                    with st.form("edit_book"):
                        # THEM: Form sua sach cho admin.
                        e_title = st.text_input("Tên sách", value=selected_book["title"])
                        e_cat = st.selectbox(
                            "Thể loại có sẵn",
                            categories,
                            index=categories.index(selected_book["category"]) if selected_book["category"] in categories else 0,
                            key="edit_book_category"
                        )
                        # THEM: Neu nhap the loai moi khi sua thi sach duoc chuyen sang category moi.
                        e_new_cat = st.text_input("Thể loại mới nếu chưa có", key=f"edit_book_new_category_{selected_book['_id']}")
                        e_price = st.number_input(
                            "Giá",
                            min_value=1000,
                            step=1000,
                            value=int(selected_book["price"])
                        )
                        # THEM: Sua so luong ton kho cua sach.
                        e_stock = st.number_input(
                            "Số lượng tồn kho",
                            min_value=0,
                            step=1,
                            value=int(selected_book.get("stock", 0))
                        )
                        e_image = st.text_input("Tên file ảnh", value=selected_book.get("image", "hinh1.jpg"))
                        # THEM: Cho phep upload anh moi khi sua sach.
                        e_image_upload = st.file_uploader(
                            "Tải ảnh bìa mới",
                            type=["jpg", "jpeg", "png", "webp"],
                            key=f"edit_book_image_upload_{selected_book['_id']}"
                        )

                        if st.form_submit_button("Lưu thay đổi"):
                            if not e_title.strip():
                                st.error("Vui lòng nhập tên sách.")
                            else:
                                final_category = db_handler.ensure_category(e_new_cat) or e_cat
                                uploaded_image_name = save_uploaded_book_image(
                                    e_image_upload,
                                    e_title,
                                    selected_book["_id"]
                                )
                                db_handler.update_book(
                                    selected_book["_id"],
                                    e_title.strip(),
                                    final_category,
                                    e_price,
                                    # SUA: Uu tien anh upload, neu khong co thi giu/nhap ten file.
                                    uploaded_image_name or e_image.strip(),
                                    e_stock
                                )
                                st.success("Đã cập nhật sách")
                                st.rerun()

                    # THEM: Xoa sach dat ngoai form sua de thao tac ro rang hon.
                    if st.button("Xóa sách đã chọn", key=f"delete_book_{selected_book['_id']}"):
                        # SUA: Goi ham delete_book neu module da reload; fallback xoa truc tiep de tranh AttributeError tren Streamlit process cu.
                        if hasattr(db_handler, "delete_book"):
                            db_handler.delete_book(selected_book["_id"])
                        else:
                            db_handler.db["Books"].delete_one({"_id": int(selected_book["_id"])})
                        st.success("Đã xóa sách")
                        st.rerun()
                else:
                    st.info("Cần có sách trước khi sửa hoặc xóa.")
                st.markdown("</div>", unsafe_allow_html=True)

        # HÓA ĐƠN
        with tab2:

            st.subheader("Toàn bộ hóa đơn")

            all_orders = db_handler.get_all_orders_for_admin()

            if not all_orders:
                st.info("Chưa có dữ liệu.")
            else:
                parsed_order_dates = [
                    parse_order_datetime(order.get("date"))
                    for order in all_orders
                ]
                valid_order_dates = [dt for dt in parsed_order_dates if dt]
                min_order_date = min(valid_order_dates).date() if valid_order_dates else datetime.now().date()
                max_order_date = max(valid_order_dates).date() if valid_order_dates else datetime.now().date()

                # THEM: Bo loc hoa don admin theo ngay/gio, the loai, trang thai va tu khoa.
                st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
                f1, f2, f3, f4 = st.columns(4)
                with f1:
                    filter_from_date = st.date_input("Từ ngày", value=min_order_date, key="order_filter_from_date")
                    filter_from_time = st.time_input("Từ giờ", value=time(0, 0), key="order_filter_from_time")
                with f2:
                    filter_to_date = st.date_input("Đến ngày", value=max_order_date, key="order_filter_to_date")
                    filter_to_time = st.time_input("Đến giờ", value=time(23, 59), key="order_filter_to_time")
                with f3:
                    filter_category = st.selectbox(
                        "Thể loại",
                        ["Tất cả"] + db_handler.get_categories(),
                        key="order_filter_category"
                    )
                    filter_status = st.selectbox(
                        "Trạng thái",
                        ["Tất cả", "Đang hiển thị", "Đã xóa hiển thị"],
                        key="order_filter_status"
                    )
                with f4:
                    filter_keyword = st.text_input(
                        "Tìm hóa đơn / khách / sách",
                        key="order_filter_keyword"
                    ).strip().lower()

                from_dt = datetime.combine(filter_from_date, filter_from_time)
                to_dt = datetime.combine(filter_to_date, filter_to_time)

                filtered_orders = []
                for order in all_orders:
                    order_dt = parse_order_datetime(order.get("date"))
                    if order_dt and (order_dt < from_dt or order_dt > to_dt):
                        continue

                    order_status = "Đã xóa hiển thị" if order.get("deleted_by_user") else "Đang hiển thị"
                    if filter_status != "Tất cả" and order_status != filter_status:
                        continue

                    if filter_category != "Tất cả" and order.get("main_category") != filter_category:
                        continue

                    haystack = " ".join([
                        str(order.get("order_id", "")),
                        str(order.get("customer_name", "")),
                        str(order.get("customer_username", "")),
                        str(order.get("main_category", "")),
                        " ".join(item.get("title", "") for item in order.get("items", []))
                    ]).lower()
                    if filter_keyword and filter_keyword not in haystack:
                        continue

                    filtered_orders.append(order)

                st.caption(f"Hiển thị {len(filtered_orders)} / {len(all_orders)} hóa đơn")
                st.markdown("</div>", unsafe_allow_html=True)

                if not filtered_orders:
                    st.info("Không có hóa đơn phù hợp với bộ lọc.")

                for o_doc in filtered_orders:

                    trang_thai = (
                        "Đã xóa hiển thị"
                        if o_doc.get("deleted_by_user")
                        else "Đang hiển thị"
                    )
                    status_color = "#dc2626" if o_doc.get("deleted_by_user") else "#0f766e"

                    with st.expander(
                        f"{o_doc['order_id']} | {o_doc['customer_name']} | {trang_thai}"
                    ):
                        # SUA: Doi chi tiet hoa don thanh card sang mau, de doc hon tren nen moi.
                        items_html = "".join(
                            f"<li>{item['title']} x {item['quantity']} - {item['price']:,} đ</li>"
                            for item in o_doc["items"]
                        )
                        first_item = o_doc["items"][0] if o_doc.get("items") else {}
                        # THEM: Lay anh cua cuon sach dau tien trong hoa don de hien ben phai card.
                        order_book = db_handler.db["Books"].find_one(
                            {"_id": first_item.get("book_id")}
                        ) or db_handler.db["Books"].find_one(
                            {"title": first_item.get("title")}
                        ) or {"title": first_item.get("title", ""), "image": "hinh1.jpg"}
                        order_image_tag = get_book_image_tag(order_book)
                        st.markdown(
                            f"""
                            <div class="order-card">
                                <div>
                                    <h4>{o_doc['order_id']} - {o_doc['customer_name']}</h4>
                                    <p><b>Trạng thái:</b> <span style="color:{status_color}; font-weight:700">{trang_thai}</span></p>
                                    <p><b>Ngày:</b> {o_doc['date']}</p>
                                    <p><b>Tuổi:</b> {o_doc['customer_age']} | <b>Thu nhập:</b> {o_doc['customer_income']:,} VNĐ</p>
                                    <p><b>Sản phẩm:</b></p>
                                    <ul>{items_html}</ul>
                                    <div class="order-total">Tổng: {o_doc['total_amount']:,} VNĐ</div>
                                </div>
                                <div class="order-cover">{order_image_tag}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

# ĐĂNG KÝ
elif st.session_state.page == "Đăng ký":

    st.subheader("Đăng ký tài khoản")

    with st.form("reg_f"):

        u = st.text_input("Tên đăng nhập")
        n = st.text_input("Họ và tên")

        g = st.selectbox(
            "Giới tính",
            ["Nam", "Nữ"]
        )

        a = st.number_input(
            "Tuổi",
            min_value=12,
            value=20
        )

        inc = st.number_input(
            "Thu nhập",
            min_value=1000000,
            value=5000000
        )

        p = st.text_input(
            "Mật khẩu",
            type="password"
        )

        if st.form_submit_button("Đăng ký"):

            db_handler.db["Users"].insert_one({
                "username": u,
                "name": n,
                "gender": g,
                "age": a,
                "income": inc,
                "password": p,
                "role": "customer"
            })

            st.success("Đăng ký thành công")
            chyen_trang("Đăng nhập")

# ĐĂNG NHẬP
elif st.session_state.page == "Đăng nhập":

    st.subheader("Đăng nhập")

    with st.form("log_f"):

        u = st.text_input("Tên đăng nhập")

        p = st.text_input(
            "Mật khẩu",
            type="password"
        )

        if st.form_submit_button("Đăng nhập"):

            user = db_handler.db["Users"].find_one({
                "username": u,
                "password": p
            })

            if user:

                st.session_state.user = user

                chyen_trang(
                    "Admin"
                    if user.get("role") == "admin"
                    else "Trang chủ"
                )

            else:
                st.error("Sai tài khoản hoặc mật khẩu")
