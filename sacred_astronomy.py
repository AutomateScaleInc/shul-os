#!/usr/bin/env python3
"""Torah Sanctuary OS — 100% Offline Astronomical Sun, Moon, Zmanim & Hebrew Calendar Engine.

Pure Python standard library (zero third-party dependencies) implementing:
- Exact Hebrew Calendar (Dershowitz & Reingold Calendrical Calculations) with halachic sunset rollover
- High-precision Solar Ephemeris (NOAA / Jean Meeus): real-time altitude, azimuth, compass bearing, 24h arc
- High-precision Lunar Ephemeris (Jean Meeus Ch. 47 + topocentric parallax): real-time illumination %,
  phase angle, lunar age, altitude, azimuth, moonrise, moonset, 24h arc, Kiddush Levana & Rosh Chodesh
- Complete Halachic Zmanim (GRA & Magen Avraham): Alot HaShachar, Misheyakir, Netz, Shema, Tefillah,
  Chatzot, Mincha Gedolah/Ketanah, Plag HaMincha, Candle Lighting, Shkiah, Tzeit HaKochavim, Chatzot HaLailah
- Full Jewish Year Awareness: Shabbat, Festivals, Chanukah nights, Sefirat HaOmer + daily Sefirah,
  Rosh Chodesh, Four Tekufot (seasons), liturgical prayer inserts (Mashiv HaRuach, Tal uMatar, Ya'aleh V'Yavo)
- Great-circle bearing & distance to Jerusalem (Mizrach / Temple Mount)
- Living OS Rhythm: recommended ambient display color temperature (K) & Shabbat Sanctuary stillness flag
"""
import datetime
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"

# Jerusalem — Temple Mount (Har HaBayit)
JERUSALEM_LAT = 31.7781
JERUSALEM_LON = 35.2354

DEFAULT_LOCATION = {
    "city": "Brussels, Belgium",
    "lat": 50.8503,
    "lon": 4.3517,
    "tz": "Europe/Brussels",
    "elevation_m": 58,
    "candle_lighting_offset_min": 18,
    "havdalah_deg": 8.5,
    "in_israel": False,
}

# Canonical city presets for 1-click synagogue deployment worldwide
CITY_PRESETS = {
    "brussels": {"city": "Brussels, Belgium", "lat": 50.8503, "lon": 4.3517, "tz": "Europe/Brussels", "elevation_m": 58, "candle_lighting_offset_min": 18, "in_israel": False},
    "antwerp": {"city": "Antwerp, Belgium", "lat": 51.2194, "lon": 4.4025, "tz": "Europe/Brussels", "elevation_m": 10, "candle_lighting_offset_min": 18, "in_israel": False},
    "jerusalem": {"city": "Jerusalem, Israel", "lat": 31.7683, "lon": 35.2137, "tz": "Asia/Jerusalem", "elevation_m": 780, "candle_lighting_offset_min": 40, "in_israel": True},
    "tel_aviv": {"city": "Tel Aviv, Israel", "lat": 32.0853, "lon": 34.7818, "tz": "Asia/Jerusalem", "elevation_m": 15, "candle_lighting_offset_min": 20, "in_israel": True},
    "london": {"city": "London, UK", "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London", "elevation_m": 25, "candle_lighting_offset_min": 18, "in_israel": False},
    "paris": {"city": "Paris, France", "lat": 48.8566, "lon": 2.3522, "tz": "Europe/Paris", "elevation_m": 35, "candle_lighting_offset_min": 18, "in_israel": False},
    "new_york": {"city": "New York, NY", "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York", "elevation_m": 15, "candle_lighting_offset_min": 18, "in_israel": False},
    "miami": {"city": "Miami, FL", "lat": 25.7617, "lon": -80.1918, "tz": "America/New_York", "elevation_m": 3, "candle_lighting_offset_min": 18, "in_israel": False},
    "los_angeles": {"city": "Los Angeles, CA", "lat": 34.0522, "lon": -118.2437, "tz": "America/Los_Angeles", "elevation_m": 85, "candle_lighting_offset_min": 18, "in_israel": False},
}

# =============================================================================
# 1. EXACT HEBREW CALENDAR (Dershowitz & Reingold — 100% Offline)
# =============================================================================
HEBREW_EPOCH = -1373428  # Adjusted so hebrew_to_rd(1, 7, 1) == -1373427 (R.D. 1 == 0001-01-01 Gregorian)

HEBREW_MONTHS_EN = {
    1: "Nisan", 2: "Iyyar", 3: "Sivan", 4: "Tammuz", 5: "Av", 6: "Elul",
    7: "Tishrei", 8: "Cheshvan", 9: "Kislev", 10: "Tevet", 11: "Shevat",
    12: "Adar", 13: "Adar II",
}
HEBREW_MONTHS_HE = {
    1: "נִיסָן", 2: "אִיָּיר", 3: "סִיוָן", 4: "תַּמּוּז", 5: "אָב", 6: "אֱלוּל",
    7: "תִּשְׁרֵי", 8: "חֶשְׁוָן", 9: "כִּסְלֵו", 10: "טֵבֵת", 11: "שְׁבָט",
    12: "אֲדָר", 13: "אֲדָר ב׳",
}
OMER_SEFIROT = [
    ("Chesed", "חֶסֶד", "Loving-kindness"),
    ("Gevurah", "גְּבוּרָה", "Discipline & Strength"),
    ("Tiferet", "תִּפְאֶרֶת", "Harmony & Compassion"),
    ("Netzach", "נֵצַח", "Endurance & Ambition"),
    ("Hod", "הוֹד", "Humility & Gratitude"),
    ("Yesod", "יְסוֹד", "Connection & Integrity"),
    ("Malchut", "מַלְכוּת", "Dignity & Leadership"),
]


def is_hebrew_leap_year(hy: int) -> bool:
    return ((7 * hy + 1) % 19) < 7


def hebrew_year_months(hy: int) -> int:
    return 13 if is_hebrew_leap_year(hy) else 12


