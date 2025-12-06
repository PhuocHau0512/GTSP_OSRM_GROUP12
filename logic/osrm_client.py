# logic/osrm_client.py
import requests                      # Thư viện để thực hiện các yêu cầu HTTP (gọi API)
from geopy.distance import geodesic  # Dùng để tính khoảng cách "đường chim bay" (cho hàm fallback)
import polyline  
import time  

class OSRMClient:
    """
    Lớp Client (máy khách) để đóng gói và quản lý tất cả các
    lời gọi API đến dịch vụ OSRM (Open Source Routing Machine).
    """

    def __init__(self, base_url="http://router.project-osrm.org"):
        # Sử dụng server OSRM demo công cộng
        # (Nên thay bằng server OSRM nội bộ nếu chạy production, ví dụ: "http://localhost:5000")
        self.base_url = base_url
        # Khởi tạo 1 Session để tái sử dụng kết nối TCP (tăng hiệu suất khi gọi API nhiều lần)
        self.session = requests.Session()
        print(f"OSRM Client khởi tạo, kết nối tới: {self.base_url}")

    def get_route_info(self, coord1, coord2, profile='driving'):
        """
        Lấy thông tin tuyến đường chi tiết giữa 2 điểm (API 'route').
        Hàm này trả về geometry (để vẽ) và steps (hướng dẫn rẽ).

        Input: coord1, coord2 là (latitude, longitude)
        """
        try:
            # OSRM API yêu cầu tọa độ theo định dạng (longitude, latitude)
            # Chúng ta cần chuyển đổi từ (lat, lon) sang (lon, lat)
            lon1, lat1 = coord1[1], coord1[0]
            lon2, lat2 = coord2[1], coord2[0]

            # Xây dựng URL cho OSRM 'route' service
            url = f"{self.base_url}/route/v1/{profile}/{lon1},{lat1};{lon2},{lat2}"
            params = {
                'overview': 'full',  # Lấy geometry chi tiết nhất
                'geometries': 'geojson',  # Yêu cầu trả về định dạng GeoJSON (dễ vẽ trên Leaflet/Mapbox)
                'steps': 'true'  # Yêu cầu trả về các bước chỉ đường chi tiết
            }

            # Gửi yêu cầu GET với timeout 10 giây
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()  # Ném lỗi nếu status code là 4xx hoặc 5xx
            data = response.json()

            if data['code'] == 'Ok' and len(data['routes']) > 0:
                route = data['routes'][0]  # Lấy tuyến đường tốt nhất
                
                # --- Trích xuất thông tin steps (hướng dẫn rẽ) ---
                steps = []
                if route.get('legs'):  # Một tuyến đường (route) có thể có nhiều chặng (legs)
                    for leg in route['legs']:
                        if leg.get('steps'):  # Mỗi chặng có nhiều bước (steps)
                            for step in leg['steps']:
                                # Lấy thông tin cần thiết cho UI
                                step_info = {
                                    "name": step.get('name', ''),  # Tên đường (ví dụ: "Đường Nguyễn Huệ")
                                    "maneuver_type": step['maneuver']['type'],  # Kiểu (depart, turn, arrive)
                                    "maneuver_modifier": step['maneuver'].get('modifier', ''),  # Hướng (left, right, straight)
                                    "distance": step['distance'],  # mét
                                    "duration": step['duration']  # giây
                                }
                                steps.append(step_info)

                # Trả về một dict chứa thông tin đã xử lý
                return {
                    'distance': route['distance'] / 1000,  # Chuyển đổi mét -> km
                    'duration': route['duration'] / 60,    # Chuyển đổi giây -> phút
                    'geometry': route['geometry'],         # Dữ liệu GeoJSON để vẽ
                    'steps': steps                         # Mảng các bước chỉ đường
                }
            else:
                # Trường hợp OSRM trả về code không 'Ok' (ví dụ: 'NoRoute')
                print(f"OSRM Route API trả về code: {data.get('code')}")
                return None
        except requests.exceptions.RequestException as e:
            # Xử lý lỗi mạng (timeout, không kết nối được, ...)
            print(f"OSRM Route API Error: {e}")
            return None

    def get_distance_matrix(self, coordinates, profile='driving'):
        """
        Lấy ma trận khoảng cách/thời gian cho một danh sách các điểm (API 'table').
        Đây là hàm quan trọng nhất để cung cấp dữ liệu cho Solver.

        Input: coordinates là danh sách các (lat, lon)
        """
        try:
            # OSRM yêu cầu (lon,lat)
            # Chuyển đổi danh sách tọa độ thành chuỗi, ví dụ: "lon1,lat1;lon2,lat2;..."
            coords_str = ';'.join([f"{lon},{lat}" for lat, lon in coordinates])

            url = f"{self.base_url}/table/v1/{profile}/{coords_str}"
            params = {
                'annotations': 'distance,duration'  # Yêu cầu trả về cả 2 ma trận
            }

            # Gửi yêu cầu (timeout 30s vì đây là request có thể rất lớn)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data['code'] == 'Ok':
                # Xử lý ma trận kết quả:
                # 1. Chuyển đổi (mét -> km) và (giây -> phút)
                # 2. Nếu OSRM trả về 'null' (không có đường đi), thay bằng float('inf') (vô cùng)
                
                distances_km = [
                    [(dist / 1000.0) if dist is not None else float('inf') for dist in row]
                    for row in data['distances']
                ]
                durations_min = [
                    [(dur / 60.0) if dur is not None else float('inf') for dur in row]
                    for row in data['durations']
                ]

                return {
                    'distances': distances_km,
                    'durations': durations_min
                }
            else:
                # Nếu OSRM báo lỗi (ví dụ: 'InvalidQuery')
                print(f"OSRM Table API trả về code: {data.get('code')}")
                return self._fallback_distance_matrix(coordinates)  # Chuyển sang hàm fallback

        except requests.exceptions.RequestException as e:
            # Lỗi mạng, timeout...
            print(f"OSRM Matrix API Error: {e}. Sử dụng fallback...")
            return self._fallback_distance_matrix(coordinates)  # Chuyển sang hàm fallback

    def _fallback_distance_matrix(self, coordinates):
        """
        Hàm dự phòng (Fallback):
        Tính ma trận chi phí bằng khoảng cách ĐƯỜNG CHIM BAY (geodesic distance).
        Được gọi khi OSRM API 'table' thất bại (do lỗi mạng, lỗi server, hoặc quá tải).

        Lưu ý: Cách này KHÔNG TÍNH ĐƯỜNG ĐI THỰC TẾ, chỉ là ước lượng.
        """
        print("Cảnh báo: Đang sử dụng ma trận fallback (đường chim bay).")
        n = len(coordinates)
        # Khởi tạo 2 ma trận rỗng (chứa giá trị 'inf')
        distances = [[float('inf')] * n for _ in range(n)]
        durations = [[float('inf')] * n for _ in range(n)]

        for i in range(n):
            distances[i][i] = 0  # Khoảng cách/thời gian đến chính nó là 0
            durations[i][i] = 0
            for j in range(i + 1, n):
                # Tính khoảng cách đường chim bay (đơn vị: km)
                dist = geodesic(coordinates[i], coordinates[j]).kilometers
                
                # Ước lượng thời gian: Giả định tốc độ di chuyển trung bình là 30km/h
                # (Đây là một giả định rất thô sơ, chỉ dùng khi bất khả kháng)
                dur = (dist / 30) * 60  # (km / (km/h)) * 60 (phút/h) = phút

                # Gán giá trị cho ma trận (ma trận đối xứng)
                distances[i][j] = distances[j][i] = dist
                durations[i][j] = durations[j][i] = dur

        return {'distances': distances, 'durations': durations}

    def get_coordinates_from_name(self, address):
        """
        Chuyển đổi một chuỗi địa chỉ (tên) thành tọa độ (lat, lon).
        Sử dụng API Geocoding của Nominatim (dựa trên OpenStreetMap).

        Input: "Dinh Độc Lập"
        Output: (10.777963, 106.695676)
        """
        print(f"BLL: Đang Geocoding cho: '{address}'...")
        try:
            # Thêm context (TP.HCM, VN) để tăng độ chính xác cho kết quả
            query = f"{address}, Ho Chi Minh City, Vietnam"

            # API Nominatim yêu cầu 1 User-Agent tùy chỉnh
            # (Không được dùng User-Agent mặc định của 'requests')
            headers = {
                'User-Agent': 'GTS_OSRM_App (ph124work@gmail.com)' # Cần thay bằng email của bạn
            }

            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': query,  # Chuỗi địa chỉ cần tìm
                'format': 'json',  # Định dạng trả về
                'limit': 1,  # Chỉ lấy 1 kết quả chính xác nhất
                'countrycodes': 'vn'  # Ưu tiên kết quả ở Việt Nam
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data:
                # Nếu tìm thấy kết quả
                # Trả về (latitude, longitude)
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                print(f"BLL: Tìm thấy tọa độ: ({lat}, {lon})")
                return (lat, lon)
            else:
                # Nếu API trả về mảng rỗng (không tìm thấy)
                print(f"BLL: Không tìm thấy tọa độ cho '{address}'.")
                return None
        except Exception as e:
            # Xử lý các lỗi khác (mạng, JSON parse...)
            print(f"BLL: Lỗi Geocoding: {e}")
            return None