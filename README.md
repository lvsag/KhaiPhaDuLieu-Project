# KhaiPhaDuLieu-Project - VouBook

VouBook là ứng dụng quản lý và bán sách được xây dựng bằng **Streamlit**, **MongoDB** và các thuật toán khai phá dữ liệu. Project mô phỏng một nhà sách trực tuyến có chức năng bán hàng, quản trị sách, quản lý hóa đơn và gợi ý sản phẩm dựa trên dữ liệu mua hàng.

## Chức năng chính

- Hiển thị danh sách sách theo dạng lưới, có ảnh bìa, giá bán, thể loại và tồn kho.
- Lọc sách theo thể loại, chữ cái đầu tiên và từ khóa tìm kiếm.
- Đăng ký, đăng nhập, đăng xuất tài khoản khách hàng.
- Thêm sách vào giỏ hàng, xóa khỏi giỏ hàng và thanh toán đơn hàng.
- Lưu lịch sử hóa đơn theo từng khách hàng.
- Cho phép khách hàng ẩn hóa đơn khỏi lịch sử cá nhân nhưng admin vẫn xem được dữ liệu.
- Quản trị sách: thêm, sửa, xóa sách, cập nhật giá, thể loại, ảnh bìa và số lượng tồn kho.
- Quản trị hóa đơn: xem toàn bộ hóa đơn, lọc theo ngày giờ, thể loại, trạng thái và từ khóa.
- Đổi mật khẩu tài khoản.

## Chức năng khai phá dữ liệu

Project sử dụng dữ liệu hóa đơn trong MongoDB để thực hiện các kỹ thuật khai phá dữ liệu:

- **KNN**: dự đoán thể loại sách phù hợp với khách hàng dựa trên tuổi và thu nhập, sau đó gợi ý sách cùng thể loại.
- **Apriori / Association Rules**: tìm luật mua kèm trong giỏ hàng để gợi ý các sách thường được mua chung.
- **Chi-Square**: phân tích mối liên hệ giữa giới tính khách hàng và thể loại sách được mua chính.

Các hàm xử lý nằm trong file `src/mining_untils.py`.

## Công nghệ sử dụng

- Python
- Streamlit
- MongoDB
- PyMongo
- Pandas
- SciPy
- MLxtend
- Scikit-learn

## Cấu trúc thư mục

```text
.
|-- data/
|   `-- tao_data.py              # Script tạo dữ liệu mẫu cho MongoDB
|-- src/
|   |-- app.py                   # Giao diện và luồng chính của ứng dụng Streamlit
|   |-- database.py              # Kết nối MongoDB và các hàm thao tác dữ liệu
|   |-- mining_untils.py         # Các thuật toán khai phá dữ liệu
|   `-- hinh_anh_sach/           # Ảnh bìa sách
|-- requirements.txt             # Danh sách thư viện cần cài
`-- README.md
```

## Yêu cầu trước khi chạy

- Python 3.9 trở lên.
- MongoDB đang chạy ở địa chỉ mặc định:

```text
mongodb://127.0.0.1:27017/
```

Database được sử dụng trong project:

```text
QuanLyNhaSach
```

Các collection chính:

- `Books`
- `Users`
- `Orders`
- `Categories`

## Cài đặt

1. Tạo và kích hoạt môi trường ảo:

```bash
python -m venv .venv
```

Trên Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

2. Cài các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

## Tạo dữ liệu mẫu

Trước khi chạy ứng dụng, hãy đảm bảo MongoDB đã được bật. Sau đó chạy:

```bash
python data/tao_data.py
```

Script này sẽ:

- Xóa dữ liệu cũ trong `Books` và `Orders`.
- Tạo danh sách sách mẫu kèm ảnh, giá, thể loại và tồn kho.
- Tạo 100 hóa đơn mẫu để phục vụ KNN, Apriori và Chi-Square.

Lưu ý: tài khoản admin mặc định được tạo tự động khi ứng dụng import `src/database.py`, nếu trong collection `Users` chưa có admin.

## Chạy ứng dụng

Chạy Streamlit từ thư mục gốc project:

```bash
streamlit run src/app.py
```

Sau đó mở địa chỉ Streamlit hiển thị trên terminal, thường là:

```text
http://localhost:8501
```

## Tài khoản admin mặc định

```text
Username: admin
Password: admin
```

Admin có thể truy cập phân hệ quản trị để quản lý sách và hóa đơn.

## Gợi ý quy trình sử dụng

1. Bật MongoDB.
2. Cài thư viện bằng `pip install -r requirements.txt`.
3. Chạy `python data/tao_data.py` để tạo dữ liệu mẫu.
4. Chạy `streamlit run src/app.py`.
5. Đăng nhập bằng tài khoản admin hoặc đăng ký tài khoản khách hàng mới.

## Ghi chú

- Ảnh sách được lưu trong `src/hinh_anh_sach`.
- Khi thêm hoặc sửa sách, có thể nhập tên file ảnh có sẵn hoặc tải ảnh bìa mới.
- Nếu sách hết tồn kho, nút thêm vào giỏ hàng sẽ bị vô hiệu hóa.
- Mật khẩu trong project demo đang được lưu dạng plain text, chỉ phù hợp cho mục đích học tập và mô phỏng.
