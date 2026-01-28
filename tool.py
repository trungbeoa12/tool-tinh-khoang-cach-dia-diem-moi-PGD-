"""CLI tool to compute air distances and driving distances between points."""

from __future__ import annotations

import argparse
import sys
import time
from typing import Optional

import numpy as np
import pandas as pd

from haversine import haversine_vectorized
from maps_selenium import create_driver, get_route_distance_time
from preprocess import NeedPoint, build_coordinate_set, load_need_points


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
        print(f"[AIR] origin {idx}/{len(needs)} done")
    return pd.DataFrame(results)


def enrich_with_driving(top_df: pd.DataFrame, headless: bool, driver_path: Optional[str], throttle_sec: float = 1.2) -> pd.DataFrame:
    """Call Google Maps via Selenium to add driving distance/time."""
    driver = create_driver(headless=headless, driver_path=driver_path)
    enriched_rows = []
    try:
        for i, row in top_df.iterrows():
            print(
                f"[GMAPS] origin {row['diem_can_do_id']} measure {row['rank_chim_bay']}/{top_df[top_df['diem_can_do_id']==row['diem_can_do_id']].shape[0]}..."
            )
            distance_km, duration_min, status, err = get_route_distance_time(
                origin_lat=row["origin_lat"],
                origin_lng=row["origin_lng"],
                dest_lat=row["lat"],
                dest_lng=row["lng"],
                driver=driver,
                throttle_sec=throttle_sec,
            )
            row = row.copy()
            row["khoang_cach_duong_bo_km"] = distance_km
            row["thoi_gian_phut"] = duration_min
            row["status"] = status
            row["error_message"] = err
            enriched_rows.append(row)
    finally:
        driver.quit()

    enriched_df = pd.DataFrame(enriched_rows)
    # Rank within each origin by driving distance then time
    def _rank_group(group: pd.DataFrame) -> pd.DataFrame:
        sorted_group = group.sort_values(
            by=["khoang_cach_duong_bo_km", "thoi_gian_phut"], na_position="last"
        ).reset_index(drop=True)
        sorted_group["rank_duong_bo"] = np.arange(1, len(sorted_group) + 1)
        return sorted_group

    ranked = enriched_df.groupby("diem_can_do_id", group_keys=False).apply(_rank_group)
    return ranked


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Tính khoảng cách chim bay + đường bộ (Google Maps).")
    parser.add_argument("--need", required=True, help="Path DIA_DIEM_CAN_DO.xlsx")
    parser.add_argument("--data", required=True, help="Path data.xlsx")
    parser.add_argument("--top_n", type=int, default=20, help="Số điểm gần nhất theo chim bay")
    parser.add_argument("--headless", type=int, default=1, help="1=headless (default), 0=hiển thị Chrome")
    parser.add_argument("--driver_path", type=str, default=None, help="Đường dẫn ChromeDriver (tùy chọn)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    headless = bool(args.headless)

    print("Đọc dữ liệu...")
    needs = load_need_points(args.need)
    coord_df = build_coordinate_set(args.data)
    if coord_df.empty:
        raise SystemExit("Coordinate set trống sau khi xử lý data.xlsx")

    print("Tính khoảng cách chim bay và xuất top20_chim_bay.xlsx ...")
    top_air_df = compute_topn_air(needs, coord_df, args.top_n)
    top_air_path = "top20_chim_bay.xlsx"
    top_air_df.to_excel(top_air_path, index=False)
    print(f"Đã ghi {top_air_path}")

    print("Đo khoảng cách đường bộ qua Google Maps (Selenium)...")
    result_df = enrich_with_driving(top_air_df, headless=headless, driver_path=args.driver_path)
    result_df = result_df[
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

    output_path = "ket_qua_top20_duong_bo.xlsx"
    result_df.to_excel(output_path, index=False)
    print(f"Hoàn tất. Kết quả: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

