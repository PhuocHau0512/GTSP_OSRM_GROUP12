# logic/database.py
#
# File này hoạt động như một lớp CSDL tĩnh (static database layer).
# Nó định nghĩa tất cả các địa điểm (landmarks) và cách chúng được phân nhóm (clusters).
#
# Cập nhật: Chứa 50 địa điểm tham quan tại TP.HCM
# và được phân thành 11 cụm logic (clusters) cho bài toán GTSP.
#

# 1. Định nghĩa tất cả 50 địa điểm (ID, Tên, Tọa độ Lat/Lon)
# Đây là nguồn dữ liệu chính (master data) cho tất cả các địa điểm.
# Cấu trúc:
# "id_duy_nhat": {"name": "Tên hiển thị", "coord": (latitude, longitude)}
ALL_LANDMARKS = {
    # --- ID duy nhất ---    { "name": "Tên địa điểm", "coord": (lat, lon) }
    "dinh_doc_lap":         {"name": "Dinh Độc Lập", "coord": (10.777963, 106.695676)},
    "nha_tho_duc_ba":       {"name": "Nhà thờ Đức Bà", "coord": (10.779738, 106.699091)},
    "buu_dien_thanh_pho":  {"name": "Bưu điện Thành phố", "coord": (10.779859, 106.699705)},
    "cho_ben_thanh":        {"name": "Chợ Bến Thành", "coord": (10.772169, 106.698268)},
    "ben_nha_rong":         {"name": "Bến Nhà Rồng", "coord": (10.768987, 106.706482)},
    "nha_hat_thanh_pho":    {"name": "Nhà hát Thành phố", "coord": (10.777417, 106.703293)},
    "bao_tang_ctct":        {"name": "Bảo tàng Chứng tích Chiến tranh", "coord": (10.779322, 106.692845)},
    "chua_vinh_nghiem":      {"name": "Chùa Vĩnh Nghiêm", "coord": (10.783190, 106.672354)},
    "pho_nguyen_hue":       {"name": "Phố đi bộ Nguyễn Huệ", "coord": (10.773372, 106.703539)},
    "dhqg_hcm_cs1":         {"name": "Đại học Quốc gia TP.HCM - Cơ sở 1", "coord": (10.762881, 106.682426)},
    "landmark_81":          {"name": "Landmark 81", "coord": (10.796419, 106.721731)},
    "cong_vien_tao_dan":    {"name": "Công viên Tao Đàn", "coord": (10.779074, 106.691272)},
    "bao_tang_my_thuat":    {"name": "Bảo tàng Mỹ thuật", "coord": (10.768834, 106.691037)},
    "nha_tho_tan_dinh":     {"name": "Nhà thờ Tân Định", "coord": (10.7891, 106.6896)},
    "cho_binh_tay":         {"name": "Chợ Bình Tây", "coord": (10.758234, 106.662345)},
    "thao_cam_vien":        {"name": "Thảo Cầm Viên Sài Gòn", "coord": (10.7842, 106.7053)},
    "bao_tang_ls_vn":       {"name": "Bảo tàng Lịch sử Việt Nam", "coord": (10.7836, 106.7049)},
    "chua_giac_lam":        {"name": "Chùa Giác Lâm", "coord": (10.7712, 106.6502)},
    "chua_ba_thien_hau":    {"name": "Chùa Bà Thiên Hậu (Nguyễn Trãi)", "coord": (10.7523, 106.6631)},
    "chua_ngoc_hoang":      {"name": "Chùa Ngọc Hoàng (Phước Hải Tự)", "coord": (10.7900, 106.6925)},
    "bao_tang_fito":        {"name": "Bảo tàng Fito (Y học Cổ truyền)", "coord": (10.7709, 106.6745)},
    "bitexco_skydeck":      {"name": "Tòa nhà Bitexco (Skydeck)", "coord": (10.7719, 106.7044)},
    "ubnd_tphcm":           {"name": "Tòa nhà Ủy ban Nhân dân Thành phố", "coord": (10.7766, 106.7011)},
    "cho_an_dong":          {"name": "Chợ An Đông", "coord": (10.7580, 106.6698)},
    "cv_nuoc_dam_sen":      {"name": "Công viên nước Đầm Sen", "coord": (10.7675, 106.6368)},
    "kdl_suoi_tien":        {"name": "Khu du lịch Suối Tiên", "coord": (10.8654, 106.8058)},
    "pho_tay_bui_vien":     {"name": "Phố Tây Bùi Viện", "coord": (10.7676, 106.6917)},
    "cau_anh_sao_q7":       {"name": "Cầu Ánh Sao (Quận 7)", "coord": (10.7291, 106.7138)},
    "duong_sach_nvb":       {"name": "Đường sách Nguyễn Văn Bình", "coord": (10.7803, 106.6997)},
    "ho_con_rua":           {"name": "Hồ Con Rùa", "coord": (10.7813, 106.6946)},
    "cau_mong":             {"name": "Cầu Mống", "coord": (10.7680, 106.7037)},
    "lang_ong_ba_chieu":    {"name": "Lăng Ông Bà Chiểu", "coord": (10.7963, 106.6897)},
    "cho_hoa_ho_thi_ky":    {"name": "Chợ hoa Hồ Thị Kỷ", "coord": (10.7634, 106.6713)},
    "chua_xa_loi":          {"name": "Chùa Xá Lợi", "coord": (10.7787, 106.6908)},
    "bao_tang_tphcm":       {"name": "Bảo tàng TPHCM (Dinh Gia Long)", "coord": (10.7744, 106.7007)},
    "bao_tang_ao_dai":      {"name": "Bảo tàng Áo Dài", "coord": (10.8495, 106.7865)},
    "bao_tang_phu_nu":      {"name": "Bảo tàng Phụ nữ Nam Bộ", "coord": (10.7831, 106.6853)},
    "chua_ong_q5":          {"name": "Chùa Ông (Nghĩa An Hội Quán)", "coord": (10.7513, 106.6644)},
    "nha_tho_huyen_sy":     {"name": "Nhà thờ Huyện Sỹ", "coord": (10.7703, 106.6865)},
    "tu_vien_khanh_an":     {"name": "Tu viện Khánh An", "coord": (10.8524, 106.6437)},
    "chua_buu_long":        {"name": "Chùa Bửu Long", "coord": (10.8797, 106.8066)},
    "den_hung_q9":          {"name": "Đền Hùng (Quận 9)", "coord": (10.8532, 106.7928)},
    "mua_roi_nuoc_rong_vang": {"name": "Nhà hát múa rối nước Rồng Vàng", "coord": (10.7800, 106.6914)},
    "cho_tan_dinh":         {"name": "Chợ Tân Định", "coord": (10.7891, 106.6896)},
    "saigon_centre":        {"name": "Saigon Centre (Takashimaya)", "coord": (10.7717, 106.7029)},
    "crescent_mall":        {"name": "Crescent Mall", "coord": (10.7289, 106.7118)},
    "sc_vivocity":          {"name": "SC VivoCity", "coord": (10.7335, 106.6994)},
    "cong_vien_gia_dinh":   {"name": "Công viên Gia Định", "coord": (10.8065, 106.6759)},
    "cho_ba_chieu":         {"name": "Chợ Bà Chiểu", "coord": (10.7951, 106.6911)},
    "dia_dao_cu_chi":       {"name": "Địa đạo Củ Chi (Bến Dược)", "coord": (11.1444, 106.4632)},
}


