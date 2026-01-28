"""Preprocessing helpers for reading Excel inputs and building coordinate sets."""

from __future__ import annotations

from dataclasses import dataclass
import unicodedata
from typing import List

import numpy as np
import pandas as pd


@dataclass
class NeedPoint:
    id: int
    lat: float
    lng: float


def _normalize(text: str) -> str:
    """Lowercase + remove accents to make column detection robust."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower().strip()


def _safe_float(value):
    if value is None:
        return None
    try:
        if isinstance(value, str):
            value = value.replace(",", ".")
        return float(value)
    except Exception:
        return None


def load_need_points(path: str) -> List[NeedPoint]:
    """Load points needing measurement from DIA_DIEM_CAN_DO.xlsx."""
    df = pd.read_excel(path)
    # Normalize column names without diacritics to reduce typo risks
    col_map = {_normalize(c): c for c in df.columns}
    lon_col = next((col_map[k] for k in col_map if "kinh" in k), None)
    lat_col = next((col_map[k] for k in col_map if "vi" in k), None)
    if lon_col is None or lat_col is None:
        raise ValueError("Không tìm thấy cột KINH ĐỘ / VĨ ĐỘ trong file cần đo")

    df = df[[lon_col, lat_col]].copy()
    df.columns = ["lng", "lat"]
    df["lng"] = df["lng"].apply(_safe_float)
    df["lat"] = df["lat"].apply(_safe_float)
    df = df.dropna(subset=["lng", "lat"]).reset_index(drop=True)

    needs: List[NeedPoint] = [NeedPoint(id=i, lat=row.lat, lng=row.lng) for i, row in df.iterrows()]
    return needs


def build_coordinate_set(data_path: str) -> pd.DataFrame:
    """Build unique coordinate set from data.xlsx with optional province."""
    df = pd.read_excel(data_path)
    province_col = None
    for col in df.columns:
        lower = _normalize(str(col))
        if "tỉnh" in lower or "tinh" in lower:
            province_col = col
            break

    records = []
    for _, row in df.iterrows():
        province_val = row.get(province_col) if province_col else None
        for suffix in ("1", "2"):
            code = row.get(f"Mã phòng ban {suffix}")
            name = row.get(f"Tên phòng ban {suffix}")
            lng = _safe_float(row.get(f"KINH ĐỘ {suffix}"))
            lat = _safe_float(row.get(f"VĨ ĐỘ {suffix}"))
            if code is None or lng is None or lat is None:
                continue
            records.append(
                {
                    "ma_phong_ban": code,
                    "ten_phong_ban": name,
                    "lng": lng,
                    "lat": lat,
                    "tinh_thanh": province_val,
                }
            )

    coord_df = pd.DataFrame(records)
    coord_df = coord_df.dropna(subset=["lng", "lat", "ma_phong_ban"])
    coord_df = coord_df.drop_duplicates(subset=["ma_phong_ban"])
    coord_df = coord_df.reset_index(drop=True)
    return coord_df

