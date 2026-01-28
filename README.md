## Tool tính khoảng cách chim bay + đường bộ và vẽ bản đồ

Tool này giúp:
- **Bước 1**: Từ `DIA_DIEM_CAN_DO.xlsx` và `data.xlsx` tính **khoảng cách chim bay (Haversine)**, lấy **top N** điểm gần nhất → xuất `top20_chim_bay.xlsx`.
- **Bước 2**: Dùng **Selenium + Google Maps** đo **khoảng cách đường bộ + thời gian lái xe** cho từng cặp trong top N → xuất `ket_qua_top20_duong_bo.xlsx`.
- **Bước 3 (tuỳ chọn)**: Vẽ **bản đồ HTML**: điểm cần đo + 20 điểm gần, có đường nối, tooltip hiển thị khoảng cách chim bay/đường bộ → file `map_top20.html`.

---

## 1. Chuẩn bị dữ liệu đầu vào

Thư mục `data/` gồm:
- `DIA_DIEM_CAN_DO.xlsx`  
  - Cột bắt buộc: **`KINH ĐỘ`**, **`VĨ ĐỘ`** (có dấu tiếng Việt, dạng số hoặc chuỗi có dấu phẩy/chấm).
- `data.xlsx`  
  - Mỗi dòng là **cặp điểm**:
    - `Mã phòng ban 1`, `Tên phòng ban 1`, `KINH ĐỘ 1`, `VĨ ĐỘ 1`  
    - `Mã phòng ban 2`, `Tên phòng ban 2`, `KINH ĐỘ 2`, `VĨ ĐỘ 2`  
    - Có thể có thêm cột tỉnh/thành (tool tự nhận).

**Lần sau chạy:**  
Bạn **chỉ cần thay nội dung** 2 file:
- `data/DIA_DIEM_CAN_DO.xlsx`
- `data/data.xlsx`  
Giữ nguyên tên cũ và cấu trúc cột như hiện tại → chạy lại lệnh là ra kết quả mới, **không cần sửa code**.

---

## 2. Cài đặt môi trường

Trong thư mục dự án:

```bash
cd "/media/trungdt2/New Volume/Work/tool_tinh_kc_dia_diem_moi"
python -m pip install -r requirements.txt
```

Yêu cầu:
- Python 3.9+ (khuyến nghị).
- Chrome + ChromeDriver (cùng version).  
  - Nếu có internet, Selenium Manager thường tự xử lý.  
  - Nếu không, tải `chromedriver` về và dùng tham số `--driver_path`.

---

## 3. Chạy tool tính khoảng cách

Lệnh tổng quát:

```bash
cd "/media/trungdt2/New Volume/Work/tool_tinh_kc_dia_diem_moi"
python tool.py \
  --need data/DIA_DIEM_CAN_DO.xlsx \
  --data data/data.xlsx \
  --top_n 20 \
  --headless 1 \
  --driver_path "/duong/dan/toi/chromedriver"  # tuỳ chọn
```

### Tham số
- **`--need`**: đường dẫn tới `DIA_DIEM_CAN_DO.xlsx`.
- **`--data`**: đường dẫn tới `data.xlsx`.
- **`--top_n`**: số điểm gần nhất theo chim bay cần giữ lại (mặc định 20).
- **`--headless`**:
  - `1`: chạy Chrome **ẩn** (khuyến nghị khi chạy nhiều).
  - `0`: mở Chrome để **debug xem Google Maps**.
- **`--driver_path`** (tuỳ chọn):  
  - Nếu môi trường **không có internet** hoặc Selenium Manager không tự tải được ChromeDriver, bạn truyền trực tiếp đường dẫn đến file `chromedriver`.

### Kết quả sau khi chạy

Tool tạo 2 file:
- `top20_chim_bay.xlsx`  
  - Danh sách top N điểm gần nhất theo **khoảng cách chim bay**.
- `ket_qua_top20_duong_bo.xlsx`  
  - Cột chính:
    - `diem_can_do_id`, `origin_lat`, `origin_lng`
    - `ma_phong_ban`, `ten_phong_ban`, `lat`, `lng`, `tinh_thanh`
    - `khoang_cach_chim_bay_km`, `rank_chim_bay`
    - `khoang_cach_duong_bo_km`, `thoi_gian_phut`, `rank_duong_bo`
    - `status` (OK/FAILED), `error_message` (nếu lỗi).

---

## 4. Chạy riêng bước vẽ bản đồ

Sau khi đã có `ket_qua_top20_duong_bo.xlsx`, bạn có thể vẽ bản đồ:

```bash
cd "/media/trungdt2/New Volume/Work/tool_tinh_kc_dia_diem_moi"
python map_viz.py \
  --input ket_qua_top20_duong_bo.xlsx \
  --output map_top20.html
```

Kết quả:
- File `map_top20.html` (mở bằng Chrome/Edge/Firefox):
  - Marker **đỏ**: điểm cần đo.
  - Marker **xanh**: các điểm top N.
  - Đường nối từ điểm cần đo đến từng điểm top N.
  - Tooltip đường: dạng `ĐB: X km; CB: Y km; rank CB: Z`.

---

## 5. Cách dùng cho các lần sau

Cho mỗi lần chạy mới, quy trình cực ngắn:
1. **Thay dữ liệu**:
   - Ghi đè file `data/DIA_DIEM_CAN_DO.xlsx` bằng file mới (giữ đúng tên cột KINH ĐỘ / VĨ ĐỘ).
   - Ghi đè file `data/data.xlsx` bằng file mới (giữ đúng cấu trúc cột đã dùng).
2. **Chạy lệnh**:
   - Tính lại khoảng cách + đo Google Maps:
     ```bash
     python tool.py --need data/DIA_DIEM_CAN_DO.xlsx --data data/data.xlsx --top_n 20 --headless 1
     ```
   - (Tuỳ chọn) Vẽ lại bản đồ:
     ```bash
     python map_viz.py --input ket_qua_top20_duong_bo.xlsx --output map_top20.html
     ```

**Không cần chỉnh sửa code** nếu cấu trúc cột đầu vào vẫn giữ như hiện tại.

---

## 6. Một số lưu ý & lỗi thường gặp

- **Bị Google chặn / chậm**:
  - Tool đã có `throttle` (delay ~1.2s mỗi request) và retry tối đa 3 lần.
  - Nếu vẫn bị, có thể tăng `throttle_sec` trực tiếp trong `maps_selenium.py` hoặc tạm thời giảm `top_n`.

- **Lỗi không tìm thấy ChromeDriver**:
  - Kiểm tra Chrome đã cài chưa.
  - Tải ChromeDriver đúng phiên bản Chrome, truyền `--driver_path`.

- **Lỗi cột không hợp lệ**:
  - Kiểm tra lại 2 file Excel có đúng tên cột yêu cầu (nhất là tiếng Việt có dấu) và không bị đổi tên sheet/cột.


