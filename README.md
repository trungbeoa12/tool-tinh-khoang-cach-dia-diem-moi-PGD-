## Chay Project

Nguoi dung tai file Excel du lieu len giao dien. File khong can nam trong
project; ket qua gom hai file Excel va mot ban do HTML duoc tai ve dang ZIP.

### Cai thu vien

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

### Chay giao dien

```bash
./.venv/bin/streamlit run streamlit_app.py
```

### Chay CLI

```bash
./.venv/bin/python tool.py --coord "10.969499056814524,106.67685107587728" --data /path/to/data.xlsx --output_dir /path/to/results --output_name ket_qua_thang_09_2026 --top_n 20 --headless 1
```

Co the dung file Excel diem can do ben ngoai project qua `--need <path>` hoac
nhap truc tiep sau khi chay lenh voi `--prompt_coord 1`. File nay khong la data
dia diem cua ung dung va khong duoc dong goi trong project.

Tren giao dien, chon file `.xlsx`, nhap ten ket qua va bam nut tai file ZIP sau
khi xu ly hoan tat.