def _hebrew_calendar_elapsed_days(hy: int) -> int:
    months_elapsed = (235 * ((hy - 1) // 19)) + (12 * ((hy - 1) % 19)) + ((7 * ((hy - 1) % 19) + 1) // 19)
    parts_elapsed = 204 + 793 * (months_elapsed % 1080)
    hours_elapsed = 5 + 12 * months_elapsed + 793 * (months_elapsed // 1080) + (parts_elapsed // 1080)
    day = 1 + 29 * months_elapsed + (hours_elapsed // 24)
    parts = 1080 * (hours_elapsed % 24) + (parts_elapsed % 1080)
    # Molad Zaken / Adu / Gatrad / Betutakpat postponements
    if (parts >= 19440) or ((day % 7 == 2) and (parts >= 9924) and not is_hebrew_leap_year(hy)) or ((day % 7 == 1) and (parts >= 16789) and is_hebrew_leap_year(hy - 1)):
        alt_day = day + 1
    else:
        alt_day = day
    if (alt_day % 7) in (0, 3, 5):
        alt_day += 1
    return alt_day


def _hebrew_year_days(hy: int) -> int:
    return _hebrew_calendar_elapsed_days(hy + 1) - _hebrew_calendar_elapsed_days(hy)


def _long_cheshvan(hy: int) -> bool:
    return (_hebrew_year_days(hy) % 10) == 5


def _short_kislev(hy: int) -> bool:
    return (_hebrew_year_days(hy) % 10) == 3


def last_day_of_hebrew_month(hm: int, hy: int) -> int:
    if hm in (2, 4, 6, 10, 13):
        return 29
    if hm == 12 and not is_hebrew_leap_year(hy):
        return 29
    if hm == 8 and not _long_cheshvan(hy):
        return 29
    if hm == 9 and _short_kislev(hy):
        return 29
    return 30


def hebrew_to_rd(hy: int, hm: int, hd: int) -> int:
    # R.D. where 0001-01-01 Gregorian == 1 (matches datetime.date.toordinal())
    rd = HEBREW_EPOCH + _hebrew_calendar_elapsed_days(hy) + hd - 1
    if hm < 7:
        for m in range(7, hebrew_year_months(hy) + 1):
            rd += last_day_of_hebrew_month(m, hy)
        for m in range(1, hm):
            rd += last_day_of_hebrew_month(m, hy)
    else:
        for m in range(7, hm):
            rd += last_day_of_hebrew_month(m, hy)
    return rd


def gregorian_to_hebrew(gdate: datetime.date) -> dict:
    rd = gdate.toordinal()
    approx = int((rd - HEBREW_EPOCH) / 365.2468) + 1
    hy = approx - 1
    while hebrew_to_rd(hy + 1, 7, 1) <= rd:
        hy += 1
    start = 1 if rd < hebrew_to_rd(hy, 1, 1) else 7
    # Wait: if rd < 1 Nisan of hy, month is between 7 (Tishrei) and end of year; else 1..6!
    if rd < hebrew_to_rd(hy, 1, 1):
        hm = 7
        while rd > hebrew_to_rd(hy, hm, last_day_of_hebrew_month(hm, hy)):
            hm += 1
    else:
        hm = 1
        while rd > hebrew_to_rd(hy, hm, last_day_of_hebrew_month(hm, hy)):
            hm += 1
    hd = rd - hebrew_to_rd(hy, hm, 1) + 1
    leap = is_hebrew_leap_year(hy)
    en_m = "Adar I" if (hm == 12 and leap) else HEBREW_MONTHS_EN[hm]
    he_m = "אֲדָר א׳" if (hm == 12 and leap) else HEBREW_MONTHS_HE[hm]
    month_len = last_day_of_hebrew_month(hm, hy)
    return {
        "year": hy,
        "month": hm,
        "day": hd,
        "is_leap_year": leap,
        "month_length": month_len,
        "month_name_en": en_m,
        "month_name_he": he_m,
        "en_str": f"{hd} {en_m} {hy}",
        "he_str": f"{to_hebrew_numeral(hd)} {he_m} {to_hebrew_numeral(hy % 1000)}",
    }


def to_hebrew_numeral(n: int) -> str:
    if n <= 0:
        return ""
    hundreds = [(400, "ת"), (300, "ש"), (200, "ר"), (100, "ק")]
    tens = [(90, "צ"), (80, "פ"), (70, "ע"), (60, "ס"), (50, "נ"), (40, "מ"), (30, "ל"), (20, "כ"), (10, "י")]
    ones = [(9, "ט"), (8, "ח"), (7, "ז"), (6, "ו"), (5, "ה"), (4, "ד"), (3, "ג"), (2, "ב"), (1, "א")]
    out = []
    rem = n
    while rem >= 400:
        out.append("ת")
        rem -= 400
    for val, ch in hundreds:
        if rem >= val:
            out.append(ch)
            rem -= val
    if rem == 15:
        out.extend(["ט", "ו"])
        rem = 0
    elif rem == 16:
        out.extend(["ט", "ז"])
        rem = 0
    else:
        for val, ch in tens:
            if rem >= val:
                out.append(ch)
                rem -= val
        for val, ch in ones:
            if rem >= val:
                out.append(ch)
                rem -= val
    if len(out) == 1:
        return out[0] + "׳"
    return "".join(out[:-1]) + "״" + out[-1]


# =============================================================================
# 2. SOLAR & LUNAR EPHEMERIS (Jean Meeus / NOAA — 100% Offline)
# =============================================================================
def _julian_day(dt_utc: datetime.datetime) -> float:
    y = dt_utc.year
    m = dt_utc.month
    d = dt_utc.day + (dt_utc.hour + (dt_utc.minute + (dt_utc.second + dt_utc.microsecond / 1e6) / 60.0) / 60.0) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + (a // 4)
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def _compass_dir(az_deg: float) -> str:
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[int((az_deg + 11.25) // 22.5) % 16]


def _gmst_deg(jd: float) -> float:
    t = (jd - 2451545.0) / 36525.0
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * t * t - (t * t * t) / 38710000.0
    return gmst % 360.0


def _equatorial_to_horizontal(ra_deg: float, dec_deg: float, jd: float, lat: float, lon: float) -> tuple[float, float]:
    lst = (_gmst_deg(jd) + lon) % 360.0
    ha = math.radians((lst - ra_deg + 540.0) % 360.0 - 180.0)
    lat_r = math.radians(lat)
    dec_r = math.radians(dec_deg)
    sin_alt = math.sin(lat_r) * math.sin(dec_r) + math.cos(lat_r) * math.cos(dec_r) * math.cos(ha)
    alt = math.asin(max(-1.0, min(1.0, sin_alt)))
    cos_az = (math.sin(dec_r) - math.sin(alt) * math.sin(lat_r)) / max(1e-9, math.cos(alt) * math.cos(lat_r))
    az = math.degrees(math.acos(max(-1.0, min(1.0, cos_az))))
    if math.sin(ha) > 0:
        az = 360.0 - az
    return math.degrees(alt), az % 360.0


def solar_position(dt_utc: datetime.datetime, lat: float, lon: float) -> dict:
    jd = _julian_day(dt_utc)
    t = (jd - 2451545.0) / 36525.0
    l0 = (280.46646 + 36000.76983 * t + 0.0003032 * t * t) % 360.0
    m = (357.52911 + 35999.05029 * t - 0.0001537 * t * t) % 360.0
    mr = math.radians(m)
    c = (
        (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(mr)
        + (0.019993 - 0.000101 * t) * math.sin(2 * mr)
        + 0.000289 * math.sin(3 * mr)
    )
    true_lon = l0 + c
    omega = 125.04 - 1934.136 * t
    app_lon = true_lon - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    eps0 = 23.0 + (26.0 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60.0) / 60.0
    eps = eps0 + 0.00256 * math.cos(math.radians(omega))

    al_r = math.radians(app_lon)
    eps_r = math.radians(eps)
    ra = math.degrees(math.atan2(math.cos(eps_r) * math.sin(al_r), math.cos(al_r))) % 360.0
    dec = math.degrees(math.asin(max(-1.0, min(1.0, math.sin(eps_r) * math.sin(al_r)))))
    alt, az = _equatorial_to_horizontal(ra, dec, jd, lat, lon)
    # Atmospheric refraction correction near horizon
    if alt > -1.5:
        refr = 1.02 / math.tan(math.radians(alt + 10.3 / (alt + 5.11))) / 60.0
        alt_app = alt + max(0.0, refr)
    else:
        alt_app = alt

    return {
        "altitude_deg": round(alt_app, 2),
        "geometric_alt_deg": round(alt, 2),
        "azimuth_deg": round(az, 1),
        "compass": _compass_dir(az),
        "declination_deg": round(dec, 2),
        "apparent_lon_deg": round(app_lon % 360.0, 3),
        "above_horizon": alt_app > 0.0,
    }


def lunar_position(dt_utc: datetime.datetime, lat: float, lon: float) -> dict:
    """High-accuracy lunar position, phase, illumination %, and topocentric elevation (Meeus Ch. 47)."""
    jd = _julian_day(dt_utc)
    t = (jd - 2451545.0) / 36525.0

    # Fundamental lunar arguments (degrees)
    lp = (218.3164477 + 481267.88123421 * t - 0.0015786 * t * t + t * t * t / 538841.0) % 360.0
    d = (297.8501921 + 445267.1114034 * t - 0.0018819 * t * t + t * t * t / 545868.0) % 360.0
    m = (357.5291092 + 35999.0502909 * t - 0.0001536 * t * t) % 360.0
    mp = (134.9633964 + 477198.8675055 * t + 0.0087414 * t * t + t * t * t / 69699.0) % 360.0
    f = (93.2720950 + 483202.0175233 * t - 0.0036539 * t * t) % 360.0

    dr, mr, mpr, fr = map(math.radians, (d, m, mp, f))
    e = 1.0 - 0.002516 * t - 0.0000074 * t * t

    # Leading longitude perturbation terms (degrees)
    sum_l = (
        6.288774 * math.sin(mpr)
        + 1.274027 * math.sin(2 * dr - mpr)
        + 0.658314 * math.sin(2 * dr)
        + 0.213618 * math.sin(2 * mpr)
        - 0.185116 * e * math.sin(mr)
        - 0.114332 * math.sin(2 * fr)
        + 0.058793 * math.sin(2 * dr - 2 * mpr)
        + 0.057066 * e * math.sin(2 * dr - mr - mpr)
        + 0.053322 * math.sin(2 * dr + mpr)
        + 0.045758 * e * math.sin(2 * dr - mr)
        - 0.040923 * e * math.sin(mr - mpr)
        - 0.034720 * math.sin(dr)
        - 0.030383 * e * math.sin(mr + mpr)
        + 0.015327 * math.sin(2 * dr - 2 * fr)
        - 0.012528 * math.sin(mpr + 2 * fr)
        + 0.010980 * math.sin(mpr - 2 * fr)
    )
    # Leading latitude perturbation terms (degrees)
    sum_b = (
        5.128122 * math.sin(fr)
        + 0.280602 * math.sin(mpr + fr)
        + 0.277693 * math.sin(mpr - fr)
        + 0.173237 * math.sin(2 * dr - fr)
        + 0.055413 * math.sin(2 * dr - mpr + fr)
        + 0.046271 * math.sin(2 * dr - mpr - fr)
        + 0.032573 * math.sin(2 * dr + fr)
        + 0.017198 * math.sin(2 * mpr + fr)
    )
    # Distance in km (Meeus Table 47.A leading terms)
    dist_km = (
        385000.56
        - 20905.355 * math.cos(mpr)
        - 3699.111 * math.cos(2 * dr - mpr)
        - 2955.968 * math.cos(2 * dr)
        - 569.925 * math.cos(2 * mpr)
    )

    moon_lon = (lp + sum_l) % 360.0
    moon_lat = sum_b

    eps = math.radians(23.439291 - 0.0130042 * t)
    mlon_r = math.radians(moon_lon)
    mlat_r = math.radians(moon_lat)

    sin_dec = math.sin(mlat_r) * math.cos(eps) + math.cos(mlat_r) * math.sin(eps) * math.sin(mlon_r)
    dec = math.degrees(math.asin(max(-1.0, min(1.0, sin_dec))))
    ra = math.degrees(math.atan2(math.sin(mlon_r) * math.cos(eps) - math.tan(mlat_r) * math.sin(eps), math.cos(mlon_r))) % 360.0

    alt_geo, az = _equatorial_to_horizontal(ra, dec, jd, lat, lon)
    # Topocentric parallax correction (~0.95 deg at horizon) + refraction
    hp_deg = math.degrees(math.asin(min(1.0, 6378.14 / dist_km)))
    alt_topo = alt_geo - hp_deg * math.cos(math.radians(alt_geo))
    if alt_topo > -1.5:
        refr = 1.02 / math.tan(math.radians(alt_topo + 10.3 / (alt_topo + 5.11))) / 60.0
        alt_topo += max(0.0, refr)

    # Exact elongation from Sun -> illumination & phase angle (0=New, 90=First Qtr, 180=Full, 270=Last Qtr)
    sun = solar_position(dt_utc, lat, lon)
    phase_angle = (moon_lon - sun["apparent_lon_deg"]) % 360.0
    illum_frac = (1.0 - math.cos(math.radians(phase_angle))) / 2.0
    illum_pct = round(illum_frac * 100.0, 1)
    synodic_month = 29.530588853
    lunar_age_days = round((phase_angle / 360.0) * synodic_month, 2)
    waxing = phase_angle < 180.0

    if phase_angle < 12 or phase_angle >= 348:
        phase_en, phase_he, emoji = "New Moon (Molad)", "מוֹלָד / רֹאשׁ חֹדֶשׁ", "🌑"
    elif phase_angle < 78:
        phase_en, phase_he, emoji = "Waxing Crescent", "יָרֵחַ מִתְמַלֵּא (חֶרְמֵשׁ)", "🌒"
    elif phase_angle < 102:
        phase_en, phase_he, emoji = "First Quarter", "רֶבַע רִאשׁוֹן", "🌓"
    elif phase_angle < 168:
        phase_en, phase_he, emoji = "Waxing Gibbous", "יָרֵחַ מִתְמַלֵּא", "🌔"
    elif phase_angle < 192:
        phase_en, phase_he, emoji = "Full Moon (Kese)", "יָרֵחַ מָלֵא (כֶּסֶא)", "🌕"
    elif phase_angle < 258:
        phase_en, phase_he, emoji = "Waning Gibbous", "יָרֵחַ מִתְחַסֵּר", "🌖"
    elif phase_angle < 282:
        phase_en, phase_he, emoji = "Last Quarter", "רֶבַע אַחֲרוֹן", "🌗"
    else:
        phase_en, phase_he, emoji = "Waning Crescent", "יָרֵחַ מִתְחַסֵּר (סוֹף חֹדֶשׁ)", "🌘"

    return {
        "altitude_deg": round(alt_topo, 2),
        "azimuth_deg": round(az, 1),
        "compass": _compass_dir(az),
        "above_horizon": alt_topo > 0.0,
        "illumination_pct": illum_pct,
        "phase_angle_deg": round(phase_angle, 1),
        "lunar_age_days": lunar_age_days,
        "synodic_cycle_days": 29.53,
        "waxing": waxing,
        "phase_en": phase_en,
        "phase_he": phase_he,
        "emoji": emoji,
        "distance_km": int(round(dist_km)),
    }


def _find_solar_crossing(local_date: datetime.date, tz: ZoneInfo, lat: float, lon: float, target_alt: float, rising: bool) -> datetime.datetime | None:
    """Scan local day at 10-min intervals & bisect to 10-second precision for solar altitude crossing."""
    start = datetime.datetime(local_date.year, local_date.month, local_date.day, 0, 0, tzinfo=tz)
    prev_dt = start
    prev_val = solar_position(prev_dt.astimezone(datetime.timezone.utc), lat, lon)["geometric_alt_deg"] - target_alt
    for step in range(1, 145):
        cur_dt = start + datetime.timedelta(minutes=step * 10)
        cur_val = solar_position(cur_dt.astimezone(datetime.timezone.utc), lat, lon)["geometric_alt_deg"] - target_alt
        crossed = (prev_val <= 0 < cur_val) if rising else (prev_val >= 0 > cur_val)
        if crossed:
            lo, hi = prev_dt, cur_dt
            for _ in range(9):
                mid = lo + (hi - lo) / 2
                mv = solar_position(mid.astimezone(datetime.timezone.utc), lat, lon)["geometric_alt_deg"] - target_alt
                if (mv < 0) == rising:
                    lo = mid
                else:
                    hi = mid
            return lo + (hi - lo) / 2
        prev_dt, prev_val = cur_dt, cur_val
    return None


def _find_lunar_rise_set(local_date: datetime.date, tz: ZoneInfo, lat: float, lon: float) -> tuple[datetime.datetime | None, datetime.datetime | None]:
    """Scan local day at 15-min intervals & bisect to 30-second precision for moonrise/moonset."""
    start = datetime.datetime(local_date.year, local_date.month, local_date.day, 0, 0, tzinfo=tz)
    rise_dt, set_dt = None, None
    prev_dt = start
    prev_val = lunar_position(prev_dt.astimezone(datetime.timezone.utc), lat, lon)["altitude_deg"]
    for step in range(1, 97):
        cur_dt = start + datetime.timedelta(minutes=step * 15)
        cur_val = lunar_position(cur_dt.astimezone(datetime.timezone.utc), lat, lon)["altitude_deg"]
        if rise_dt is None and prev_val <= 0 < cur_val:
            lo, hi = prev_dt, cur_dt
            for _ in range(8):
                mid = lo + (hi - lo) / 2
                if lunar_position(mid.astimezone(datetime.timezone.utc), lat, lon)["altitude_deg"] < 0:
                    lo = mid
                else:
                    hi = mid
            rise_dt = lo + (hi - lo) / 2
        if set_dt is None and prev_val >= 0 > cur_val:
            lo, hi = prev_dt, cur_dt
            for _ in range(8):
                mid = lo + (hi - lo) / 2
                if lunar_position(mid.astimezone(datetime.timezone.utc), lat, lon)["altitude_deg"] > 0:
                    lo = mid
                else:
                    hi = mid
            set_dt = lo + (hi - lo) / 2
        prev_dt, prev_val = cur_dt, cur_val
    return rise_dt, set_dt


def bearing_to_jerusalem(lat: float, lon: float) -> dict:
    lat1, lon1, lat2, lon2 = map(math.radians, (lat, lon, JERUSALEM_LAT, JERUSALEM_LON))
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    brng = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
    # Haversine distance
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    dist_km = 6371.0 * 2 * math.asin(min(1.0, math.sqrt(a)))
    return {
        "bearing_deg": round(brng, 1),
        "compass": _compass_dir(brng),
        "distance_km": int(round(dist_km)),
    }


# =============================================================================
# 3. JEWISH YEAR CYCLE, HOLIDAYS, TEKUFOT, OMER & LITURGICAL COMPASS
# =============================================================================
def get_upcoming_milestones(he_date: dict, gdate: datetime.date, in_israel: bool = False) -> dict:
    """100% offline calculator for exact Next Rosh Chodesh, Shabbat Mevarchim, and Next 4 Jewish Holidays."""
    hy, hm, hd = he_date["year"], he_date["month"], he_date["day"]
    leap = he_date["is_leap_year"]
    today_rd = gdate.toordinal()

    # 1. Exact Next Rosh Chodesh
    months_in_y = hebrew_year_months(hy)
    if hm == months_in_y:
        rc_hy, rc_hm = hy + 1, 7 if months_in_y == 12 else 1
    else:
        rc_hy, rc_hm = (hy + 1, 7) if hm == 6 else (hy, hm + 1)
    # Wait: Hebrew year increments at Tishrei (month 7)! Months in order of year are 7,8,9,10,11,12,(13),1,2,3,4,5,6.
    yr_order = [7, 8, 9, 10, 11, 12] + ([13] if leap else []) + [1, 2, 3, 4, 5, 6]
    idx_m = yr_order.index(hm)
    if idx_m + 1 < len(yr_order):
        rc_hy, rc_hm = hy, yr_order[idx_m + 1]
    else:
        rc_hy, rc_hm = hy + 1, 7
    rc_rd = hebrew_to_rd(rc_hy, rc_hm, 1)
    rc_gdate = datetime.date.fromordinal(rc_rd)
    rc_days = max(0, rc_rd - today_rd)
    rc_name_en = "Adar I" if (rc_hm == 12 and is_hebrew_leap_year(rc_hy)) else HEBREW_MONTHS_EN[rc_hm]
    rc_name_he = "אֲדָר א׳" if (rc_hm == 12 and is_hebrew_leap_year(rc_hy)) else HEBREW_MONTHS_HE[rc_hm]
    shabbat_mevarchim_soon = (1 <= rc_days <= 8) and (rc_hm != 7)

    # 2. Next 4 Upcoming Major Jewish Festivals / Milestones (scanning hy and hy+1)
    milestones = []
    for cand_y in (hy, hy + 1):
        adar_p = 13 if is_hebrew_leap_year(cand_y) else 12
        defs = [
            (7, 1, "Rosh Hashanah", "רֹאשׁ הַשָּׁנָה", "🍎"),
            (7, 10, "Yom Kippur", "יוֹם כִּפּוּר", "🕊"),
            (7, 15, "Sukkot", "סֻכּוֹת", "🌿"),
            (7, 22, "Shemini Atzeret / Simchat Torah", "שִׂמְחַת תּוֹרָה", "📜"),
            (9, 25, "Chanukah (1st Day · Eve prior night)", "חֲנֻכָּה", "🕎"),
            (10, 10, "Asara B'Tevet", "עֲשָׂרָה בְּטֵבֵת", "🕯"),
            (11, 15, "Tu B'Shvat (New Year of Trees)", "ט״ו בִּשְׁבָט", "🌳"),
            (adar_p, 14, "Purim", "פּוּרִים", "👑"),
            (1, 15, "Pesach (Passover)", "פֶּסַח", "🍷"),
            (2, 18, "Lag BaOmer", "ל״ג בָּעֹמֶר", "🔥"),
            (3, 6, "Shavuot (Giving of the Torah)", "שָׁבוּעוֹת", "⛰"),
            (5, 9, "Tisha B'Av", "תִּשְׁעָה בְּאָב", "🕯"),
            (5, 15, "Tu B'Av", "ט״ו בְּאָב", "💛"),
        ]
        for mm, dd, en_n, he_n, em in defs:
            m_rd = hebrew_to_rd(cand_y, mm, dd)
            if m_rd >= today_rd:
                gd = datetime.date.fromordinal(m_rd)
                milestones.append({
                    "days_away": m_rd - today_rd,
                    "name": en_n,
                    "he": he_n,
                    "emoji": em,
                    "hebrew_date": f"{dd} {HEBREW_MONTHS_EN[mm]} {cand_y}",
                    "gregorian_date": gd.strftime("%b %d, %Y"),
                })
    milestones.sort(key=lambda x: x["days_away"])

    # 3. Ordered Months for the 12/13-Month Jewish Year Wheel SVG
    wheel_months = []
    fest_short = {7: "Tishrei · High Holidays", 8: "Cheshvan", 9: "Kislev · Chanukah", 10: "Tevet", 11: "Shevat · Tu B'Shvat", 12: "Adar · Purim", 13: "Adar II · Purim", 1: "Nisan · Pesach", 2: "Iyyar · Omer", 3: "Sivan · Shavuot", 4: "Tammuz", 5: "Av", 6: "Elul · Shofar"}
    for m_num in yr_order:
        m_en = "Adar I" if (m_num == 12 and leap) else HEBREW_MONTHS_EN[m_num]
        m_he = "אֲדָר א׳" if (m_num == 12 and leap) else HEBREW_MONTHS_HE[m_num]
        wheel_months.append({
            "num": m_num,
            "en": m_en,
            "he": m_he,
            "note": fest_short.get(m_num, m_en),
            "is_current": (m_num == hm),
            "day_frac": round(hd / max(29, he_date["month_length"]), 3) if m_num == hm else 0.0,
        })

    return {
        "next_rosh_chodesh": {
            "month_en": rc_name_en,
            "month_he": rc_name_he,
            "gregorian_date": rc_gdate.strftime("%a, %b %d, %Y"),
            "days_away": rc_days,
            "shabbat_mevarchim_soon": shabbat_mevarchim_soon,
        },
        "upcoming_holidays": milestones[:5],
        "wheel_months": wheel_months,
    }


def get_jewish_year_context(he_date: dict, gdate: datetime.date, in_israel: bool = False) -> dict:
    hy, hm, hd = he_date["year"], he_date["month"], he_date["day"]
    leap = he_date["is_leap_year"]
    adar_purim = 13 if leap else 12
    special_days = []
    is_yom_tov = False
    chanukah_night = None
    omer_day = None
    omer_info = None

    # Rosh Chodesh
    if hd == 1 and hm != 7:
        special_days.append({"name": f"Rosh Chodesh {he_date['month_name_en']}", "he": f"רֹאשׁ חֹדֶשׁ {he_date['month_name_he']}", "kind": "rosh_chodesh"})
    elif hd == 30:
        next_m = 1 if hm == hebrew_year_months(hy) else (hm + 1)
        nm_en = "Adar I" if (next_m == 12 and leap) else HEBREW_MONTHS_EN[next_m]
        special_days.append({"name": f"Rosh Chodesh {nm_en} (Day 1)", "he": "רֹאשׁ חֹדֶשׁ (א׳)", "kind": "rosh_chodesh"})

    # Tishrei (7)
    if hm == 7:
        if hd in (1, 2):
            special_days.append({"name": f"Rosh Hashanah (Day {hd})", "he": "רֹאשׁ הַשָּׁנָה", "kind": "yom_tov"})
            is_yom_tov = True
        elif hd == 3:
            special_days.append({"name": "Tzom Gedaliah", "he": "צוֹם גְּדַלְיָה", "kind": "fast"})
        elif 1 <= hd <= 10:
            special_days.append({"name": "Aseret Yemei Teshuvah (Ten Days of Repentance)", "he": "עֲשֶׂרֶת יְמֵי תְּשׁוּבָה", "kind": "season"})
        if hd == 10:
            special_days.append({"name": "Yom Kippur", "he": "יוֹם כִּפּוּר", "kind": "yom_tov"})
            is_yom_tov = True
        elif 15 <= hd <= 21:
            if hd == 15 or (hd == 16 and not in_israel):
                special_days.append({"name": "Sukkot (Yom Tov)", "he": "סֻכּוֹת", "kind": "yom_tov"})
                is_yom_tov = True
            elif hd == 21:
                special_days.append({"name": "Hoshana Rabbah", "he": "הוֹשַׁעְנָא רַבָּה", "kind": "festival"})
            else:
                special_days.append({"name": "Chol HaMoed Sukkot", "he": "חוֹל הַמּוֹעֵד סֻכּוֹת", "kind": "festival"})
        elif hd == 22:
            special_days.append({"name": "Shemini Atzeret" + (" & Simchat Torah" if in_israel else ""), "he": "שְׁמִינִי עֲצֶרֶת", "kind": "yom_tov"})
            is_yom_tov = True
        elif hd == 23 and not in_israel:
            special_days.append({"name": "Simchat Torah", "he": "שִׂמְחַת תּוֹרָה", "kind": "yom_tov"})
            is_yom_tov = True

    # Kislev (9) & Tevet (10) — Chanukah
    if hm == 9 and hd >= 25:
        chanukah_night = hd - 24
        special_days.append({"name": f"Chanukah — Day {chanukah_night}", "he": f"חֲנֻכָּה · נֵר {to_hebrew_numeral(chanukah_night)}", "kind": "festival"})
    elif hm == 10:
        kislev_len = last_day_of_hebrew_month(9, hy)
        c_day = (kislev_len - 24) + hd
        if c_day <= 8:
            chanukah_night = c_day
            special_days.append({"name": f"Chanukah — Day {c_day}", "he": f"חֲנֻכָּה · נֵר {to_hebrew_numeral(c_day)}", "kind": "festival"})
        if hd == 10:
            special_days.append({"name": "Asara B'Tevet", "he": "עֲשָׂרָה בְּטֵבֵת", "kind": "fast"})

    # Shevat (11)
    if hm == 11 and hd == 15:
        special_days.append({"name": "Tu B'Shvat (New Year of the Trees)", "he": "ט״ו בִּשְׁבָט", "kind": "festival"})

    # Adar / Purim
    if hm == adar_purim:
        if hd == 13:
            special_days.append({"name": "Ta'anit Esther", "he": "תַּעֲנִית אֶסְתֵּר", "kind": "fast"})
        elif hd == 14:
            special_days.append({"name": "Purim", "he": "פּוּרִים", "kind": "festival"})
        elif hd == 15:
            special_days.append({"name": "Shushan Purim", "he": "שׁוּשַׁן פּוּרִים", "kind": "festival"})

    # Nisan (1) — Pesach
    if hm == 1:
        if 15 <= hd <= (21 if in_israel else 22):
            if hd in (15, 21) or (not in_israel and hd in (16, 22)):
                special_days.append({"name": "Pesach (Yom Tov)", "he": "פֶּסַח", "kind": "yom_tov"})
                is_yom_tov = True
            else:
                special_days.append({"name": "Chol HaMoed Pesach", "he": "חוֹל הַמּוֹעֵד פֶּסַח", "kind": "festival"})

    # Sefirat HaOmer (16 Nisan to 5 Sivan = 49 days)
    if (hm == 1 and hd >= 16) or (hm == 2) or (hm == 3 and hd <= 5):
        rd_now = hebrew_to_rd(hy, hm, hd)
        rd_omer1 = hebrew_to_rd(hy, 1, 16)
        omer_day = rd_now - rd_omer1 + 1
        if 1 <= omer_day <= 49:
            wk = (omer_day - 1) // 7
            dy = (omer_day - 1) % 7
            inner = OMER_SEFIROT[dy]
            outer = OMER_SEFIROT[wk]
            omer_info = {
                "day": omer_day,
                "weeks": omer_day // 7,
                "remainder_days": omer_day % 7,
                "sefirah_en": f"{inner[0]} sheb'{outer[0]} ({inner[2]} within {outer[2]})",
                "sefirah_he": f"{inner[1]} שֶׁבְּ{outer[1]}",
            }
            if omer_day == 33:
                special_days.append({"name": "Lag BaOmer (Day 33 of the Omer)", "he": "ל״ג בָּעֹמֶר", "kind": "festival"})

    # Sivan (3) — Shavuot
    if hm == 3 and (hd == 6 or (hd == 7 and not in_israel)):
        special_days.append({"name": "Shavuot (Giving of the Torah)", "he": "שָׁבוּעוֹת", "kind": "yom_tov"})
        is_yom_tov = True

    # Tammuz (4) & Av (5)
    if hm == 4 and hd == 17:
        special_days.append({"name": "Shiva Asar B'Tammuz", "he": "שִׁבְעָה עָשָׂר בְּתַמּוּז", "kind": "fast"})
    if (hm == 4 and hd >= 17) or (hm == 5 and hd <= 9):
        special_days.append({"name": "The Three Weeks (Bein HaMetzarim)", "he": "בֵּין הַמְּצָרִים", "kind": "season"})
    if hm == 5 and hd == 9:
        special_days.append({"name": "Tisha B'Av", "he": "תִּשְׁעָה בְּאָב", "kind": "fast"})
    if hm == 5 and hd == 15:
        special_days.append({"name": "Tu B'Av (Day of Joy & Love)", "he": "ט״ו בְּאָב", "kind": "festival"})

    # Elul (6)
    if hm == 6:
        special_days.append({"name": "Month of Elul (Shofar & Spiritual Reflection)", "he": "חֹדֶשׁ אֱלוּל", "kind": "season"})

    # Liturgical Prayer Inserts (Mashiv HaRuach, V'ten Tal uMatar, Ya'aleh V'Yavo)
    in_winter_mashiv = (hm == 7 and hd >= 22) or (hm in (8, 9, 10, 11, 12, 13)) or (hm == 1 and hd < 15)
    # V'ten Tal uMatar: Diaspora Dec 4/5 until Pesach; Israel 7 Cheshvan until Pesach
    if in_israel:
        in_rain_request = (hm == 8 and hd >= 7) or (hm in (9, 10, 11, 12, 13)) or (hm == 1 and hd < 15)
    else:
        in_rain_request = ((gdate.month == 12 and gdate.day >= 5) or (gdate.month in (1, 2, 3)) or (hm == 1 and hd < 15)) and in_winter_mashiv
    prayers = [
        "Mashiv HaRuach uMorid HaGeshem (He causes the wind to blow and the rain to fall)" if in_winter_mashiv else "Morid HaTal (He causes the dew to fall)",
        "V'ten Tal uMatar Livrachah (Grant dew and rain for blessing)" if in_rain_request else "V'ten Berachah (Grant blessing)",
    ]
    if any(s["kind"] in ("rosh_chodesh", "yom_tov", "festival") and "Chanukah" not in s["name"] and "Purim" not in s["name"] and "Tu B'" not in s["name"] and "Lag" not in s["name"] for s in special_days):
        prayers.append("Ya'aleh V'Yavo (Rosh Chodesh / Festival insertion)")
    if chanukah_night:
        prayers.append("Al HaNissim (Chanukah) & Full Hallel")

    # Four Tekufot (Jewish Solar-Agricultural Seasons)
    m_g = gdate.month
    if m_g in (3, 4, 5):
        tekufah = {"en": "Tekufat Nisan (Spring Awakening)", "he": "תְּקוּפַת נִיסָן"}
    elif m_g in (6, 7, 8):
        tekufah = {"en": "Tekufat Tammuz (Summer Radiance)", "he": "תְּקוּפַת תַּמּוּז"}
    elif m_g in (9, 10, 11):
        tekufah = {"en": "Tekufat Tishrei (Autumn Harvest & Ingathering)", "he": "תְּקוּפַת תִּשְׁרֵי"}
    else:
        tekufah = {"en": "Tekufat Tevet (Winter Sanctuary & Light)", "he": "תְּקוּפַת טֵבֵת"}

    # Kiddush Levana (Sanctification of the New Moon): Day 3 through Day 15 of the Hebrew month
    kiddush_levana = {
        "in_window": 3 <= hd <= 15,
        "hebrew_day": hd,
        "status": (
            f"Kiddush Levana window OPEN (Day {hd} of {he_date['month_name_en']} · waxing moon visible at night)"
            if 3 <= hd <= 15
            else (f"Molad / New Month — Kiddush Levana opens in {3 - hd} day(s)" if hd < 3 else f"Waning phase — next Rosh Chodesh in {he_date['month_length'] - hd + 1} day(s)")
        ),
        "days_to_rosh_chodesh": max(0, he_date["month_length"] - hd + 1) if hd != 1 else 0,
    }

    return {
        "special_days": special_days,
        "is_yom_tov": is_yom_tov,
        "chanukah_night": chanukah_night,
        "omer": omer_info,
        "prayers": prayers,
        "tekufah": tekufah,
        "kiddush_levana": kiddush_levana,
        "milestones": get_upcoming_milestones(he_date, gdate, in_israel=in_israel),
    }


# =============================================================================
# 4. MASTER REAL-TIME SACRED SNAPSHOT (Sun + Moon + Zmanim + Hebrew Calendar + OS Rhythm)
# =============================================================================
def load_location_config() -> dict:
    loc = dict(DEFAULT_LOCATION)
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(cfg.get("location"), dict):
                loc.update({k: v for k, v in cfg["location"].items() if v is not None and v != ""})
        except Exception:
            pass
    return loc


def _fmt_hm(dt: datetime.datetime | None) -> str:
    return dt.strftime("%H:%M") if dt else "—"


def get_sacred_moment(now_dt: datetime.datetime | None = None, location: dict | None = None) -> dict:
    loc = dict(DEFAULT_LOCATION)
    loc.update(location or load_location_config())
    lat = float(loc["lat"])
    lon = float(loc["lon"])
    tz = ZoneInfo(str(loc.get("tz") or "Europe/Brussels"))
    candle_offset = int(loc.get("candle_lighting_offset_min", 18))
    havdalah_deg = float(loc.get("havdalah_deg", 8.5))
    in_israel = bool(loc.get("in_israel", False))

    now_local = (now_dt.astimezone(tz) if now_dt else datetime.datetime.now(tz))
    now_utc = now_local.astimezone(datetime.timezone.utc)
    today = now_local.date()

    # Exact current Sun & Moon positions
    sun = solar_position(now_utc, lat, lon)
    moon = lunar_position(now_utc, lat, lon)
    mizrach = bearing_to_jerusalem(lat, lon)

    # Today's Zmanim via exact solar crossings
    alot = _find_solar_crossing(today, tz, lat, lon, -16.1, rising=True)
    misheyakir = _find_solar_crossing(today, tz, lat, lon, -11.5, rising=True)
    sunrise = _find_solar_crossing(today, tz, lat, lon, -0.833, rising=True)
    sunset = _find_solar_crossing(today, tz, lat, lon, -0.833, rising=False)
    tzeit = _find_solar_crossing(today, tz, lat, lon, -havdalah_deg, rising=False)

    if sunrise and sunset:
        day_len = (sunset - sunrise).total_seconds()
        shaah_gra = day_len / 12.0
        chatzot = sunrise + datetime.timedelta(seconds=day_len / 2.0)
        shema_gra = sunrise + datetime.timedelta(seconds=3.0 * shaah_gra)
        tefillah_gra = sunrise + datetime.timedelta(seconds=4.0 * shaah_gra)
        mincha_gedolah = chatzot + datetime.timedelta(seconds=max(1800.0, 0.5 * shaah_gra))
        mincha_ketanah = sunrise + datetime.timedelta(seconds=9.5 * shaah_gra)
        plag_hamincha = sunrise + datetime.timedelta(seconds=10.75 * shaah_gra)
        candle_lighting = sunset - datetime.timedelta(minutes=candle_offset)
        chatzot_lailah = chatzot + datetime.timedelta(hours=12)
        if alot and tzeit:
            shaah_mga = (tzeit - alot).total_seconds() / 12.0
            shema_mga = alot + datetime.timedelta(seconds=3.0 * shaah_mga)
        else:
            shema_mga = shema_gra - datetime.timedelta(minutes=36)
    else:
        shaah_gra = 3600.0
        chatzot = shema_gra = shema_mga = tefillah_gra = mincha_gedolah = mincha_ketanah = plag_hamincha = candle_lighting = chatzot_lailah = None

    # Moonrise & Moonset today
    moonrise, moonset = _find_lunar_rise_set(today, tz, lat, lon)
    moon["moonrise"] = _fmt_hm(moonrise)
    moon["moonset"] = _fmt_hm(moonset)

    # Halachic Sunset Rollover -> exact Jewish Day!
    after_sunset = bool(sunset and now_local >= sunset)
    after_tzeit = bool(tzeit and now_local >= tzeit)
    halachic_gdate = today + datetime.timedelta(days=1) if after_sunset else today
    he_date = gregorian_to_hebrew(halachic_gdate)
    year_ctx = get_jewish_year_context(he_date, halachic_gdate, in_israel=in_israel)

    # Exact Shabbat Status (Friday Candle Lighting -> Saturday Tzeit/Havdalah)
    dow = now_local.weekday()  # Mon=0 .. Fri=4, Sat=5, Sun=6
    is_erev_shabbat = (dow == 4) and not (candle_lighting and now_local >= candle_lighting)
    is_shabbat = ((dow == 4) and bool(candle_lighting and now_local >= candle_lighting)) or ((dow == 5) and not after_tzeit)
    is_motzaei_shabbat = (dow == 5) and after_tzeit
    shabbat_mode = is_shabbat or year_ctx["is_yom_tov"]

    # Build ordered Zmanim schedule + Active & Next Zman countdown
    zmanim_raw = [
        ("alot", "Alot HaShachar (Dawn)", "עֲלוֹת הַשַּׁחַר", alot),
        ("misheyakir", "Misheyakir (Tallit & Tefillin)", "מִשֶּׁיַּכִּיר", misheyakir),
        ("sunrise", "Netz HaChamah (Sunrise)", "נֵץ הַחַמָּה", sunrise),
        ("shema_mga", "Sof Zman Shema (MGA)", "סוֹף זְמַן ק״ש (מג״א)", shema_mga),
        ("shema_gra", "Sof Zman Shema (GRA)", "סוֹף זְמַן ק״ש (גר״א)", shema_gra),
        ("tefillah_gra", "Sof Zman Tefillah (GRA)", "סוֹף זְמַן תְּפִלָּה", tefillah_gra),
        ("chatzot", "Chatzot HaYom (Solar Midday)", "חֲצוֹת הַיּוֹם", chatzot),
        ("mincha_gedolah", "Mincha Gedolah", "מִנְחָה גְּדוֹלָה", mincha_gedolah),
        ("mincha_ketanah", "Mincha Ketanah", "מִנְחָה קְטַנָּה", mincha_ketanah),
        ("plag_hamincha", "Plag HaMincha (Golden Hour)", "פְּלַג הַמִּנְחָה", plag_hamincha),
        ("candle_lighting", "Candle Lighting" if dow == 4 else "Pre-Sunset (18m)", "הַדְלָקַת נֵרוֹת" if dow == 4 else "לִפְנֵי הַשְּׁקִיעָה", candle_lighting),
        ("sunset", "Shkiah (Sunset)", "שְׁקִיעַת הַחַמָּה", sunset),
        ("tzeit", "Havdalah / Tzeit HaKochavim" if dow == 5 else "Tzeit HaKochavim (Nightfall)", "צֵאת הַכּוֹכָבִים", tzeit),
        ("chatzot_lailah", "Chatzot HaLailah (Midnight)", "חֲצוֹת הַלַּיְלָה", chatzot_lailah),
    ]
    zmanim_list = []
    next_zman = None
    active_zman = None
    for key, en_lbl, he_lbl, zdt in zmanim_raw:
        if zdt is None:
            continue
        passed = now_local >= zdt
        if passed:
            active_zman = {"key": key, "name": en_lbl, "he": he_lbl, "time": _fmt_hm(zdt)}
        elif next_zman is None:
            mins_left = max(1, int(round((zdt - now_local).total_seconds() / 60.0)))
            hrs, rem_m = divmod(mins_left, 60)
            cd_str = f"{hrs}h {rem_m}m" if hrs else f"{rem_m}m"
            next_zman = {"key": key, "name": en_lbl, "he": he_lbl, "time": _fmt_hm(zdt), "in_minutes": mins_left, "countdown": cd_str}
        zmanim_list.append({
            "key": key,
            "name": en_lbl,
            "he": he_lbl,
            "time": _fmt_hm(zdt),
            "passed": passed,
        })

    # Determine Sacred Watch, Sky Mood, and OS Color Temp (Kelvin for hyprsunset)
    alt = sun["altitude_deg"]
    if alot and sunrise and alot <= now_local < sunrise:
        watch = {"en": "Alot HaShachar · Dawn Awakening", "he": "עֲלוֹת הַשַּׁחַר", "mood": "dawn", "kelvin": 4600}
    elif sunrise and chatzot and sunrise <= now_local < chatzot:
        watch = {"en": "Shacharit · Morning Illumination", "he": "שַׁחֲרִית", "mood": "morning", "kelvin": 6200}
    elif chatzot and plag_hamincha and chatzot <= now_local < plag_hamincha:
        watch = {"en": "Mincha · Afternoon Clarity", "he": "מִנְחָה", "mood": "midday", "kelvin": 5900}
    elif plag_hamincha and sunset and plag_hamincha <= now_local < sunset:
        watch = {"en": "Plag HaMincha · Golden Hour", "he": "פְּלַג הַמִּנְחָה", "mood": "golden", "kelvin": 4700}
    elif sunset and tzeit and sunset <= now_local < tzeit:
        watch = {"en": "Bein HaShmashot · Sacred Twilight", "he": "בֵּין הַשְּׁמָשׁוֹת", "mood": "twilight", "kelvin": 4000}
    else:
        watch = {"en": "Maariv · Starlight Sanctuary", "he": "מַעֲרִיב", "mood": "night", "kelvin": 3700}

    if is_shabbat:
        watch["en"] = "Shabbat Kodesh · Sanctuary Stillness"
        watch["he"] = "שַׁבָּת קֹדֶשׁ"
    elif is_motzaei_shabbat:
        watch["en"] = "Motzaei Shabbat · Shavua Tov"
        watch["he"] = "מוֹצָאֵי שַׁבָּת · שָׁבוּעַ טוֹב"

    # 24-hour Solar & Lunar Sky Arc (every 60 minutes from 00:00 to 24:00) for exact SVG Sky Dome plotting
    day_start = datetime.datetime(today.year, today.month, today.day, 0, 0, tzinfo=tz)
    sun_arc = []
    moon_arc = []
    for hr in range(0, 25):
        sdt = (day_start + datetime.timedelta(hours=hr)).astimezone(datetime.timezone.utc)
        sp = solar_position(sdt, lat, lon)
        mp = lunar_position(sdt, lat, lon)
        sun_arc.append({"hour": hr, "alt": sp["altitude_deg"], "az": sp["azimuth_deg"]})
        moon_arc.append({"hour": hr, "alt": mp["altitude_deg"], "az": mp["azimuth_deg"]})

    return {
        "timestamp_iso": now_local.isoformat(timespec="seconds"),
        "local_time": now_local.strftime("%H:%M"),
        "local_date_en": now_local.strftime("%A, %B %d, %Y"),
        "local_hour_float": round(now_local.hour + now_local.minute / 60.0, 3),
        "location": {
            "city": loc["city"],
            "lat": lat,
            "lon": lon,
            "tz": str(tz),
            "in_israel": in_israel,
        },
        "hebrew_date": he_date,
        "after_sunset": after_sunset,
        "after_tzeit": after_tzeit,
        "is_erev_shabbat": is_erev_shabbat,
        "is_shabbat": is_shabbat,
        "is_motzaei_shabbat": is_motzaei_shabbat,
        "shabbat_mode": shabbat_mode,
        "sun": sun,
        "moon": moon,
        "mizrach": mizrach,
        "watch": watch,
        "zmanim": zmanim_list,
        "active_zman": active_zman,
        "next_zman": next_zman,
        "shaah_zmanit_gra_min": round(shaah_gra / 60.0, 1),
        "year_context": year_ctx,
        "sun_arc": sun_arc,
        "moon_arc": moon_arc,
    }


if __name__ == "__main__":
    snap = get_sacred_moment()
    print(json.dumps({
        "local": f"{snap['local_date_en']} {snap['local_time']} ({snap['location']['city']})",
        "hebrew_date": snap["hebrew_date"]["en_str"] + " | " + snap["hebrew_date"]["he_str"],
        "after_sunset": snap["after_sunset"],
        "shabbat": {"is_shabbat": snap["is_shabbat"], "motzaei": snap["is_motzaei_shabbat"], "shabbat_mode": snap["shabbat_mode"]},
        "watch": snap["watch"],
        "sun": snap["sun"],
        "moon": snap["moon"],
        "mizrach": snap["mizrach"],
        "next_zman": snap["next_zman"],
        "zmanim": [(z["key"], z["time"]) for z in snap["zmanim"]],
        "tekufah": snap["year_context"]["tekufah"],
        "prayers": snap["year_context"]["prayers"],
        "kiddush_levana": snap["year_context"]["kiddush_levana"],
    }, ensure_ascii=False, indent=2))
