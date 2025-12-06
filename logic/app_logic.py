# logic/app_logic.py
# Import các thư viện và module cần thiết
from flask import Flask, request, jsonify# Thư viện Flask để tạo server API
from flask_cors import CORS              # Thư viện để xử lý Cross-Origin Resource Sharing (cho phép frontend gọi)
import database                          # Module tự định nghĩa (giả định) để tương tác với cơ sở dữ liệu
from osrm_client import OSRMClient       # Module client để giao tiếp với OSRM API
from gtsp_solver import GTSPGraspSolver  # Module chứa thuật toán giải GTSP (GRASP)
import time                              # Thư viện time để đo lường thời gian thực thi

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# Cấu hình CORS: Cho phép các yêu cầu từ frontend (chạy ở localhost:8080)
# truy cập đến các API của server này (chạy ở localhost:5001).
CORS(app, resources={r"/*": {"origins": "*"}})

# Khởi tạo OSRM client, trỏ đến dịch vụ OSRM công cộng
# OSRM (Open Source Routing Machine) dùng để tính toán ma trận khoảng cách/thời gian và lấy lộ trình chi tiết.
osrm = OSRMClient(base_url="http://router.project-osrm.org")


@app.route('/get_clusters', methods=['GET'])
def get_clusters():
    """
    API Endpoint [GET] /get_clusters
    Mục đích: Lấy thông tin tóm tắt của tất cả các cụm (clusters) từ CSDL.
    Frontend sẽ gọi API này để hiển thị danh sách các cụm cho người dùng chọn.
    """
    try:
        # Gọi hàm từ module database để lấy dữ liệu
        clusters_info = database.get_all_clusters_info()
        # Trả về dữ liệu dưới dạng JSON
        return jsonify(clusters_info)
    except Exception as e:
        # Xử lý nếu có lỗi xảy ra
        print(f"Lỗi /get_clusters: {e}")
        return jsonify({"error": str(e)}), 500  # Trả về lỗi 500 (Internal Server Error)


