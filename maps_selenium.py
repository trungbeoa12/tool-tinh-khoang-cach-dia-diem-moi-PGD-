"""Selenium helpers for fetching driving distance/time from Google Maps."""

from __future__ import annotations

import re
import time
from typing import Optional, Tuple

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def create_driver(headless: bool = True, driver_path: Optional[str] = None, page_load_timeout: int = 60):
    """Create Chrome driver with optional explicit executable path."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--lang=vi")
    service = Service(executable_path=driver_path) if driver_path else None
    driver = webdriver.Chrome(options=options, service=service)
    driver.set_page_load_timeout(page_load_timeout)
    return driver


def _parse_number(raw: str) -> Optional[float]:
    """Parse number with either ',' or '.' as decimal/thousand separator."""
    if raw is None:
        return None
    raw = raw.replace(" ", "")
    if "," in raw and "." in raw:
        # Decide which is decimal: take the rightmost separator
        if raw.rfind(".") > raw.rfind(","):
            # 1,234.5 -> remove commas, keep dot as decimal
            raw_norm = raw.replace(",", "")
        else:
            # 1.234,5 -> remove dots, comma as decimal
            raw_norm = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        # Assume comma is decimal
        raw_norm = raw.replace(".", "").replace(",", ".")
    else:
        # Only dot or plain digits
        raw_norm = raw
    try:
        return float(raw_norm)
    except Exception:
        return None


def _parse_distance_km(text: str) -> Optional[float]:
    """
    Parse distance text. Use word boundary to avoid matching 'm' inside 'min'.
    """
    pattern = re.compile(r"([\d.,]+)\s*(km|kilometer|kilometres|kilometers|m\b|meters|metres)", re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    raw_val = match.group(1)
    value = _parse_number(raw_val)
    if value is None:
        return None
    unit = match.group(2).lower()
    if unit.startswith("m") and not unit.startswith("km"):
        return value / 1000.0
    return value


def _parse_duration_min(text: str) -> Optional[float]:
    text = text.lower()
    hour = 0
    minute = 0
    hour_match = re.search(r"(\d+)\s*(giờ|hour|hrs|h)", text)
    minute_match = re.search(r"(\d+)\s*(phút|min|minutes|m)", text)
    if hour_match:
        hour = int(hour_match.group(1))
    if minute_match:
        minute = int(minute_match.group(1))
    if hour == 0 and minute == 0:
        return None
    return hour * 60 + minute


def _collect_candidate_texts(driver) -> str:
    """Collect texts from various selectors to improve robustness."""
    selectors = [
        'div.section-directions-trip-distance',
        'div.section-directions-trip-duration',
        'div[id^="section-directions-trip-0"]',
        'div[data-trip-index="0"]',
        'div[role="article"]',
        'div[role="feed"]',
    ]
    texts = []
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
        except Exception:
            continue
        for el in elements:
            try:
                txt = el.text
                if txt:
                    texts.append(txt)
            except Exception:
                continue
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        if body_text:
            texts.append(body_text)
    except Exception:
        pass
    return "\n".join(texts)


def get_route_distance_time(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    driver,
    timeout: int = 25,
    throttle_sec: float = 1.2,
    max_retries: int = 3,
) -> Tuple[Optional[float], Optional[float], str, Optional[str]]:
    """
    Fetch driving distance/time using Google Maps directions.

    Returns: (distance_km, duration_min, status, error_message)
    """
    last_error = None
    url = (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={origin_lat},{origin_lng}"
        f"&destination={dest_lat},{dest_lng}"
        "&travelmode=driving"
    )

    for attempt in range(1, max_retries + 1):
        try:
            driver.get(url)
            # Wait for directions card or text containing km
            selectors = [
                (By.CSS_SELECTOR, 'div.section-directions-trip-distance'),
                (By.CSS_SELECTOR, 'div[data-trip-index="0"]'),
                (By.CSS_SELECTOR, 'div[id^="section-directions-trip-0"]'),
            ]
            WebDriverWait(driver, timeout).until(
                lambda d: any(len(d.find_elements(by, sel)) > 0 for by, sel in selectors)
            )

            # Prefer first route card text if present
            try:
                primary_el = driver.find_element(By.CSS_SELECTOR, 'div[data-trip-index=\"0\"]')
                text_blob = primary_el.text or ""
            except Exception:
                text_blob = ""
            if not text_blob:
                text_blob = _collect_candidate_texts(driver)
            distance_km = _parse_distance_km(text_blob)
            duration_min = _parse_duration_min(text_blob)
            if distance_km is not None and duration_min is not None:
                time.sleep(throttle_sec)
                return distance_km, duration_min, "OK", None

            last_error = "Không parse được distance/time"
        except TimeoutException:
            last_error = "Timeout khi tải kết quả chỉ đường"
        except NoSuchElementException:
            last_error = "Không tìm thấy phần tử kết quả"
        except Exception as exc:  # pylint: disable=broad-except
            last_error = f"Lỗi khác: {exc}"

        time.sleep(throttle_sec)
    return None, None, "FAILED", last_error