# 2. Định nghĩa các CỤM (Clusters)
# Đây là logic nghiệp vụ cốt lõi cho bài toán GTSP (Generalized TSP).
# Chúng ta nhóm các địa điểm (landmarks) lại thành các cụm.
# Solver (thuật toán) sẽ được yêu cầu đi thăm ÍT NHẤT MỘT điểm từ mỗi cụm được chọn.
# Cấu trúc:
# "cluster_id": {"name": "Tên cụm hiển thị", "members": [danh sách các "id_duy_nhat" từ ALL_LANDMARKS]}
CLUSTERS = {
    "cluster_q1_core": {
        "name": "Cụm T.Tâm Lịch sử (Q.1)",
        "members": [
            "dinh_doc_lap", "nha_tho_duc_ba", "buu_dien_thanh_pho",
            "nha_hat_thanh_pho", "ubnd_tphcm", "pho_nguyen_hue",
            "duong_sach_nvb", "bao_tang_tphcm"
        ]
    },
    "cluster_q1_museum_park": {
        "name": "Cụm Bảo tàng & Công viên (Q.1)",
        "members": [
            "bao_tang_ctct", "bao_tang_ls_vn", "thao_cam_vien",
            "cong_vien_tao_dan", "mua_roi_nuoc_rong_vang", "ho_con_rua"
        ]
    },
    "cluster_q1_market_port": {
        "name": "Cụm Chợ Bến Thành & Bến cảng (Q.1)",
        "members": [
            "cho_ben_thanh", "bitexco_skydeck", "saigon_centre",
            "ben_nha_rong", "cau_mong", "bao_tang_my_thuat",
            "pho_tay_bui_vien", "nha_tho_huyen_sy"
        ]
    },
    "cluster_q3_phunhuan": {
        "name": "Cụm Q.3 & Phú Nhuận",
        "members": [
            "chua_vinh_nghiem", "nha_tho_tan_dinh", "chua_xa_loi",
            "bao_tang_phu_nu", "cho_tan_dinh"
        ]
    },
    "cluster_cholon_q5_q6": {
        "name": "Cụm Chợ Lớn (Q.5, Q.6)",
        "members": [
            "cho_binh_tay", "chua_ba_thien_hau", "cho_an_dong", "chua_ong_q5"
        ]
    },
    "cluster_q10_q11": {
        "name": "Cụm Q.10 & Q.11",
        "members": [
            "dhqg_hcm_cs1", "chua_giac_lam", "bao_tang_fito",
            "cv_nuoc_dam_sen", "cho_hoa_ho_thi_ky"
        ]
    },
    "cluster_binhthanh_govap": {
        "name": "Cụm Bình Thạnh & Gò Vấp",
        "members": [
            "landmark_81", "chua_ngoc_hoang", "lang_ong_ba_chieu",
            "cong_vien_gia_dinh", "cho_ba_chieu"
        ]
    },
    "cluster_q7": {
        "name": "Cụm Quận 7",
        "members": [
            "cau_anh_sao_q7", "crescent_mall", "sc_vivocity"
        ]
    },
    "cluster_thuduc_xa": {
        "name": "Cụm TP. Thủ Đức (Xa)",
        "members": [
            "kdl_suoi_tien", "bao_tang_ao_dai", "chua_buu_long", "den_hung_q9"
        ]
    },
    "cluster_q12_hocmon": {
        "name": "Cụm Q.12 & Hóc Môn",
        "members": [
            "tu_vien_khanh_an"
        ]
    },
    "cluster_cuchi_ratxa": {
        "name": "Cụm Củ Chi (Rất Xa)",
        "members": [
            "dia_dao_cu_chi"
        ]
    }
}


