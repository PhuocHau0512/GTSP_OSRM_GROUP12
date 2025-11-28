# presentation/app_presentation.py
from flask import Flask, render_template  # Import Flask và hàm render_template

# Khởi tạo Flask App cho Lớp Trình diễn (Presentation Layer)
# Đây là server chỉ có MỘT nhiệm vụ: phục vụ file HTML, CSS, JS cho trình duyệt.
app = Flask(__name__)


@app.route('/')  # Định nghĩa route (đường dẫn) gốc
def index():
    """
    Phục vụ trang web chính (index.html).
    Khi người dùng truy cập vào http://localhost:8080/,
    hàm này sẽ được gọi.
    """
    # render_template sẽ tự động tìm file 'index.html'
    # trong thư mục 'templates' (theo quy ước của Flask)
    return render_template('index.html')


if __name__ == '__main__':
    # Điểm khởi chạy khi ta chạy file python này
    # (ví dụ: python app_presentation.py)
    
    # Chạy Presentation server trên cổng 8080
    print("--- Lớp Trình diễn (UI) đang chạy tại: http://localhost:8080 ---")
    app.run(debug=True, port=8080)