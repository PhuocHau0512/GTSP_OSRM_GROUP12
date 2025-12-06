// presentation/static/app.js

/**
 * Địa chỉ API của Lớp Logic nghiệp vụ (BLL)
 * Đây là server Flask (app_logic.py) chạy ở cổng 5001.
 */
const BLL_API_URL = "http://localhost:5001";

// --- CÁC HÀM HỖ TRỢ ĐỊNH DẠNG (Từ lần trước) ---

/**
 * Định dạng thời gian (tổng số phút) thành chuỗi "X giờ Y phút"
 * @param {number} totalMinutes - Tổng số phút
 * @returns {string} - Chuỗi đã định dạng
 */
function formatDuration(totalMinutes) {
    if (totalMinutes < 0.1) return "0 phút";
    if (totalMinutes < 1) return "dưới 1 phút";
    const roundedMinutes = Math.round(totalMinutes);
    if (roundedMinutes < 60) return `${totalMinutes.toFixed(1).replace(/\.0$/, '')} phút`;
    const hours = Math.floor(roundedMinutes / 60);
    const minutes = roundedMinutes % 60;
    if (minutes === 0) return `${hours} giờ`;
    return `${hours} giờ ${minutes} phút`;
}

/**
 * Định dạng quãng đường (tổng số km) thành chuỗi "X km" hoặc "Y m"
 * @param {number} totalKm - Tổng số km
 * @returns {string} - Chuỗi đã định dạng
 */
function formatDistance(totalKm) {
    if (totalKm < 0.01) return "0 m";
    if (totalKm < 1.0) return `${Math.round(totalKm * 1000)} m`;
    return `${totalKm.toFixed(1).replace(/\.0$/, '')} km`;
}

// --- HÀM HỖ TRỢ DỊCH HƯỚNG DẪN (MỚI) ---

/**
 * Dịch thông tin 'step' (chỉ đường chi tiết) từ OSRM sang Tiếng Việt
 * @param {object} step - Đối tượng step từ OSRM (đã được BLL xử lý)
 * @returns {string} - Chuỗi hướng dẫn (ví dụ: "Rẽ trái vào Lê Lợi (trong 500 m)")
 */
function getManeuverText(step) {
    const type = step.maneuver_type;
    const modifier = step.maneuver_modifier;
    
    // Bảng tra cứu để dịch các thuật ngữ của OSRM
    const translations = {
        'depart': 'Khởi hành',
        'arrive': 'Đến nơi',
        'turn': 'Rẽ',
        'new name': 'Đi vào',
        'continue': 'Tiếp tục',
        'fork': 'Đi theo lối',
        'end of road': 'Hết đường',
        'roundabout': 'Đi vào vòng xuyến',
        'rotary': 'Đi vào vòng xuyến',
        'left': 'trái',
        'right': 'phải',
        'slight left': 'hơi rẽ trái',
        'slight right': 'hơi rẽ phải',
        'sharp left': 'rẽ trái gắt',
        'sharp right': 'rẽ phải gắt',
        'straight': 'đi thẳng',
        'uturn': 'quay đầu'
    };
    
    let text = translations[type] || type; // Lấy từ bảng dịch, nếu không có thì dùng từ gốc
    // Thêm chi tiết (trái, phải, thẳng...)
    if (modifier && translations[modifier]) {
        text += ` ${translations[modifier]}`;
    }
    
    // Thêm tên đường (nếu có)
    if (step.name && step.name !== '') {
        text += ` vào <b>${step.name}</b>`;
    }
    
    // Thêm khoảng cách (step.distance là mét, cần đổi sang km để dùng formatDistance)
    const distanceStr = formatDistance(step.distance / 1000); 
    
    return `${text} (trong ${distanceStr})`;
}