# --- Các hàm truy xuất dữ liệu ---
# Các hàm này cung cấp một giao diện (interface) sạch
# để lớp BLL (app_logic.py) tương tác với dữ liệu mà không cần biết cấu trúc bên trong.

def get_all_clusters_info():
    """
    Lấy thông tin cơ bản của tất cả các cụm để hiển thị trên UI (Frontend).
    Hàm này không trả về danh sách thành viên (members) để giữ cho payload nhẹ.
    
    Trả về:
    Dict { cluster_id: { "name": "Tên cụm", "representative_coord": (lat, lon) } }
    """
    info = {}  # Khởi tạo dict kết quả
    # Duyệt qua tất cả các cụm đã định nghĩa trong CLUSTERS
    for cluster_id, data in CLUSTERS.items():
        if not data["members"]:
            continue  # Bỏ qua nếu cụm bị định nghĩa rỗng

        # Lấy ID của địa điểm đầu tiên trong danh sách thành viên
        first_member_id = data["members"][0]
        
        # Kiểm tra xem địa điểm này có tồn tại trong CSDL ALL_LANDMARKS không
        if first_member_id in ALL_LANDMARKS:
            # Lấy tọa độ của điểm đầu tiên này làm "tọa độ đại diện"
            # (dùng để ghim 1 điểm trên bản đồ đại diện cho cả cụm)
            representative_coord = ALL_LANDMARKS[first_member_id]["coord"]
            info[cluster_id] = {
                "name": data["name"],
                "representative_coord": representative_coord
            }
    return info  # Trả về dict chứa thông tin các cụm


