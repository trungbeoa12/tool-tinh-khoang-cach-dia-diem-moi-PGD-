"""Simple local UI for running the distance tool from a browser."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from map_viz import make_map
from preprocess import NeedPoint
from tool import run_pipeline


DEFAULT_DATA_PATH = "data/data.xlsx"


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a dataframe to an Excel file in memory."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer.getvalue()


st.set_page_config(page_title="Tinh khoang cach", page_icon="📍", layout="wide")
st.title("Tinh khoang cach diem giao dich")
st.caption("Nhap toa do, bam chay, xem ket qua va tai file Excel.")

with st.sidebar:
    st.header("Cau hinh")
    data_path = st.text_input("Duong dan data.xlsx", value=DEFAULT_DATA_PATH)
    top_n = st.number_input("So diem gan nhat", min_value=1, max_value=100, value=20, step=1)
    headless = st.checkbox("Chay Chrome an", value=True)
    driver_path_raw = st.text_input("ChromeDriver path (neu can)", value="")
    driver_path = driver_path_raw.strip() or None

coord_text = st.text_input("Toa do", value="", placeholder="10.969499056814524,106.67685107587728")
run_clicked = st.button("Chay tinh khoang cach", type="primary", use_container_width=True)

if run_clicked:
    coord_text = coord_text.strip()
    if not coord_text:
        st.error("Can nhap toa do theo dang lat,lng.")
    elif not Path(data_path).exists():
        st.error(f"Khong tim thay file du lieu: {data_path}")
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
                with st.spinner("Dang tinh khoang cach chim bay va duong bo..."):
                    try:
                        top_air_df, result_df, output_dir = run_pipeline(
                            needs=[need],
                            data_path=data_path,
                            top_n=int(top_n),
                            headless=headless,
                            driver_path=driver_path,
                        )
                        map_output_path = output_dir / "map_top20.html"
                        make_map(result_df, output=str(map_output_path))
                    except Exception as exc:  # pylint: disable=broad-except
                        st.exception(exc)
                    else:
                        st.success("Da chay xong.")
                        st.caption(f"Thu muc output: {output_dir}")

                        col1, col2 = st.columns(2)
                        col1.metric("So dong top chim bay", len(top_air_df))
                        col2.metric("So dong ket qua duong bo", len(result_df))

                        st.subheader("Ket qua")
                        st.dataframe(result_df, use_container_width=True)

                        excel_bytes = dataframe_to_excel_bytes(result_df)
                        top_air_bytes = dataframe_to_excel_bytes(top_air_df)

                        download_col1, download_col2 = st.columns(2)
                        download_col1.download_button(
                            "Tai ket_qua_top20_duong_bo.xlsx",
                            data=excel_bytes,
                            file_name="ket_qua_top20_duong_bo.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                        download_col2.download_button(
                            "Tai top20_chim_bay.xlsx",
                            data=top_air_bytes,
                            file_name="top20_chim_bay.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )

                        if map_output_path.exists():
                            with open(map_output_path, "r", encoding="utf-8") as map_file:
                                st.subheader("Ban do")
                                st.components.v1.html(map_file.read(), height=600, scrolling=True)
