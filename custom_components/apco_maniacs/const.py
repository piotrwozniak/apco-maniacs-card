"""APCO Maniacs integration constants."""
DOMAIN = "apco_maniacs"
NAME = "APCO Maniacs"
DEFAULTS = {
    "name": NAME,
    "latitude": 53.531944,
    "longitude": 21.385556,
    "timezone": "Europe/Warsaw",
    "wind_threshold": 5.0,
    "precip_threshold": 10.0,
}
API_URL = "https://api.open-meteo.com/v1/forecast"
