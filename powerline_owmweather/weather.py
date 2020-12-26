# type: ignore

import json
import time
import urllib.parse
from functools import lru_cache
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from powerline.lib.url import urllib_read  # pylint: disable=import-error

temp_units_names = {"C": "metric", "F": "imperial", "K": "standard"}

temp_units_representation = {
    "C": "°C",
    "F": "°F",
    "K": "K",
}

conditions_to_icon = (
    ("clear", "☀️"),
    ("clouds", "☁️"),
    ("haze|fog|mist", "🌫️"),
    ("rain|drizzle", "🌧️"),
    ("snow", "❄️"),
    ("thunder", "⚡"),
    ("tornado", "🌪️"),
)

#  {
#    "coord": {
#      "lon": -0.22,
#      "lat": 51.46
#    },
#    "weather": [
#      {
#        "id": 800,
#        "main": "Clear",
#        "description": "clear sky",
#        "icon": "01n"
#      }
#    ],
#    "base": "stations",
#    "main": {
#      "temp": 275.13,
#      "feels_like": 270.8,
#      "temp_min": 274.26,
#      "temp_max": 276.15,
#      "pressure": 1031,
#      "humidity": 64
#    },
#    "visibility": 10000,
#    "wind": {
#      "speed": 2.6,
#      "deg": 310
#    },
#    "clouds": {
#      "all": 6
#    },
#    "dt": 1608914771,
#    "sys": {
#      "type": 1,
#      "id": 1417,
#      "country": "GB",
#      "sunrise": 1608883541,
#      "sunset": 1608911783
#    },
#    "timezone": 0,
#    "id": 2643741,
#    "name": "Putney",
#    "cod": 200
#  }

state = {"prev_location_query": None}

_ICON_TRANSLATION_TABLE = {
    "01d": ("☀️", 1),  # clear sky day
    "01n": ("🌙️", 1), # clear sky night
    "02d": ("⛅️", 1), # few clouds day
    "02n": ("⛅️", 1), # few clouds night
    "03d": ("☁️", 3),  # scattered clouds day
    "03n": ("☁️", 3),  # scattered clouds night
    "04d": ("🌤️", 3),  # broken clouds day
    "04n": ("🌤️", 3),  # broken clouds night
    "09d": ("🌧️", 3),  # shower rain day
    "09n": ("🌧️", 3),  # shower rain night
    "10d": ("🌧️", 3),  # rain day
    "10n": ("🌧️", 3),  # rain night
    "11d": ("⛈️", 1),  # thunderstorm day
    "11n": ("⛈️", 1),  # thunderstorm night
    "13d": ("❄️", 1),  # snow day
    "13n": ("❄️", 1),  # snow night
    "50d": ("🌫️", 3),  # mist day
    "50n": ("🌫️", 3),  # mist night
}


def _translate_icon(icon):
    try:
        icon, width = _ICON_TRANSLATION_TABLE[icon]
        return icon.ljust(width)
    except KeyError:
        return icon


def _get_icon_for_condition(search_condition):
    search_condition = search_condition.lower()
    for condition, icon in conditions_to_icon:
        if condition in search_condition or search_condition in condition:
            return icon
    return search_condition


def _fetch_location(pl):
    pl.debug("Fetching location")
    location_request = Request(
        "https://ipapi.co/json", headers={"user-agent": "curl/7.64.0"}
    )
    try:
        location_response = urlopen(location_request, timeout=10).read().decode("utf-8")
        pl.debug("location response: {0}", location_response)
    except HTTPError as e:
        pl.error("Error fetching location: {0}", e)
        pl.debug("Using previous known location: {0}", state["prev_location_query"])
        location_query = state["prev_location_query"]
    else:
        location_json = json.loads(location_response)
        location_query = "{}, {}".format(
            location_json["city"], location_json["country_code"]
        )
        state["prev_location_query"] = location_query
    return location_query


