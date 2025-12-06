# XÂY DỰNG CHƯƠNG TRÌNH TÌM LỘ TRÌNH TỐI ƯU ĐỂ XE ĐƯA KHÁCH THAM QUAN ĐẾN CÁC DANH THẮNG LỊCH SỬ Ở THÀNH PHỐ HCM BẰNG THUẬT TOÁN GTS KẾT HỢP OSRM

Ứng dụng web giải quyết **Bài toán Người Du lịch Tổng quát (Generalized Traveling Salesman Problem -- GTSP)** bằng dữ liệu bản đồ thực tế (OSRM) và thuật toán **GRASP**.

Mục tiêu: tìm **lộ trình tối ưu** từ điểm A đến điểm B, bắt buộc đi qua các **cụm địa điểm**, nhưng chỉ cần ghé **một địa điểm đại diện** trong mỗi cụm.

--------------------------------------------------------------------------------------------------------------------

## Tính năng nổi bật

-   **Giải thuật GTSP**: Sử dụng **GRASP (Greedy Randomized Adaptive Search Procedure)** để tìm nghiệm tốt trong thời gian hợp lý.
-   **Tối ưu hóa kép**: Người dùng tùy chọn tối ưu theo **quãng đường (km)** hoặc **thời gian (phút)**.
-   **Kiến trúc 3 lớp chuẩn**: Presentation -- Business Logic -- Data Layer.
-   **Điểm linh hoạt**: Cho phép người dùng nhập điểm bắt đầu/kết thúc bằng tên địa chỉ (Geocoding với Nominatim).
-   **Dữ liệu thật từ OSRM**: Tính toán ma trận chi phí & đường đi dựa trên bản đồ OSM.
-   **Giao diện trực quan**: Leaflet.js hiển thị bản đồ, cụm điểm và tuyến đường.

--------------------------------------------------------------------------------------------------------------------

## Kiến trúc Hệ thống (3-Layer Architecture)

Presentation (UI) <--HTTP--> Business Logic (API) <--HTTP--> Data Layer (OSRM + DB)

## 1. Presentation Layer
- **Công nghệ:** Flask, HTML, CSS (Bootstrap), JavaScript, Leaflet.js  
- **Chạy tại:** `http://localhost:8080`
- **Chức năng:**
  - Hiển thị bản đồ & giao diện người dùng.
  - Nhận input: điểm bắt đầu/kết thúc, cụm được chọn, tiêu chí tối ưu.
  - Gửi yêu cầu giải GTSP đến BLL.
  - Nhận kết quả và render lộ trình trên bản đồ.

## 2. Business Logic Layer (BLL)
- **Công nghệ:** Flask API, Flask-CORS, Python  
- **Chạy tại:** `http://localhost:5001`
- **Chức năng:**
  - Cung cấp API: `/get_clusters`, `/solve_gtsp`.
  - Thực hiện Geocoding.
  - Lấy danh sách điểm của các cụm từ `database.py`.
  - Gọi OSRM để lấy **ma trận chi phí**.
  - Chạy **GTSPGraspSolver** để tìm lộ trình tối ưu.
  - Gọi lại OSRM để lấy **geometry** của tuyến đường.

## 3. Data Layer
- Bao gồm:
  1. **OSRM Server** (dữ liệu bản đồ) – chạy bằng Docker hoặc OSRM demo server.
  2. **Cơ sở dữ liệu ứng dụng** (`database.py`) – lưu danh sách điểm & các cụm GTSP.

--------------------------------------------------------------------------------------------------------------------

# Công nghệ sử dụng
--------------------------------------------------------------
|   Thành phần  |                Công nghệ                   |
|---------------|--------------------------------------------|
| Backend (BLL) | Python 3, Flask, Flask-CORS                |
| Frontend (UI) | HTML5, Bootstrap 5, JavaScript, Leaflet.js |
| Map & Routing | OSRM, Nominatim                            |
| Python libs   | requests, geopy, polyline                  |
--------------------------------------------------------------

--------------------------------------------------------------------------------------------------------------------

# Cấu trúc thư mục

<<<<<<< HEAD
/gts_osrm
│
├── presentation/
│ ├── static/
│ │ └── app.js
│ ├── templates/
│ │ └── index.html
│ └── app_presentation.py
│
├── logic/ 
│ ├── app_logic.py
│ ├── database.py
│ ├── gtsp_solver.py
│ └── osrm_client.py
│
├── README.md
└── requirements.txt

=======
```
/gts_osrm_group12
├── presentation/
│   ├── static/
│   │   └── app.js
│   ├── templates/
│   │   └── index.html
│   └── app_presentation.py
├── logic/
│   ├── app_logic.py
│   ├── database.py
│   ├── gtsp_solver.py
│   └── osrm_client.py
├── README.md
└── requirements.txt
```
>>>>>>> 5b64062fdf1062d87e0a6be251679e475c0025bb
--------------------------------------------------------------------------------------------------------------------

## Cài đặt & Chạy hệ thống

## 1. Yêu cầu
- Python 3.8+
- Docker Desktop (nếu chạy OSRM nội bộ)
- File dữ liệu `.osrm` từ Geofabrik

## 2. Cài đặt thư viện
1. **Cài đặt môi trường ảo**

`python -m venv .venv`

Activate : `.\.venv\Scripts\activate` 

hoặc `.\.venv\Scripts\Activate.ps1`

Thoát môi trường ảo: `deactivate`
2. **Cài đặt gói**

`pip install -r requirements.txt`

## 3. Cấu hình dữ liệu

Mở file: `logic/database.py`

Và điều chỉnh:

-   Danh sách địa điểm: ALL_LANDMARKS

-   Danh sách cụm: CLUSTERS

--------------------------------------------------------------------------------------------------------------------

## Khởi chạy hệ thống (3 terminal)

1. **Terminal 1 – Chạy OSRM Server**

`Cách A – Docker (Khuyên dùng)`

docker run -t -i -p 5000:5000 \
  -v "/duong/dan/vietnam-latest.osrm:/data" \
  osrm/osrm-backend osrm-routed --algorithm mld --port 5000 /data

⚠️ Sửa đường dẫn file .osrm.
Trong logic/osrm_client.py chỉnh:

self.base_url = "http://localhost:5000"

`Cách B – Dùng OSRM demo`

Không cần chạy Docker → Dùng sẵn: http://router.project-osrm.org

2. **Terminal 2 – Chạy Business Logic Layer**
```bash
python logic/app_logic.py
```
Bạn sẽ thấy: --- Lớp Logic nghiệp vụ (BLL) chạy tại http://localhost:5001 ---

3. **Terminal 3 – Chạy Presentation Layer**
```bash
python presentation/app_presentation.py
```

Kết quả: --- Lớp Trình diễn (UI) chạy tại http://localhost:8080 ---

--------------------------------------------------------------------------------------------------------------------

## Truy cập ứng dụng

Mở trình duyệt và truy cập: http://localhost:8080

--------------------------------------------------------------------------------------------------------------------

## Contact

**Email**: ph124work@gmail.com hoặc lephuochau5122004@gmail.com


<<<<<<< HEAD
netstat -ano | findstr :8080

taskkill /PID ... /F


=======
>>>>>>> 5b64062fdf1062d87e0a6be251679e475c0025bb
