"""Validate Open-Meteo data and assess current conditions without HA dependencies."""
from math import isfinite
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

HOUR = 3600


def number(value):
    """JSON nulls, booleans and non-finite numbers are missing data."""
    return value if type(value) in (int, float) and isfinite(value) else None


def validate_settings(settings):
    """Validate both form input and saved configuration."""
    result = dict(settings)
    name = result.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 80:
        raise ValueError("name")
    result["name"] = name.strip()
    for key, low, high in (
        ("latitude", -90, 90), ("longitude", -180, 180),
        ("wind_threshold", 0.5, 30), ("precip_threshold", 0, 100),
    ):
        if number(result.get(key)) is None or not low <= result[key] <= high:
            raise ValueError(key)
    try:
        ZoneInfo(result["timezone"])
    except (KeyError, TypeError, ValueError, ZoneInfoNotFoundError) as err:
        raise ValueError("timezone") from err
    return result


def forecast_params(settings):
    """Use the same units and UTC timestamps as the standalone card."""
    return {
        "latitude": settings["latitude"], "longitude": settings["longitude"],
        "timezone": settings["timezone"], "timeformat": "unixtime",
        "wind_speed_unit": "ms", "temperature_unit": "celsius", "forecast_days": 5,
        "current": "temperature_2m,wind_speed_10m,wind_direction_10m",
        "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,precipitation_probability",
        "daily": "sunrise,sunset",
    }


def validate_forecast(payload, now):
    """Keep only bounded, finite data needed by the sensors and existing card normalizer."""
    if not isinstance(payload, dict):
        raise ValueError("Invalid forecast")
    for key in ("current_units", "hourly_units"):
        units = payload.get(key, {})
        if not isinstance(units, dict) or units.get("temperature_2m") != "°C" or units.get("wind_speed_10m") != "m/s":
            raise ValueError("Unexpected weather units")
    hourly, daily, current = (payload.get(key) for key in ("hourly", "daily", "current"))
    if not all(isinstance(part, dict) for part in (hourly, daily, current)):
        raise ValueError("Missing forecast sections")
    times = hourly.get("time")
    if not isinstance(times, list) or not 1 <= len(times) <= 144:
        raise ValueError("Missing hourly timestamps")
    if any(number(time) is None for time in times) or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("Invalid hourly timestamps")
    if not any(time <= now < time + HOUR for time in times):
        raise ValueError("Forecast does not cover the current hour")
    current_time = number(current.get("time"))
    if current_time is None or not 0 <= now - current_time < HOUR:
        raise ValueError("Stale current weather")
    clean_hourly = {"time": times[:]}
    for key in ("temperature_2m", "wind_speed_10m", "wind_direction_10m", "precipitation_probability"):
        values = hourly.get(key)
        if not isinstance(values, list) or len(values) != len(times):
            raise ValueError(f"Invalid hourly array: {key}")
        clean_hourly[key] = [number(value) for value in values]
    clean_daily = {}
    for key in ("sunrise", "sunset"):
        values = daily.get(key)
        if not isinstance(values, list) or not 1 <= len(values) <= 6:
            raise ValueError("Missing sunrise/sunset data")
        clean_daily[key] = [number(value) for value in values]
    if len(clean_daily["sunrise"]) != len(clean_daily["sunset"]):
        raise ValueError("Mismatched solar data")
    return {
        "current_units": {"temperature_2m": "°C", "wind_speed_10m": "m/s"},
        "hourly_units": {"temperature_2m": "°C", "wind_speed_10m": "m/s"},
        "current": {key: number(current.get(key)) for key in (
            "time", "temperature_2m", "wind_speed_10m", "wind_direction_10m",
        )},
        "hourly": clean_hourly, "daily": clean_daily,
    }


def current_values(forecast, now):
    """Combine current wind/temperature with the current hour's precipitation probability."""
    current, hourly = forecast["current"], forecast["hourly"]
    fresh = current["time"] is not None and 0 <= now - current["time"] < HOUR
    index = next((i for i, time in enumerate(hourly["time"]) if time <= now < time + HOUR), None)
    wind = current["wind_speed_10m"] if fresh else None
    precip = hourly["precipitation_probability"][index] if index is not None else None
    return {
        "temperature": current["temperature_2m"] if fresh else None,
        "wind": wind if wind is not None and wind >= 0 else None,
        "precipitation": precip if precip is not None and 0 <= precip <= 100 else None,
    }


def assessment(values, settings):
    """Match the card: thresholds are exclusive and missing data is never good."""
    wind, precip = values["wind"], values["precipitation"]
    if wind is None or precip is None:
        return "unknown"
    return "good" if wind < settings["wind_threshold"] and precip < settings["precip_threshold"] else "bad"