// 1. KHỞI TẠO CÁC ĐỐI TƯỢNG GIAO DIỆN (DOM Elements)
// Tham chiếu đến các phần tử HTML để tương tác
const map = L.map('map').setView([10.7769, 106.7009], 12); // Tọa độ trung tâm Sài Gòn
const clusterListDiv = document.getElementById('cluster-list');
const solveForm = document.getElementById('solve-form');
const loadingOverlay = document.getElementById('loading');
const resultsSummaryDiv = document.getElementById('results-summary');

// Biến toàn cục để quản lý các lớp (layers) trên bản đồ
let clusterMarkers = []; // Mảng chứa các marker của cụm
let routeLayer = null;   // Layer chứa đường đi (sẽ bị xóa và vẽ lại)
let startEndMarkers = []; // Mảng chứa marker điểm đầu, cuối và các điểm dừng


// 2. THIẾT LẬP BẢN ĐỒ LEAFLET
// Sử dụng tile layer (hình ảnh bản đồ) từ OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// 3. HÀM TẢI DANH SÁCH CỤM TỪ BLL (API)
async function loadClusters() {
    try {
        // Gọi API /get_clusters từ BLL
        const response = await fetch(`${BLL_API_URL}/get_clusters`);
        if (!response.ok) {
            // Xử lý lỗi nếu API trả về (vd: 400, 500)
            const err = await response.json();
            throw new Error(err.error || 'Không thể tải danh sách cụm');
        }
        const clusters = await response.json();
        
        clusterListDiv.innerHTML = ''; // Xóa nội dung cũ (nếu có)
        
        // Duyệt qua từng cụm nhận được từ BLL
        Object.entries(clusters).forEach(([clusterId, data]) => {
            // Tạo HTML cho checkbox
            clusterListDiv.innerHTML += `
                <div class="form-check">
                    <input class="form-check-input cluster-checkbox" type="checkbox" value="${clusterId}" id="cluster_${clusterId}">
                    <label class="form-check-label" for="cluster_${clusterId}">
                        ${data.name}
                    </label>
                </div>
            `;
            // Tạo marker (gút) đại diện cho cụm và thêm vào bản đồ
            const [lat, lon] = data.representative_coord;
            const marker = L.marker([lat, lon], { opacity: 0.7 })
                .bindPopup(`<b>Cụm:</b> ${data.name}`)
                .addTo(map);
            clusterMarkers.push(marker); // Lưu lại để quản lý
        });
    } catch (error) {
        console.error(error);
        clusterListDiv.innerHTML = `<p class="text-danger"><b>Lỗi:</b> ${error.message}</p>`;
    }
}