@app.route('/solve_gtsp', methods=['POST'])
def solve_gtsp_api():
    """
    API Endpoint [POST] /solve_gtsp
    Mục đích: Đây là API cốt lõi, nhận đầu vào (điểm đầu, cuối, các cụm)
    và giải bài toán GTSP (Generalized Travelling Salesperson Problem)
    để tìm lộ trình tối ưu.
    """
    try:
        # 1. Nhận dữ liệu đầu vào (dạng JSON) từ frontend
        data = request.json
        print("\n--- BLL: Nhận được yêu cầu /solve_gtsp ---")

        # Lấy các thông tin từ request
        start_address = data.get('start_address')           # Địa chỉ bắt đầu (dạng text) # type: ignore
        end_address = data.get('end_address')               # Địa chỉ kết thúc (dạng text) # type: ignore
        selected_cluster_ids = data.get('cluster_ids', [])  # Danh sách ID các cụm đã chọn # type: ignore
        optimize_for = data.get('optimize_for', 'distance') # Tiêu chí tối ưu ('distance' hoặc 'duration') # type: ignore

        # Kiểm tra tính hợp lệ của đầu vào
        if not all([start_address, end_address, selected_cluster_ids]):
            return jsonify({"error": "Thiếu thông tin: start_address, end_address hoặc cluster_ids"}), 400

        print(f"BLL: Start='{start_address}', End='{end_address}', Clusters={len(selected_cluster_ids)}")

        # 2. Geocoding (Chuyển đổi địa chỉ text sang tọa độ [lat, lon])
        start_coord = None
        end_coord = None

        # Tối ưu: Tạo một map tra cứu (Tên -> Tọa độ) từ CSDL (ALL_LANDMARKS)
        # Nếu điểm Start/End là một địa danh có sẵn, ta dùng tọa độ CSDL, không cần gọi API geocode.
        landmarks_by_name = {info["name"]: info["coord"] for info in database.ALL_LANDMARKS.values()}

        # 2a. Xử lý điểm Bắt đầu (Start)
        if start_address in landmarks_by_name:
            start_coord = landmarks_by_name[start_address]  # Lấy từ CSDL
            print(f"BLL: Tìm thấy '{start_address}' trong database.")
        else:
            start_coord = osrm.get_coordinates_from_name(start_address)  # Gọi OSRM API để geocode

        if not start_coord:
            return jsonify({"error": f"Không tìm thấy tọa độ cho điểm xuất phát: '{start_address}'"}), 400

        # 2b. Xử lý điểm Kết thúc (End)
        if end_address in landmarks_by_name:
            end_coord = landmarks_by_name[end_address]  # Lấy từ CSDL
            print(f"BLL: Tìm thấy '{end_address}' trong database.")
        else:
            end_coord = osrm.get_coordinates_from_name(end_address)  # Gọi OSRM API để geocode

        if not end_coord:
            return jsonify({"error": f"Không tìm thấy tọa độ cho điểm kết thúc: '{end_address}'"}), 400

        # 3. Lấy tất cả các điểm con (landmarks) thuộc các cụm đã chọn
        points_from_clusters = database.get_points_for_selected_clusters(selected_cluster_ids)

        # 4. Xây dựng danh sách tổng hợp tất cả các điểm (nodes)
        # Danh sách này bao gồm: Điểm Start, Điểm End, và tất cả các điểm con từ các cụm.
        # Đây là các điểm sẽ được dùng để tính ma trận chi phí.
        
        # [ (tên/id, tọa độ), ... ]
        all_points_info = [("START_POINT", start_coord), ("END_POINT", end_coord)]
        # Map: { tên/id -> index (vị trí trong ma trận) }
        point_name_to_index = {"START_POINT": 0, "END_POINT": 1}
        # List: [ [lat, lon], ... ] (chỉ chứa tọa độ để gửi cho OSRM)
        all_coords_list = [start_coord, end_coord]

        current_index = 2  # Bắt đầu index 2 (vì 0 và 1 đã dành cho Start/End)
        # Thêm các điểm con từ CSDL vào danh sách
        for landmark_id, info in points_from_clusters.items():
            if landmark_id not in point_name_to_index:  # Đảm bảo không thêm trùng
                all_points_info.append((landmark_id, info["coord"]))
                all_coords_list.append(info["coord"])
                point_name_to_index[landmark_id] = current_index
                current_index += 1

        print(f"BLL: Tổng số điểm con cần tính toán ma trận: {len(all_coords_list)}")

        # 5. Gọi OSRM 'table' API
        # Lấy ma trận chi phí (khoảng cách và thời gian) giữa TẤT CẢ các cặp điểm trong `all_coords_list`.
        # Ví dụ: nếu có 50 điểm, OSRM sẽ trả về ma trận 50x50.
        print("BLL: Đang gọi OSRM API (table) để lấy ma trận chi phí...")
        start_time = time.time()
        matrix_data = osrm.get_distance_matrix(all_coords_list)
        if not matrix_data:
            return jsonify({"error": "Không thể lấy ma trận chi phí từ OSRM"}), 500
        print(f"BLL: Lấy ma trận chi phí xong. Thời gian: {time.time() - start_time:.2f}s")

        # 6. Chuẩn bị đầu vào cho GTSP Solver
        # Chuyển đổi định nghĩa cụm từ (ID landmark) sang (index ma trận)
        start_index = point_name_to_index["START_POINT"]  # (luôn là 0)
        end_index = point_name_to_index["END_POINT"]      # (luôn là 1)

        # Lấy định nghĩa cụm cho solver (vd: Cụm 'Quận 1' = [index 5, index 8, index 12])
        solver_clusters = database.get_cluster_definitions_for_solver(
            point_name_to_index,
            selected_cluster_ids
        )
        # Thêm 2 "cụm" đặc biệt: START và END.
        # Solver sẽ hiểu đây là 2 cụm bắt buộc (mỗi cụm chỉ có 1 điểm).
        solver_clusters["START_CLUSTER"] = [start_index]
        solver_clusters["END_CLUSTER"] = [end_index]

        # 7. Khởi chạy GTSP Solver
        print("BLL: Đang chạy GTSP Solver...")
        start_time = time.time()
        # Khởi tạo đối tượng Solver với các tham số
        solver = GTSPGraspSolver(
            distance_matrix=matrix_data['distances'],  # Ma trận khoảng cách từ OSRM
            duration_matrix=matrix_data['durations'],  # Ma trận thời gian từ OSRM
            clusters=solver_clusters,                  # Định nghĩa các cụm (dạng index)
            start_index=start_index,                   # Index điểm bắt đầu
            end_index=end_index,                       # Index điểm kết thúc
            optimize_for=optimize_for                  # Tiêu chí tối ưu
        )

        # Chạy thuật toán giải (ví dụ: 100 vòng lặp GRASP)
        # Kết quả là 1 danh sách các *indices* của lộ trình tối ưu và tổng chi phí.
        optimal_tour_indices, best_cost = solver.solve(max_iterations=100)

        if not optimal_tour_indices:
            return jsonify({"error": "Solver không tìm thấy lộ trình."}), 500

        print(f"BLL: Solver hoàn thành. Lộ trình (indices): {optimal_tour_indices}")
        print(f"BLL: Thời gian chạy Solver: {time.time() - start_time:.2f}s")

        # 8. Xử lý kết quả (Hậu xử lý)
        # Solver chỉ trả về thứ tự các *điểm* (indices), ví dụ: [0, 5, 12, 8, 1].
        # Ta cần gọi OSRM 'route' API cho TỪNG CHẶNG (0->5, 5->12, 12->8, 8->1)
        # để lấy đường đi chi tiết (geometry) vẽ lên bản đồ và thông tin chỉ đường (steps).
        print("BLL: Đang gọi OSRM API (route) để lấy geometry chi tiết...")

        # Tạo map tra cứu ngược: index -> tọa độ, và index -> tên/ID
        index_to_coord = {i: coord for i, (_, coord) in enumerate(all_points_info)}
        index_to_name_id = {i: name_id for i, (name_id, _) in enumerate(all_points_info)}

        route_geometries = []  # Mảng chứa các đoạn geometry (dạng polyline)
        tour_details = []  # Mảng chứa thông tin chi tiết của từng chặng
        total_distance_osrm = 0  # Tổng khoảng cách (tính lại dựa trên API 'route' cho chính xác)
        total_duration_osrm = 0  # Tổng thời gian (tính lại dựa trên API 'route')

        # Duyệt qua lộ trình tối ưu (từng cặp điểm)
        for i in range(len(optimal_tour_indices) - 1):
            idx_from = optimal_tour_indices[i]  # Index điểm đi
            idx_to = optimal_tour_indices[i + 1]  # Index điểm đến

            # Lấy tọa độ tương ứng
            coord_from = index_to_coord[idx_from]
            coord_to = index_to_coord[idx_to]

            # Lấy tên/ID và tra cứu tên thật
            name_id_from = index_to_name_id[idx_from]
            if name_id_from in database.ALL_LANDMARKS:
                name_from = database.ALL_LANDMARKS[name_id_from]["name"]
            else:
                # Xử lý trường hợp đặc biệt cho START/END
                name_from = start_address if name_id_from == "START_POINT" else end_address

            name_id_to = index_to_name_id[idx_to]
            if name_id_to in database.ALL_LANDMARKS:
                name_to = database.ALL_LANDMARKS[name_id_to]["name"]
            else:
                name_to = start_address if name_id_to == "START_POINT" else end_address

            # Gọi OSRM 'route' API để lấy thông tin chi tiết chặng này
            route_info = osrm.get_route_info(coord_from, coord_to)

            # Xử lý kết quả route
            if route_info:
                # Nếu OSRM 'route' thành công
                route_geometries.append(route_info['geometry'])  # Thêm geometry (để vẽ)
                total_distance_osrm += route_info['distance']  # Cộng dồn khoảng cách
                total_duration_osrm += route_info['duration']  # Cộng dồn thời gian
                tour_details.append({
                    "from": name_from,
                    "to": name_to,
                    "distance_km": route_info['distance'],
                    "duration_min": route_info['duration'],
                    "steps": route_info['steps']  # Thêm mảng 'steps' (chỉ đường)
                })
            else:
                # Fallback: Nếu OSRM 'route' thất bại (ví dụ: API lỗi, không tìm thấy đường)
                # Ta sử dụng tạm dữ liệu từ ma trận 'table' (ít chính xác hơn 'route')
                dist = matrix_data['distances'][idx_from][idx_to]
                dur = matrix_data['durations'][idx_from][idx_to]
                total_distance_osrm += dist
                total_duration_osrm += dur
                tour_details.append({
                    "from": name_from,
                    "to": name_to,
                    "distance_km": dist,
                    "duration_min": dur,
                    "steps": []  # Không có steps chi tiết
                })
                # Tạo một geometry đơn giản (đường thẳng)
                # OSRM dùng [lon, lat] cho GeoJSON, trong khi code này dùng [lat, lon]
                # Cần chuyển đổi (coord[1] là lon, coord[0] là lat)
                route_geometries.append({
                    "type": "LineString",
                    "coordinates": [[coord_from[1], coord_from[0]], [coord_to[1], coord_to[0]]]
                })

        print("BLL: Hoàn tất. Trả kết quả về cho Presentation Layer.")

        # 9. Trả kết quả cuối cùng về cho Frontend
        return jsonify({
            "status": "success",
            "optimize_for": optimize_for,  # Tiêu chí đã dùng
            "total_cost": best_cost,  # Chi phí (từ solver, dựa trên ma trận 'table')
            "total_distance_km": total_distance_osrm,  # Tổng khoảng cách (từ API 'route')
            "total_duration_min": total_duration_osrm,  # Tổng thời gian (từ API 'route')
            "tour": tour_details,  # Mảng thông tin chi tiết các chặng
            "geometries": route_geometries  # Mảng các geometry (để vẽ map)
        })

    except Exception as e:
        # Xử lý lỗi tổng (catch-all) nếu có bất kỳ lỗi nào xảy ra trong quá trình
        print(f"Lỗi nghiêm trọng tại /solve_gtsp: {e}")
        import traceback
        traceback.print_exc()  # In chi tiết lỗi (stack trace) ra console
        return jsonify({"error": f"Lỗi máy chủ nội bộ: {str(e)}"}), 500


# Điểm khởi chạy của ứng dụng (khi chạy file python app_logic.py)
if __name__ == '__main__':
    NEW_PORT = 8081
    print(f"--- Lớp Trình diễn (UI) đang chạy tại: http://localhost:{NEW_PORT} ---")
    app.run(debug=True, port=NEW_PORT)