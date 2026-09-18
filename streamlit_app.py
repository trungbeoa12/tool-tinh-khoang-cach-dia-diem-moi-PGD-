"""Simple local UI for running the distance tool from a browser."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

import streamlit as st

from map_viz import make_map
from preprocess import NeedPoint, build_coordinate_set
from tool import run_pipeline


def build_result_zip(output_dir: Path) -> bytes:
    """Package the pipeline's Excel and map artifacts for browser download."""
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for artifact in output_dir.iterdir():
            if artifact.is_file():
                archive.write(artifact, arcname=artifact.name)
    return buffer.getvalue()


def result_archive_name(output_name: str) -> str:
    """Build the browser download name for the result archive."""
    result_name = output_name.strip()
    if result_name.lower().endswith((".xlsx", ".zip")):
        result_name = Path(result_name).stem
    return f"{result_name}.zip"


st.set_page_config(page_title="Tinh khoang cach", page_icon="📍", layout="wide")
st.title("Tinh khoang cach diem giao dich")
st.caption("Tai file Excel, nhap toa do va tai ket qua sau khi xu ly.")

uploaded_file = st.file_uploader("Chọn file dữ liệu Excel", type=["xlsx"])
if uploaded_file:
    st.caption(f"File dữ liệu: {uploaded_file.name}")
output_name = st.text_input("Tên kết quả", value="")
top_n = st.number_input("So diem gan nhat", min_value=1, max_value=100, value=20, step=1)
headless = st.checkbox("Chay Chrome an", value=True)
driver_path_raw = st.text_input("ChromeDriver path (neu can)", value="")
driver_path = driver_path_raw.strip() or None

coord_text = st.text_input("Toa do", value="", placeholder="10.969499056814524,106.67685107587728")
run_clicked = st.button("Chay tinh khoang cach", type="primary", use_container_width=True)

if run_clicked:
    coord_text = coord_text.strip()
    if not uploaded_file:
        st.error("Vui lòng chọn file dữ liệu Excel trước khi chạy.")
    elif not output_name.strip():
        st.error("Vui lòng nhập tên kết quả.")
    elif not coord_text:
        st.error("Can nhap toa do theo dang lat,lng.")
    else:
        parts = [part.strip() for part in coord_text.split(",")]
        if len(parts) != 2:
            st.error("Toa do phai co dang lat,lng.")
        else:
            try:
                lat = float(parts[0])
                lng = float(parts[1])
            except ValueError:
                st.error("Khong doc duoc gia tri lat/lng.")
            else:
                need = NeedPoint(id=0, lat=lat, lng=lng)
                with TemporaryDirectory(prefix="distance-tool-") as temporary_dir:
                    temporary_path = Path(temporary_dir)
                    input_path = temporary_path / "input.xlsx"
                    input_path.write_bytes(uploaded_file.getvalue())
                    try:
                        build_coordinate_set(input_path)
                    except Exception as exc:  # pylint: disable=broad-except
                        st.error(f"Không thể đọc file dữ liệu đã chọn: {exc}")
                    else:
                        with st.spinner("Dang tinh khoang cach chim bay va duong bo..."):
                            try:
                                top_air_df, result_df, output_dir = run_pipeline(
                                    needs=[need],
                                    data_path=input_path,
                                    top_n=int(top_n),
                                    headless=headless,
                                    driver_path=driver_path,
                                    output_base_dir=temporary_path,
                                    output_name=output_name,
                                )
                                map_output_path = output_dir / "map_top20.html"
                                make_map(result_df, output=str(map_output_path))
                                result_zip = build_result_zip(output_dir)
                                map_html = map_output_path.read_text(encoding="utf-8")
                            except Exception as exc:  # pylint: disable=broad-except
                                st.error(f"Xử lý không thành công: {exc}")
                            else:
                                st.success("Hoàn thành.")
                                col1, col2 = st.columns(2)
                                col1.metric("So dong top chim bay", len(top_air_df))
                                col2.metric("So dong ket qua duong bo", len(result_df))
                                st.download_button(
                                    "Tải file kết quả",
                                    data=result_zip,
                                    file_name=result_archive_name(output_name),
                                    mime="application/zip",
                                    use_container_width=True,
                                )
                                st.subheader("Ket qua")
                                st.dataframe(result_df, use_container_width=True)
                                st.subheader("Ban do")
                                st.components.v1.html(map_html, height=600, scrolling=True)