def _fetch_weather(pl, location_query, units, openweathermap_api_key):
    weather_url = "https://api.openweathermap.org/data/2.5/weather?q={}&units={}&appid={}".format(
        urllib.parse.quote(location_query),
        temp_units_names.get(units, "metric"),
        openweathermap_api_key,
    )
    raw_response = urllib_read(weather_url)
    if not raw_response:
        pl.error("Failed to get response")
        return None
    pl.debug("weather response: {0}", raw_response)
    try:
        weather_json = json.loads(raw_response)
        return {
            "condition": weather_json["weather"][0]["main"].lower(),
            "humidity": float(weather_json["main"]["humidity"]),
            "temp": float(weather_json["main"]["temp"]),
            "feels_like": float(weather_json["main"]["feels_like"]),
            "icon": weather_json["weather"][0]["icon"],
        }
    except (json.decoder.JSONDecodeError, KeyError, TypeError):
        pl.error(
            "openweathermap returned malformed or unexpected response: {0}",
            raw_response,
        )
        return None


@lru_cache()
def _weather(
    pl,
    *,
    openweathermap_api_key,
    condition_as_icon=True,
    humidity_format="{humidity:.0f}",
    location_query=None,
    post_condition="",
    post_humidity="",
    post_location="",
    post_temp="",
    post_feels_like="",
    pre_condition=" ",
    pre_humidity=" ",
    pre_location=" ",
    pre_temp=" ",
    pre_feels_like=" ",
    show="temp",
    temp_format="{temp:.0f}",
    ttl=None,
    units="C",
    **kwargs
):
    pl.debug("_weather called with arguments {0}", locals())
    location_query = location_query or _fetch_location(pl)
    pl.debug("Fetching weather for {0}", location_query)
    weather_dict = _fetch_weather(pl, location_query, units, openweathermap_api_key)
    if weather_dict:
        condition = weather_dict["condition"]
        icon = weather_dict["icon"]
        #  pl.debug("Icon: {0}", icon)
        #  pl.debug("Icon: {0}", _translate_icon(icon))
        data_to_content = {
            "condition": {
                "pre": pre_condition,
                "post": post_condition,
                "content": lambda: (
                    #  _get_icon_for_condition(condition)
                    _translate_icon(icon)
                    if condition_as_icon
                    else condition
                ),
            },
            "humidity": {
                "pre": pre_humidity,
                "post": post_humidity,
                "content": lambda: humidity_format.format(
                    humidity=weather_dict[data_to_show]
                ),
            },
            "location": {
                "pre": pre_location,
                "post": post_location,
                "content": lambda: location_query,
            },
            "temp": {
                "pre": pre_temp,
                "post": post_temp,
                "content": lambda: temp_format.format(temp=weather_dict[data_to_show])
                + temp_units_representation[units],
            },
            "feels_like": {
                "pre": pre_feels_like,
                "post": post_feels_like,
                "content": lambda: temp_format.format(temp=weather_dict[data_to_show])
                + temp_units_representation[units],
            },
        }
        segments = []
        for data_to_show in map(str.strip, show.split(",")):
            try:
                data = data_to_content[data_to_show]
                segments.append(
                    {
                        "contents": data["pre"],
                        "highlight_groups": [
                            "owmweather_pre_{}".format(data_to_show),
                            "owmweather_{}".format(data_to_show),
                            "owmweather",
                        ],
                        "divider_highlight_group": "background:divider",
                    }
                )
                segment = {
                    "contents": data["content"](),
                    "highlight_groups": [
                        "owmweather_{}".format(data_to_show),
                        "owmweather",
                    ],
                    "divider_highlight_group": "background:divider",
                }
                pl.debug("Adding segment {0} for {1}", segment, data_to_show)
                segments.append(segment)
                segments.append(
                    {
                        "contents": data["post"],
                        "highlight_groups": [
                            "owmweather_post_{}".format(data_to_show),
                            "owmweather_{}".format(data_to_show),
                            "owmweather",
                        ],
                        "divider_highlight_group": "background:divider",
                    }
                )
            except KeyError:
                pl.error("Got invalid data_to_show {0}, ignoring it.", data_to_show)
        return segments


def weather(*args, **kwargs):
    try:
        ttl_in_minutes = kwargs.pop("ttl_in_minutes")
    except KeyError:
        ttl_in_minutes = 60
    if ttl_in_minutes == 0:
        return _weather(*args, ttl=time.time(), **kwargs)
    return _weather(*args, ttl=time.time() // (ttl_in_minutes * 60), **kwargs)
