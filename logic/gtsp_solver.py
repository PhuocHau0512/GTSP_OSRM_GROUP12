# logic/gtsp_solver.py
import random  # Thư viện để thực hiện các lựa chọn ngẫu nhiên

class GTSPGraspSolver:
    """
    Giải bài toán GTSP (Generalized TSP - Bài toán Người bán hàng Tổng quát)
    bằng thuật toán GRASP (Greedy Randomized Adaptive Search Procedure).

    Mục tiêu:
    Tìm một lộ trình (tour) bắt đầu từ 'start_index', kết thúc tại 'end_index',
    và đi qua MỖI CỤM (cluster) trong 'clusters' đúng MỘT LẦN.
    
    Lưu ý: Thuật toán này giải quyết bài toán ở mức độ *cụm*. Nó tìm ra
    *thứ tự các cụm* và *điểm đại diện* cho mỗi cụm để tối ưu hóa chi phí.
    """

    def __init__(self, distance_matrix, duration_matrix, clusters,
                 start_index, end_index, optimize_for='distance'):
        """
        Hàm khởi tạo (Constructor) của lớp Solver.
        
        Tham số:
        - distance_matrix: Ma trận (list 2D) lưu khoảng cách giữa các điểm (nodes).
        - duration_matrix: Ma trận (list 2D) lưu thời gian di chuyển giữa các điểm.
        - clusters: Dict định nghĩa các cụm.
          Vd: {"cluster_id_1": [index1, index2], "cluster_id_2": [index3, index4], ...}
          LƯU Ý: dict này phải BAO GỒM cả cụm START và cụm END.
        - start_index: Index của điểm bắt đầu (ví dụ: 0).
        - end_index: Index của điểm kết thúc (ví dụ: 1).
        - optimize_for: Tiêu chí tối ưu ('distance' hoặc 'time').
        """
        
        self.distance_matrix = distance_matrix
        self.duration_matrix = duration_matrix
        self.optimize_for = optimize_for
        
        # clusters là dict: {"cluster_id": [index1, index2], ...}
        # Đã bao gồm cả cụm Start và End
        self.clusters = clusters
        
        # Tạo map tra cứu ngược: từ index (của điểm con) về cluster_id
        # Giúp nhanh chóng biết một điểm (index) thuộc cụm nào.
        # Vd: { index1: "cluster_id_1", index2: "cluster_id_1", index3: "cluster_id_2", ... }
        self.index_to_cluster = {}
        for cluster_id, indices in clusters.items():
            for index in indices:
                self.index_to_cluster[index] = cluster_id
        
        self.start_index = start_index
        self.end_index = end_index
        self.n_nodes = len(distance_matrix)  # Tổng số điểm con (nodes) trong ma trận
        self.n_clusters = len(clusters)      # Tổng số cụm cần thăm (gồm cả Start/End)

    def get_cost(self, i, j):
        """
        Hàm tiện ích: Lấy chi phí (cost) di chuyển từ điểm i đến điểm j
        dựa trên tiêu chí tối ưu (optimize_for) đã chọn.
        """
        # Kiểm tra tính hợp lệ của index
        if i < 0 or j < 0 or i >= self.n_nodes or j >= self.n_nodes:
            return float('inf')  # Chi phí vô cùng lớn nếu index không hợp lệ
        
        if self.optimize_for == 'time':
            return self.duration_matrix[i][j]
        else:
            return self.distance_matrix[i][j]

    def calculate_total_cost(self, tour):
        """Tính tổng chi phí của một lộ trình (tour)"""
        # tour là một danh sách các index, ví dụ: [0, 5, 12, 8, 1]
        total = 0
        for i in range(len(tour) - 1):
            # Cộng dồn chi phí của từng chặng (ví dụ: 0->5, 5->12, 12->8, 8->1)
            total += self.get_cost(tour[i], tour[i+1])
        return total

    def construction_phase(self, alpha=0.4):
        """
        Pha Xây dựng (Construction Phase) của thuật toán GRASP cho GTSP.
        Tạo ra một lộ trình "khá tốt" một cách tham lam và ngẫu nhiên.
        
        Tham số:
        - alpha (0 <= alpha <= 1): Hệ số ngẫu nhiên.
          + alpha = 0: Thuật toán tham lam thuần túy (luôn chọn cái tốt nhất).
          + alpha = 1: Thuật toán ngẫu nhiên thuần túy (chọn bất kỳ).
          + 0 < alpha < 1: Tham lam có ngẫu nhiên (GRASP).
        """
        # Bắt đầu lộ trình với điểm start_index
        tour = [self.start_index]
        
        # Xác định cụm hiện tại (cụm START)
        current_cluster = self.index_to_cluster[self.start_index]
        
        # Tạo một tập (set) chứa các cụm CHƯA được thăm
        unvisited_clusters = set(self.clusters.keys())
        unvisited_clusters.discard(current_cluster)  # Loại bỏ cụm START
        
        # Lặp cho đến khi lộ trình đi qua đủ số cụm (self.n_clusters)
        while len(tour) < self.n_clusters:
            current_index = tour[-1]  # Điểm cuối cùng vừa thêm vào tour
            
            # Tìm các ứng viên (candidates) cho bước đi tiếp theo
            # candidate = (chi phí, điểm_đến, cụm_đến)
            candidates = []
            
            # Chỉ tìm điểm đến ở các cụm CHƯA THĂM
            target_clusters = unvisited_clusters
            
            # --- Xử lý logic đặc biệt cho điểm KẾT THÚC (END) ---
            # Nếu chỉ còn 1 cụm chưa thăm, VÀ cụm đó là cụm END
            # -> Bắt buộc bước tiếp theo phải đi đến cụm END.
            end_cluster_id = self.index_to_cluster[self.end_index]
            if len(unvisited_clusters) == 1 and end_cluster_id in unvisited_clusters:
                 target_clusters = {end_cluster_id}  # Chỉ đi đến cụm END

            # Duyệt qua các cụm mục tiêu (chưa thăm)
            for cluster_id in target_clusters:
                # Duyệt qua TẤT CẢ các điểm con (nodes) trong cụm đó
                for next_index in self.clusters[cluster_id]:
                    cost = self.get_cost(current_index, next_index)
                    if cost != float('inf'):  # Nếu có đường đi
                        candidates.append((cost, next_index, cluster_id))
            
            if not candidates:
                # Trường hợp bị kẹt (không tìm thấy đường đi)
                # (ví dụ: ma trận chi phí bị lỗi hoặc điểm bị cô lập)
                # Cố gắng thêm điểm cuối (nếu chưa có) và thoát
                if self.end_index not in tour:
                    tour.append(self.end_index)
                return tour  # Trả về lộ trình lỗi

            # Tìm chi phí min/max từ các ứng viên
            min_cost = min(candidates, key=lambda x: x[0])[0]
            max_cost = max(candidates, key=lambda x: x[0])[0]
            
            # Tạo Danh sách Ứng viên Hạn chế (RCL - Restricted Candidate List)
            # RCL bao gồm các ứng viên "đủ tốt"
            # Ngưỡng (threshold) = min_cost + alpha * (max_cost - min_cost)
            threshold = min_cost + alpha * (max_cost - min_cost)
            
            # Thêm 1e-9 để xử lý sai số dấu phẩy động
            rcl = [c for c in candidates if c[0] <= threshold + 1e-9]
            
            if not rcl:
                rcl = candidates  # Fallback (nếu rcl rỗng, dùng tất cả ứng viên)
            
            # Chọn NGẪU NHIÊN một ứng viên từ RCL
            chosen_cost, chosen_index, chosen_cluster = random.choice(rcl)
            
            # Thêm điểm được chọn vào lộ trình
            tour.append(chosen_index)
            # Đánh dấu cụm tương ứng là "đã thăm"
            unvisited_clusters.remove(chosen_cluster)
        
        # Đảm bảo điểm kết thúc (end_index) LUÔN là điểm cuối cùng
        # (Vì vòng lặp trên có thể chọn điểm END ở giữa)
        if tour[-1] != self.end_index:
            if self.end_index in tour:
                tour.remove(self.end_index)  # Xóa nếu nó nằm ở giữa
            # Thêm điểm END vào cuối cùng
            # (Nếu điểm cuối cùng *đã là* end_index, không làm gì cả)
            tour.append(self.end_index)
            
        return tour  # Trả về lộ trình đã xây dựng

    def local_search_2opt(self, tour):
        """
        Pha Cải tiến (Local Search) - Thuật toán 2-opt.
        Mục đích: Tối ưu hóa THỨ TỰ của các điểm/cụm trong lộ trình.
        Nó thử đảo ngược một đoạn của lộ trình để xem chi phí có giảm không.

        Ví dụ: Lộ trình A -> B -> C -> D
        Thử: A -> C -> B -> D (đảo đoạn B-C)
        Nếu cost(A->C) + cost(B->D) < cost(A->B) + cost(C->D) thì chấp nhận.

        LƯU Ý: Chúng ta giữ cố định điểm đầu (index 0) và điểm cuối (index -1).
        """
        best_tour = tour
        best_cost = self.calculate_total_cost(tour)
        n = len(tour)
        improved = True  # Cờ (flag) kiểm tra xem còn cải thiện được không
        
        while improved:
            improved = False
            # i từ 1 (sau điểm START)
            for i in range(1, n - 2):
                # j từ i+1 (sau i)
                for j in range(i + 1, n - 1):  # (trước điểm END)
                    
                    # Lấy 4 điểm liên quan đến 2 cạnh (i-1 -> i) và (j -> j+1)
                    p_i_minus_1 = tour[i-1] # (A)
                    p_i = tour[i]           # (B)
                    p_j = tour[j]           # (C)
                    p_j_plus_1 = tour[j+1]  # (D)

                    # Chi phí của 2 cạnh cũ: (A->B) và (C->D)
                    cost_before = self.get_cost(p_i_minus_1, p_i) + self.get_cost(p_j, p_j_plus_1)
                    # Chi phí của 2 cạnh mới (nếu đảo): (A->C) và (B->D)
                    cost_after = self.get_cost(p_i_minus_1, p_j) + self.get_cost(p_i, p_j_plus_1)
                    
                    # Chênh lệch chi phí
                    cost_delta = cost_after - cost_before

                    # Nếu chi phí giảm (nhỏ hơn 0, dùng -1e-9 để tránh sai số)
                    if cost_delta < -1e-9:  # Cải thiện
                        # Đảo ngược đoạn [i, j]
                        tour = tour[:i] + tour[i:j+1][::-1] + tour[j+1:]
                        
                        best_tour = tour
                        best_cost += cost_delta
                        improved = True  # Đánh dấu là đã cải thiện
                        break  # Thoát vòng lặp j
                if improved:
                    break  # Thoát vòng lặp i (bắt đầu lại từ đầu với tour mới)
        
        return best_tour  # Trả về lộ trình tốt nhất sau 2-opt

    def local_search_intra_cluster(self, tour):
        """
        Pha Cải tiến (Local Search) - Cải tiến nội cụm (Intra-Cluster).
        Mục đích: Tối ưu hóa việc CHỌN ĐIỂM ĐẠI DIỆN cho mỗi cụm.
        
        Với mỗi điểm trong lộ trình (trừ Start/End),
        thử thay thế nó bằng một điểm KHÁC trong CÙNG CỤM của nó.
        
        Ví dụ: Lộ trình ... -> A -> B1 -> C -> ... (B1 thuộc cụm Cluster_B)
        Thử: ... -> A -> B2 -> C -> ... (B2 cũng thuộc Cluster_B)
        Nếu cost(A->B2) + cost(B2->C) < cost(A->B1) + cost(B1->C) thì chấp nhận.
        """
        n = len(tour)
        improved = True
        
        while improved:
            improved = False
            # Duyệt qua các điểm (nodes) trong lộ trình
            # Bỏ qua điểm đầu (index 0) và cuối (index n-1)
            for i in range(1, n - 1):
                current_index = tour[i]  # Điểm đang xét (ví dụ: B1)
                current_cluster_id = self.index_to_cluster.get(current_index)
                
                # Lấy 2 điểm lân cận
                prev_index = tour[i-1]  # (A)
                next_index = tour[i+1]  # (C)
                
                # Chi phí hiện tại của đoạn ...A -> B1 -> C...
                cost_before = self.get_cost(prev_index, current_index) + self.get_cost(current_index, next_index)
                
                best_new_index = current_index  # Tạm thời, điểm tốt nhất vẫn là điểm hiện tại
                
                # Thử TẤT CẢ các điểm khác (candidate) trong cùng cụm
                for candidate_index in self.clusters[current_cluster_id]:
                    if candidate_index == current_index:
                        continue  # Bỏ qua chính nó
                    
                    # Chi phí mới nếu thay (B1) bằng (candidate)
                    # ...A -> candidate -> C...
                    cost_after = self.get_cost(prev_index, candidate_index) + self.get_cost(candidate_index, next_index)
                    
                    if cost_after < cost_before - 1e-9:  # Nếu tìm thấy cải thiện
                        cost_before = cost_after  # Cập nhật chi phí tốt nhất
                        best_new_index = candidate_index  # Lưu lại điểm thay thế tốt nhất
                        improved = True
                
                if improved:
                    # Nếu tìm thấy cải thiện (best_new_index != current_index)
                    # Cập nhật lộ trình (thay thế điểm cũ bằng điểm mới)
                    tour[i] = best_new_index
                    break  # Thoát vòng lặp for i và bắt đầu lại từ đầu
        
        return tour  # Trả về lộ trình tốt nhất sau khi tối ưu nội cụm

    def solve(self, max_iterations=50, progress_callback=None):
        """
        Hàm chính: Chạy thuật toán GRASP.
        Kết hợp Pha Xây dựng và Pha Cải tiến trong nhiều vòng lặp.
        
        Tham số:
        - max_iterations: Số lần chạy GRASP (ví dụ: 50, 100, 1000).
        - progress_callback: (Tùy chọn) Hàm callback để báo cáo tiến độ.
        """
        best_tour_so_far = None  # Lộ trình tốt nhất tìm được
        best_cost_so_far = float('inf')  # Chi phí tốt nhất tương ứng
        
        print(f"BLL: Bắt đầu GRASP Solver với {max_iterations} vòng lặp...")
        
        for iteration in range(max_iterations):
            # 1. Pha Xây dựng (Construction)
            # Tạo 1 lộ trình "khá tốt" (có ngẫu nhiên)
            current_tour = self.construction_phase()
            
            # 2. Pha Cải tiến (Local Search)
            # Liên tục cải tiến lộ trình này cho đến khi không thể tốt hơn
            improved = True
            while improved:
                cost_before_opt = self.calculate_total_cost(current_tour)
                
                # 2a. Cải tiến 2-Opt (Tối ưu thứ tự cụm)
                current_tour = self.local_search_2opt(current_tour)
                
                # 2b. Cải tiến nội cụm (Tối ưu điểm đại diện)
                current_tour = self.local_search_intra_cluster(current_tour)
                
                # Tính chi phí sau 2 bước cải tiến
                cost_after_opt = self.calculate_total_cost(current_tour)
                
                # Nếu chi phí không giảm nữa (hoặc giảm không đáng kể)
                if cost_after_opt >= cost_before_opt - 1e-9:
                    improved = False  # Dừng cải tiến
            
            # Lộ trình (current_tour) bây giờ là "tối ưu cục bộ" (local optimum)
            current_cost = self.calculate_total_cost(current_tour)
            
            # 3. Cập nhật kết quả tốt nhất (Best Solution Update)
            # So sánh với kết quả tốt nhất *từ trước đến nay*
            if current_cost < best_cost_so_far:
                best_cost_so_far = current_cost
                best_tour_so_far = current_tour.copy()  # Lưu lại bản sao
            
            # (Tùy chọn) Gọi callback để báo cáo tiến độ
            if progress_callback:
                progress = (iteration + 1) / max_iterations * 100
                progress_callback(progress, best_cost_so_far)
        
        # Sau khi chạy hết các vòng lặp (iterations)
        print(f"BLL: Solver hoàn tất. Chi phí tốt nhất: {best_cost_so_far}")
        # Trả về lộ trình tốt nhất (tối ưu toàn cục - global optimum) tìm được
        return best_tour_so_far, best_cost_so_far