// 4. HÀM XỬ LÝ SỰ KIỆN SUBMIT FORM (Khi người dùng nhấn nút "Tìm đường")
solveForm.addEventListener('submit', async (e) => {
    e.preventDefault(); // Ngăn chặn hành vi submit mặc định của form (tải lại trang)
    
    // Lấy giá trị từ các ô input
    const startAddress = document.getElementById('start-address').value;
    const endAddress = document.getElementById('end-address').value;
    const optimizeFor = document.getElementById('optimize-for').value;
    
    // Lấy danh sách các ID cụm đã được check
    const selectedClusters = Array.from(
        document.querySelectorAll('.cluster-checkbox:checked')
    ).map(cb => cb.value);
    
    // Kiểm tra, bắt buộc chọn ít nhất 1 cụm
    if (selectedClusters.length === 0) {
        alert('Vui lòng chọn ít nhất 1 cụm điểm tham quan.');
        return;
    }
    
    // --- Bắt đầu quá trình tìm đường ---
    loadingOverlay.style.display = 'flex'; // Hiển thị màn hình chờ (loading)
    resultsSummaryDiv.innerHTML = '<p>Đang tìm lộ trình...</p>'; // Cập nhật trạng thái
    
    // Xóa kết quả (đường đi, marker) cũ trên bản đồ
    if (routeLayer) map.removeLayer(routeLayer);
    startEndMarkers.forEach(m => map.removeLayer(m));
    startEndMarkers = [];
    
    try {
        // Gọi API /solve_gtsp của BLL với phương thức POST
        const response = await fetch(`${BLL_API_URL}/solve_gtsp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // Gửi dữ liệu (đầu vào) dưới dạng JSON
            body: JSON.stringify({
                start_address: startAddress,
                end_address: endAddress,
                cluster_ids: selectedClusters,
                optimize_for: optimizeFor
            })
        });
        
        // Nhận kết quả JSON từ BLL
        const result = await response.json();
        // Nếu response không OK (lỗi 400, 500) thì ném lỗi
        if (!response.ok) throw new Error(result.error || 'Lỗi không xác định từ máy chủ Logic');
        
        console.log("Kết quả từ BLL:", result);
        // Gọi hàm để hiển thị kết quả lên giao diện
        displayResults(result);
        
    } catch (error) {
        // Xử lý nếu có lỗi (lỗi mạng, lỗi BLL)
        console.error(error);
        resultsSummaryDiv.innerHTML = `<p class="text-danger"><b>Lỗi:</b> ${error.message}</p>`;
    } finally {
        // Luôn luôn ẩn màn hình chờ sau khi xong (kể cả khi lỗi)
        loadingOverlay.style.display = 'none';
    }
});


// 5. HÀM HIỂN THỊ KẾT QUẢ LỘ TRÌNH LÊN GIAO DIỆN
function displayResults(result) {
    
    // --- Hiển thị tóm tắt ---
    // Định dạng chi phí (solver) dựa trên tiêu chí tối ưu
    const formattedSolverCost = result.optimize_for === 'distance'
        ? formatDistance(result.total_cost)
        : formatDuration(result.total_cost);

    // Tạo HTML cho phần tóm tắt kết quả
    resultsSummaryDiv.innerHTML = `
        <div class="alert alert-success p-2">
            <h5 class="alert-heading fs-6">Hoàn thành!</h5>
            <p class="mb-1"><b>Tối ưu theo:</b> ${result.optimize_for === 'distance' ? 'Quãng đường' : 'Thời gian'}</p>
            <p class="mb-0"><b>Chi phí tối ưu (Solver):</b> ${formattedSolverCost}</p>
        </div>
        <hr>
        <p><b>Tổng quãng đường (OSRM):</b> ${formatDistance(result.total_distance_km)}</p>
        <p><b>Tổng thời gian (OSRM):</b> ${formatDuration(result.total_duration_min)}</p>
        <h6 class="fw-bold mt-3">Chi tiết lộ trình:</h6>
    `;
    
    // --- Tạo danh sách các chặng (Bắt đầu sửa) ---
    const tourList = document.createElement('div'); // Dùng <div> thay vì <ol>
    tourList.className = 'list-group'; // Dùng list-group của Bootstrap
    
    // --- Vẽ đường đi lên bản đồ ---
    // Gom tất cả các đoạn geometry (từ BLL) thành một FeatureCollection (chuẩn GeoJSON)
    const allGeometries = {
        type: "FeatureCollection",
        features: result.geometries.map(geom => ({
            type: "Feature", geometry: geom, properties: {}
        }))
    };
    
    // Tạo lớp (layer) GeoJSON từ geometries và vẽ lên bản đồ
    routeLayer = L.geoJSON(allGeometries, {
        style: { color: '#0d6efd', weight: 5, opacity: 0.8 } // Màu xanh, dày 5px
    }).addTo(map);
    
    // Tự động zoom bản đồ để vừa với toàn bộ lộ trình
    map.fitBounds(routeLayer.getBounds().pad(0.1)); // Thêm 10% padding
    
    // --- Hiển thị các chặng và Marker ---
    
    // Chặng 0 (Xử lý riêng cho Điểm Bắt Đầu)
    const firstStopName = result.tour[0].from.replace("START_POINT", "Điểm xuất phát");
    // Lấy tọa độ điểm bắt đầu (là tọa độ ĐẦU TIÊN [0] của geometry ĐẦU TIÊN [0])
    // OSRM trả về [lon, lat]
    const firstStopCoord = result.geometries[0].coordinates[0]; // [lon, lat]
    
    // Thêm HTML cho điểm bắt đầu (chặng 1)
    tourList.innerHTML += `
        <div class="list-group-item list-group-item-success d-flex align-items-center">
            <span class="badge bg-dark rounded-pill me-2">1</span>
            <b>${firstStopName}</b>
        </div>
    `;
    // Tạo marker cho điểm bắt đầu (Leaflet yêu cầu [lat, lon])
    let startMarker = L.marker([firstStopCoord[1], firstStopCoord[0]]) // Chú ý: [1], [0]
        .bindPopup(`<b>1. Điểm xuất phát</b><br>${firstStopName}`)
        .addTo(map);
    startEndMarkers.push(startMarker);

    
    // Duyệt qua từng chặng (leg) trong lộ trình (result.tour) để hiển thị
    // (Bao gồm các chặng giữa và điểm kết thúc)
    result.tour.forEach((leg, index) => {
        let stopName = leg.to;
        let cssClass = "";
        let isEnd = false;
        
        // Xử lý riêng (tô màu đỏ) nếu là Điểm Kết Thúc
        if (stopName.includes("END_POINT")) {
            stopName = leg.to.replace("END_POINT", "Điểm kết thúc");
            cssClass = "list-group-item-danger"; // Màu đỏ
            isEnd = true;
        }

        const legDistance = formatDistance(leg.distance_km);
        const legDuration = formatDuration(leg.duration_min);
        // Tạo ID duy nhất cho nút 'Chi tiết' (collapse) của Bootstrap
        const collapseId = `collapse-step-${index}`;

        // Xây dựng HTML cho danh sách các bước chỉ đường chi tiết
        let stepsHtml = '<ul class="list-unstyled mt-2">';
        leg.steps.forEach(step => {
            // Gọi hàm dịch getManeuverText
            stepsHtml += `<li class="step-instruction">${getManeuverText(step)}</li>`;
        });
        stepsHtml += '</ul>';

        // Tạo HTML cho chặng này (bao gồm nút 'Chi tiết' và nội dung 'collapse')
        tourList.innerHTML += `
            <div class="list-group-item ${cssClass}">
                <div class="d-flex w-100 justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <span class="badge bg-dark rounded-pill me-2">${index + 2}</span>
                        <b>${stopName}</b>
                    </h6>
                    <button class="btn btn-sm btn-outline-primary" type="button" 
                            data-bs-toggle="collapse" 
                            data-bs-target="#${collapseId}" 
                            aria-expanded="false" 
                            aria-controls="${collapseId}">
                        Chi tiết
                    </button>
                </div>
                <small class="text-muted d-block mt-1">
                    Chặng ${index + 1}: ${legDistance} / ${legDuration}
                </small>
                
                <div class="collapse mt-2" id="${collapseId}">
                    <div class="card card-body p-2">
                        ${stepsHtml}
                    </div>
                </div>
            </div>
        `;
        
        // Thêm marker cho điểm dừng này
        // Tọa độ của điểm dừng này là tọa độ CUỐI CÙNG (.slice(-1)[0]) của geometry HIỆN TẠI (index)
        const stopCoord = result.geometries[index].coordinates.slice(-1)[0]; // [lon, lat]
        let marker = L.marker([stopCoord[1], stopCoord[0]]) // Chuyển sang [lat, lon]
            .bindPopup(`<b>${index + 2}. ${stopName}</b>`)
            .addTo(map);
        startEndMarkers.push(marker);
    });
    
    // Gắn danh sách chặng đã tạo vào trang
    resultsSummaryDiv.appendChild(tourList);
}

// 6. CHẠY HÀM KHỞI TẠO KHI TRANG TẢI XONG
// Sự kiện khi DOM (HTML) đã tải xong
document.addEventListener('DOMContentLoaded', () => {
    // Gọi hàm tải danh sách cụm ban đầu để hiển thị cho người dùng
    loadClusters();
});