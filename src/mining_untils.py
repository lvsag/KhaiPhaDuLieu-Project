from pymongo import MongoClient
import pandas as pd
from scipy.stats import chi2_contingency
from mlxtend.frequent_patterns import apriori, association_rules
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

# Hàm kết nối nhanh đến MongoDB và lấy dữ liệu Orders về dạng DataFrame
def get_orders_dataframe():
    client = MongoClient("mongodb://127.0.0.1:27017/")
    db = client["QuanLyNhaSach"]
    orders = list(db["Orders"].find())
    return pd.DataFrame(orders)

def run_chi_square_analysis():
    df = get_orders_dataframe()
    if df.empty:
        return pd.DataFrame(), 0, 1

    # Lập bảng tần suất chéo giữa Giới tính và Thể loại mua chính
    contingency_table = pd.crosstab(df['customer_gender'], df['main_category'])
    
    # Tính toán Chi-Square
    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
    
    return contingency_table, chi2, p_value

def run_apriori_analysis(min_support=0.1, min_confidence=0.5):
    df = get_orders_dataframe()
    if df.empty or 'items' not in df:
        return pd.DataFrame()
    
    # Biến đổi dữ liệu mảng 'items' trong mỗi hóa đơn thành dạng ma trận One-Hot (0 và 1)
    # Để biết hóa đơn nào có mua những sách nào
    all_orders_items = []
    for items_list in df['items']:
        order_dict = {item['title']: 1 for item in items_list}
        all_orders_items.append(order_dict)
        
    # SUA: mlxtend Apriori khuyen nghi dung bool thay vi int de tranh warning va chay dung kieu du lieu.
    df_items = pd.DataFrame(all_orders_items).fillna(False).astype(bool)
    
    # 1. Tìm tập phổ biến bằng Apriori
    frequent_itemsets = apriori(df_items, min_support=min_support, use_colnames=True)
    
    # 2. Tạo luật kết hợp (Association Rules)
    if not frequent_itemsets.empty:
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
        # Chỉ lấy các cột quan trọng để hiển thị cho dễ hiểu
        rules = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']]
        return rules
    return pd.DataFrame()

def predict_customer_group_knn(age, income):
    df = get_orders_dataframe()
    if df.empty:
        return "Chưa đủ dữ liệu"
    
    # Chuẩn bị dữ liệu huấn luyện: Dựa vào Tuổi và Thu nhập để học Thể loại sách họ hay mua nhất
    X = df[['customer_age', 'customer_income']]
    y = df['main_category']
    
    # Chuẩn hóa dữ liệu vì Khoảng cách của Thu nhập lớn hơn Tuổi rất nhiều
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Khởi tạo mô hình KNN với K=5
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(X_scaled, y)
    
    # Chuẩn hóa dữ liệu của khách hàng mới cần dự đoán
    # SUA: Truyen DataFrame co ten cot de tranh warning "X does not have valid feature names".
    new_customer = pd.DataFrame(
        [[age, income]],
        columns=['customer_age', 'customer_income']
    )
    new_customer_scaled = scaler.transform(new_customer)
    
    # Dự đoán kết quả
    prediction = knn.predict(new_customer_scaled)
    return prediction[0]
