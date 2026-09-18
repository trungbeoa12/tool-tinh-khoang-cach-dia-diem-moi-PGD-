"""CLI tool to compute air distances and driving distances between points."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Optional

import numpy as np
import pandas as pd

from haversine import haversine_vectorized
from maps_selenium import create_driver, get_route_distance_time
from preprocess import NeedPoint, build_coordinate_set, load_need_points


def parse_inline_coordinate(raw: str) -> NeedPoint:
    """Parse a single coordinate from CLI in the form 'lat,lng'."""
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 2:
        raise ValueError("Tọa độ phải có dạng 'lat,lng'")
    try:
        lat = float(parts[0])
        lng = float(parts[1])
    except ValueError as exc:
        raise ValueError("Không đọc được tọa độ từ --coord") from exc
    return NeedPoint(id=0, lat=lat, lng=lng)


def prompt_for_coordinate() -> NeedPoint:
    """Prompt for a single coordinate interactively in the terminal."""
    raw = input("Nhập tọa độ dạng lat,lng: ").strip()
    if not raw:
        raise ValueError("Bạn chưa nhập tọa độ")
    return parse_inline_coordinate(raw)


def compute_topn_air(needs: list[NeedPoint], coord_df: pd.DataFrame, top_n: int) -> pd.DataFrame:
    """Compute haversine distances and keep top_n nearest for each need point."""
    dest_lats = coord_df["lat"].to_numpy(dtype=float)
    dest_lngs = coord_df["lng"].to_numpy(dtype=float)
    results = []
    for idx, need in enumerate(needs, start=1):
        distances = haversine_vectorized(need.lat, need.lng, dest_lats, dest_lngs)
        order = np.argsort(distances)[:top_n]
        for rank, dest_idx in enumerate(order, start=1):
            dest_row = coord_df.iloc[dest_idx]
            results.append(
                {
                    "diem_can_do_id": need.id,
                    "origin_lat": need.lat,
                    "origin_lng": need.lng,
                    "ma_phong_ban": dest_row["ma_phong_ban"],
                    "ten_phong_ban": dest_row.get("ten_phong_ban"),
                    "lat": dest_row["lat"],
                    "lng": dest_row["lng"],
                    "tinh_thanh": dest_row.get("tinh_thanh"),
                    "khoang_cach_chim_bay_km": float(distances[dest_idx]),
                    "rank_chim_bay": rank,
                }
            )
        print(f"[AIR] origin {idx}/{len(needs)} done", flush=True)
    return pd.DataFrame(results)


def enrich_with_driving(top_df: pd.DataFrame, headless: bool, driver_path: Optional[str], throttle_sec: float = 1.2) -> pd.DataFrame:
    """Call Google Maps via Selenium to add driving distance/time."""
    driver = create_driver(headless=headless, driver_path=driver_path)
    enriched_rows = []
    try:
        total_by_origin = top_df.groupby("diem_can_do_id").size().to_dict()
        for _, row in top_df.iterrows():
            print(
                f"[GMAPS] origin {row['diem_can_do_id']} measure {row['rank_chim_bay']}/{total_by_origin[row['diem_can_do_id']]}...",
                flush=True,
            )
            distance_km, duration_min, status, err, session_broken = get_route_distance_time(
                origin_lat=row["origin_lat"],
                origin_lng=row["origin_lng"],
                dest_lat=row["lat"],
                dest_lng=row["lng"],
                driver=driver,
                throttle_sec=throttle_sec,
            )
            if session_broken:
                print("[GMAPS] session died, recreating Chrome driver...", flush=True)
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = create_driver(headless=headless, driver_path=driver_path)
            row = row.copy()
            row["khoang_cach_duong_bo_km"] = distance_km
            row["thoi_gian_phut"] = duration_min
            row["status"] = status
            row["error_message"] = err
            enriched_rows.append(row)
    finally:
        driver.quit()

    enriched_df = pd.DataFrame(enriched_rows)
    ranked = enriched_df.sort_values(
        by=["diem_can_do_id", "khoang_cach_duong_bo_km", "thoi_gian_phut"],
        na_position="last",
    ).reset_index(drop=True)
    ranked["rank_duong_bo"] = ranked.groupby("diem_can_do_id").cumcount() + 1
    return ranked


def finalize_result_columns(result_df: pd.DataFrame) -> pd.DataFrame:
    """Keep output columns in a stable order for exports and UI."""
    return result_df[
        [
            "diem_can_do_id",
            "origin_lat",
            "origin_lng",
            "ma_phong_ban",
            "ten_phong_ban",
            "lat",
            "lng",
            "tinh_thanh",
            "khoang_cach_chim_bay_km",
            "rank_chim_bay",
            "khoang_cach_duong_bo_km",
            "thoi_gian_phut",
            "rank_duong_bo",
            "status",
            "error_message",
        ]
    ]


def validate_data_file(data_path: str | Path) -> Path:
    """Validate a user-selected Excel input file before processing."""
    input_file = Path(data_path).expanduser()
    if not input_file.is_file():
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {input_file}")
    if input_file.suffix.lower() not in {".xlsx", ".xls"}:
        raise ValueError("File dữ liệu phải có định dạng .xlsx hoặc .xls")
    return input_file


def create_output_dir(base_dir: str | Path, output_name: str) -> Path:
    """Create a uniquely named result directory inside a user-selected folder."""
    output_base_dir = Path(base_dir).expanduser()
    if not output_base_dir.is_dir():
        raise NotADirectoryError(f"Thư mục lưu kết quả không tồn tại: {output_base_dir}")
    if not os.access(output_base_dir, os.W_OK):
        raise PermissionError(f"Không có quyền ghi vào thư mục: {output_base_dir}")

    directory_name = output_name.strip()
    if directory_name.lower().endswith(".xlsx"):
        directory_name = Path(directory_name).stem
    if not directory_name:
        raise ValueError("Vui lòng nhập tên kết quả")
    if Path(directory_name).name != directory_name or directory_name in {".", ".."}:
        raise ValueError("Tên kết quả không được chứa đường dẫn")

    candidate = output_base_dir / directory_name
    suffix = 1
    while candidate.exists():
        candidate = output_base_dir / f"{directory_name}_{suffix}"
        suffix += 1
    candidate.mkdir()
    return candidate


def run_pipeline(
    needs: list[NeedPoint],
    data_path: str | Path,
    top_n: int = 20,
    headless: bool = True,
    driver_path: Optional[str] = None,
    output_base_dir: str | Path = ".",
    output_name: str = "ket_qua",
) -> tuple[pd.DataFrame, pd.DataFrame, Path]:
    """Run the full distance pipeline and optionally export Excel outputs."""
    input_file = validate_data_file(data_path)
    coord_df = build_coordinate_set(input_file)
    if coord_df.empty:
        raise ValueError("Coordinate set trống sau khi xử lý file dữ liệu")

    output_dir = create_output_dir(output_base_dir, output_name)
    top_air_path = output_dir / "top20_chim_bay.xlsx"
    output_path = output_dir / "ket_qua_top20_duong_bo.xlsx"
    top_air_df = compute_topn_air(needs, coord_df, top_n)
    top_air_df.to_excel(top_air_path, index=False)
    print(f"Đã ghi {top_air_path}", flush=True)

    result_df = enrich_with_driving(top_air_df, headless=headless, driver_path=driver_path)
    result_df = finalize_result_columns(result_df)
    result_df.to_excel(output_path, index=False)
    print(f"Hoàn tất. Kết quả: {output_path}", flush=True)

    return top_air_df, result_df, output_dir


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Tính khoảng cách chim bay + đường bộ (Google Maps).")
    parser.add_argument("--need", help="Path to an external Excel file of points to measure")
    parser.add_argument("--data", required=True, help="Path to the Excel location data")
    parser.add_argument("--output_dir", required=True, help="Directory in which to save result files")
    parser.add_argument("--output_name", required=True, help="Name of the result directory")
    parser.add_argument("--coord", help="Tọa độ chạy nhanh dạng 'lat,lng', ví dụ '10.9694,106.6768'")
    parser.add_argument("--prompt_coord", type=int, default=0, help="1 để nhập tọa độ trực tiếp trên terminal")
    parser.add_argument("--top_n", type=int, default=20, help="Số điểm gần nhất theo chim bay")
    parser.add_argument("--headless", type=int, default=1, help="1=headless (default), 0=hiển thị Chrome")
    parser.add_argument("--driver_path", type=str, default=None, help="Đường dẫn ChromeDriver (tùy chọn)")
    args = parser.parse_args(argv)
    if not args.need and not args.coord and not bool(args.prompt_coord):
        parser.error("Cần truyền một trong ba: --need hoặc --coord hoặc --prompt_coord 1")
    return args


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    headless = bool(args.headless)
    data_file = validate_data_file(args.data)

    print(f"Đọc dữ liệu từ {data_file}...", flush=True)
    if args.coord:
        needs = [parse_inline_coordinate(args.coord)]
    elif args.prompt_coord:
        needs = [prompt_for_coordinate()]
    else:
        needs = load_need_points(args.need)

    print("Tính khoảng cách chim bay và xuất top20_chim_bay.xlsx ...", flush=True)
    print("Đo khoảng cách đường bộ qua Google Maps (Selenium)...", flush=True)
    run_pipeline(
        needs=needs,
        data_path=data_file,
        top_n=args.top_n,
        headless=headless,
        driver_path=args.driver_path,
        output_base_dir=args.output_dir,
        output_name=args.output_name,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
