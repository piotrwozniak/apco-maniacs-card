"""Constants for the Warun integration."""

DOMAIN = "warun"

CONF_WEATHER_ENTITY = "weather_entity"
CONF_WIND_THRESHOLD = "wind_threshold"
CONF_PRECIP_THRESHOLD = "precip_threshold"
CONF_FORECAST_HOURS = "forecast_hours"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_LOCATION_NAME = "location_name"

CONF_LANGUAGE = "language"
DEFAULT_LANGUAGE = "pl"
DEFAULT_NAME = "Warun (legacy)"
DEFAULT_WIND_THRESHOLD = 5.0  # m/s
DEFAULT_PRECIP_THRESHOLD = 10  # %
DEFAULT_FORECAST_HOURS = 40

WIND_DIRECTIONS = [
    "N", "NNE", "NE", "ENE",
    "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW",
    "W", "WNW", "NW", "NNW",
]

TEXT = {
    "pl": {"now": "Teraz", "cloud": "chmury", "wind": "Wiatr", "humidity": "Wilgotność", "pressure": "Ciśnienie", "rain": "Opady", "no_rain": "brak opadów", "no_forecast": "Brak prognozy", "missing": "Brak danych", "good": "Warun", "bad": "Brak warunu", "yes": "OK", "no": "NIE", "days": ["pon.", "wt.", "śr.", "czw.", "pt.", "sob.", "niedz."]},
    "en": {"now": "Now", "cloud": "clouds", "wind": "Wind", "humidity": "Humidity", "pressure": "Pressure", "rain": "Precipitation", "no_rain": "no precipitation", "no_forecast": "No forecast", "missing": "No data", "good": "Flyable", "bad": "Not flyable", "yes": "OK", "no": "NO", "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
}
