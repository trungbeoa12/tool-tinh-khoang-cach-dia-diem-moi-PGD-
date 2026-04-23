## Chay Project

### File input can co

Trong thu muc `data/`:

- `DIA_DIEM_CAN_DO.xlsx`
  - cot bat buoc: `KINH ĐỘ`, `VĨ ĐỘ`
- `data.xlsx`
  - cot bat buoc:
    - `Mã phòng ban 1`
    - `Tên phòng ban 1`
    - `KINH ĐỘ 1`
    - `VĨ ĐỘ 1`
    - `Mã phòng ban 2`
    - `Tên phòng ban 2`
    - `KINH ĐỘ 2`
    - `VĨ ĐỘ 2`

### Cai thu vien

```bash
cd "/Users/pro201715inch/Documents/tool_tinh_kc_diem_gd_moi"
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

### Chay tool tinh khoang cach

```bash
cd "/Users/pro201715inch/Documents/tool_tinh_kc_diem_gd_moi"
./.venv/bin/python tool.py --need data/DIA_DIEM_CAN_DO.xlsx --data data/data.xlsx --top_n 20 --headless 1
```

### Chay nhanh bang 1 toa do tu terminal

```bash
cd "/Users/pro201715inch/Documents/tool_tinh_kc_diem_gd_moi"
./.venv/bin/python tool.py --coord "10.969499056814524,106.67685107587728" --data data/data.xlsx --top_n 20 --headless 1
```

Khong can sua `data/DIA_DIEM_CAN_DO.xlsx` neu dung `--coord`.

### Chay lenh truoc roi nhap toa do sau tren terminal

```bash
cd "/Users/pro201715inch/Documents/tool_tinh_kc_diem_gd_moi"
./.venv/bin/python tool.py --prompt_coord 1 --data data/data.xlsx --top_n 20 --headless 1
```

Sau khi chay lenh, terminal se hien:

```text
Nhập tọa độ dạng lat,lng:
```

Vi du nhap:

```text
10.969499056814524,106.67685107587728
```

### Ve ban do HTML

```bash
cd "/Users/pro201715inch/Documents/tool_tinh_kc_diem_gd_moi"
./.venv/bin/python map_viz.py --input output/<timestamp>/ket_qua_top20_duong_bo.xlsx --output output/<timestamp>/map_top20.html
```

### Chay giao dien don gian

```bash
cd "/Users/pro201715inch/Documents/tool_tinh_kc_diem_gd_moi"
./.venv/bin/streamlit run streamlit_app.py
```

Giao dien cho phep:

- nhap 1 toa do `lat,lng`
- chon `top_n`
- bam nut chay
- xem bang ket qua
- tai file Excel
- xem ban do ngay tren trinh duyet
- moi lan chay se tao them 1 thu muc moi trong `output/`

### Chay 1 lenh tu dau den cuoi

```bash
cd "/Users/pro201715inch/Documents/tool_tinh_kc_diem_gd_moi"
./.venv/bin/python tool.py --need data/DIA_DIEM_CAN_DO.xlsx --data data/data.xlsx --top_n 20 --headless 1
./.venv/bin/python map_viz.py --input output/<timestamp>/ket_qua_top20_duong_bo.xlsx --output output/<timestamp>/map_top20.html
```

Hoac dung toa do nhap truc tiep:

```bash
cd "/Users/pro201715inch/Documents/tool_tinh_kc_diem_gd_moi"
./.venv/bin/python tool.py --coord "10.969499056814524,106.67685107587728" --data data/data.xlsx --top_n 20 --headless 1
./.venv/bin/python map_viz.py --input output/<timestamp>/ket_qua_top20_duong_bo.xlsx --output output/<timestamp>/map_top20.html
```

Hoac nhap toa do sau khi lenh da chay:

```bash
cd "/Users/pro201715inch/Documents/tool_tinh_kc_diem_gd_moi"
./.venv/bin/python tool.py --prompt_coord 1 --data data/data.xlsx --top_n 20 --headless 1
./.venv/bin/python map_viz.py --input output/<timestamp>/ket_qua_top20_duong_bo.xlsx --output output/<timestamp>/map_top20.html
```

### File output

- `output/<timestamp>/top20_chim_bay.xlsx`
- `output/<timestamp>/ket_qua_top20_duong_bo.xlsx`
- `output/<timestamp>/map_top20.html`
