"""Vẽ bản đồ top20: điểm cần đo + 20 điểm gần, có đường chim bay/đường bộ."""

from __future__ import annotations

import argparse
import math
from typing import Optional

import folium
import pandas as pd


def make_map(df: pd.DataFrame, output: str, tile: str = "OpenStreetMap") -> None:
    if df.empty:
        raise ValueError("Dữ liệu rỗng, không thể vẽ bản đồ.")

    # Trung tâm bản đồ: trung bình tất cả lat/lng
    center_lat = df["origin_lat"].mean()
    center_lng = df["origin_lng"].mean()
    fmap = folium.Map(location=[center_lat, center_lng], zoom_start=8, tiles=tile, control_scale=True)

    for origin_id, group in df.groupby("diem_can_do_id"):
        layer = folium.FeatureGroup(name=f"Điểm cần đo {origin_id}")
        origin_lat = group.iloc[0]["origin_lat"]
        origin_lng = group.iloc[0]["origin_lng"]
        folium.Marker(
            [origin_lat, origin_lng],
            popup=f"Điểm cần đo {origin_id}",
            tooltip=f"Điểm cần đo {origin_id}",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(layer)

        for _, row in group.iterrows():
            dest_lat = row["lat"]
            dest_lng = row["lng"]
            air = row.get("khoang_cach_chim_bay_km")
            drive = row.get("khoang_cach_duong_bo_km")
            line_text = f"ĐB: {drive:.2f} km; CB: {air:.2f} km; rank CB: {row.get('rank_chim_bay')}"
            folium.Marker(
                [dest_lat, dest_lng],
                popup=f"{row.get('ma_phong_ban')} - {row.get('ten_phong_ban')}",
                tooltip=line_text,
                icon=folium.Icon(color="blue", icon="cloud"),
            ).add_to(layer)

            folium.PolyLine(
                [[origin_lat, origin_lng], [dest_lat, dest_lng]],
                color="green",
                weight=3,
                opacity=0.7,
                tooltip=line_text,
            ).add_to(layer)
        layer.add_to(fmap)

    folium.LayerControl().add_to(fmap)
    fmap.save(output)


def parse_args():
    parser = argparse.ArgumentParser(description="Vẽ bản đồ kết quả top20 (chim bay + đường bộ).")
    parser.add_argument("--input", required=True, help="File ket_qua_top20_duong_bo.xlsx")
    parser.add_argument("--output", default="map_top20.html", help="File HTML đầu ra")
    return parser.parse_args()


def main():
    args = parse_args()
    df = pd.read_excel(args.input)
    needed_cols = [
        "diem_can_do_id",
        "origin_lat",
        "origin_lng",
        "lat",
        "lng",
        "khoang_cach_chim_bay_km",
        "khoang_cach_duong_bo_km",
        "rank_chim_bay",
        "ma_phong_ban",
        "ten_phong_ban",
    ]
    missing = [c for c in needed_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Thiếu cột trong input: {missing}")
    make_map(df, output=args.output)
    print(f"Đã ghi bản đồ: {args.output}")


if __name__ == "__main__":
    main()