def get_points_for_selected_clusters(cluster_ids: list[str]) -> dict:
    """
    Lấy tất cả các điểm con (landmarks) từ các cụm đã được chọn (cluster_ids).
    Đây là tất cả các điểm sẽ được dùng để tính toán ma trận chi phí OSRM.

    Input:
    - cluster_ids: Một danh sách các ID của cụm, ví dụ: ["cluster_q1_core", "cluster_q7"]

    Trả về:
    Dict { "landmark_id": {"name": ..., "coord": ...}, ... }
    Ví dụ: { "dinh_doc_lap": {...}, "nha_tho_duc_ba": {...}, "cau_anh_sao_q7": {...}, ... }
    """
    points = {}  # Khởi tạo dict kết quả
    # Duyệt qua danh sách các ID cụm mà người dùng đã chọn
    for cluster_id in cluster_ids:
        # Kiểm tra xem cluster_id này có tồn tại trong CSDL CLUSTERS không
        if cluster_id in CLUSTERS:
            # Nếu có, duyệt qua tất cả các thành viên (landmark_id) trong cụm đó
            for landmark_id in CLUSTERS[cluster_id]["members"]:
                # Thêm địa điểm vào dict kết quả
                # (Nếu landmark_id đã tồn tại, nó sẽ không được thêm lại - dict tự xử lý)
                # (Đồng thời kiểm tra xem landmark_id có trong ALL_LANDMARKS không)
                if landmark_id not in points and landmark_id in ALL_LANDMARKS:
                    points[landmark_id] = ALL_LANDMARKS[landmark_id]
    return points  # Trả về dict chứa tất cả các địa điểm con


def get_cluster_definitions_for_solver(points_map: dict, cluster_ids: list[str]) -> dict:
    """
    Hàm này thực hiện một bước chuyển đổi quan trọng:
    Nó chuyển đổi định nghĩa cụm từ dạng (list of landmark_id) sang dạng (list of matrix_index).
    Đây là định dạng mà thuật toán GTSP (Solver) yêu cầu.

    Input:
    - points_map: Một dict ánh xạ từ "landmark_id" sang "vị trí (index) trong ma trận chi phí".
                  Ví dụ: {"START_POINT": 0, "END_POINT": 1, "dinh_doc_lap": 2, "nha_tho_duc_ba": 3, ...}
    - cluster_ids: list các cluster_id người dùng chọn (giống hàm trên)

    Output:
    - Dict { "cluster_id": [list_of_indices], ... }
    - Ví dụ: { "cluster_q1_core": [2, 3, 8, 10], "cluster_q7": [15, 16], ... }
    """
    solver_clusters = {}  # Khởi tạo dict kết quả
    # Duyệt qua các ID cụm người dùng đã chọn
    for cluster_id in cluster_ids:
        # Kiểm tra xem ID cụm có hợp lệ không
        if cluster_id in CLUSTERS:
            indices = []  # Danh sách tạm để chứa các *index* của cụm này
            # Duyệt qua từng thành viên (landmark_id) của cụm
            for landmark_id in CLUSTERS[cluster_id]["members"]:
                # Kiểm tra xem landmark_id này có trong map ánh xạ không
                # (Nó phải luôn có, vì `points_map` được tạo từ chính các điểm này)
                if landmark_id in points_map:
                    # Lấy index tương ứng (ví dụ: 2) và thêm vào danh sách
                    indices.append(points_map[landmark_id])
            
            # Nếu danh sách index không rỗng (tức là cụm có thành viên)
            if indices:
                # Gán danh sách index này cho cluster_id tương ứng
                solver_clusters[cluster_id] = indices
    return solver_clusters  # Trả về định nghĩa cụm (dạng index) cho solver