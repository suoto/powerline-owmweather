# type: ignore

# pylint: disable=bad-continuation

# vim:fileencoding=utf-8:noet
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import json
import os
import os.path as p
import time
import urllib.parse
from collections import namedtuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from powerline.lib.threaded import KwThreadedSegment
from powerline.lib.url import urllib_read  # pylint: disable=import-error

from .utils import getConditionIcon

_WeatherKey = namedtuple("Key", ["location_query", "units", "openweathermap_api_key"])

_HOME = os.environ["HOME"]
_CACHE = p.join(_HOME, ".cache", "powerline_weather")

_TEMPERATURE_UNITS_NAMES = {"C": "metric", "F": "imperial", "K": "standard"}

_TEMPERATURE_UNITS_REPRESENTATION = {
    "C": "",
    "F": "°F",
    "K": "K",
}


class WeatherSegment(KwThreadedSegment):
    update_interval = 5*60
    _state = {}

    @staticmethod
    def key(location_query, units="C", openweathermap_api_key=None, **kwargs):
        return _WeatherKey(location_query, units, openweathermap_api_key)

    def compute_state(self, key):
        self.debug("\n\n\n\n")
        location_query = key.location_query
        if location_query is None:
            location_query = self._fetch_location()

        os.makedirs(_CACHE, exist_ok=True)
        cache_filename = p.join(_CACHE, key.location_query.replace(",", "__"))

        try:
            cache = json.load(open(cache_filename))
            data = cache["data"]
            timestamp = cache["timestamp"]
            if timestamp + WeatherSegment.update_interval < time.time():
                data = None
        except (FileNotFoundError, json.JSONDecodeError):
            data = None
            timestamp = time.time()

        if data is None:
            timestamp = time.time()
            data = self._fetch_weather(
                location_query, key.units, key.openweathermap_api_key
            )

        json.dump({"data": data, "timestamp": timestamp}, open(cache_filename, "w"))

        self.debug("Weather is: {0}", data)
        return data, timestamp + WeatherSegment.update_interval - time.time()

    def render_one(
        self,
        state,
        pl,
        openweathermap_api_key=None,
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
        units="C",
    ):

        state, time_to_update = state

        if state:
            condition = state["condition"]
            icon_info = state["icon_info"]
            data_to_content = {
                "condition": {
                    "pre": pre_condition,
                    "post": post_condition,
                    "content": lambda: (
                        getConditionIcon(**icon_info)
                        if condition_as_icon
                        else condition
                    ),
                },
                "humidity": {
                    "pre": pre_humidity,
                    "post": post_humidity,
                    "content": lambda: humidity_format.format(
                        humidity=state[data_to_show]
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
                    "content": lambda: temp_format.format(temp=state[data_to_show])
                    + _TEMPERATURE_UNITS_REPRESENTATION[units],
                },
                "feels_like": {
                    "pre": pre_feels_like,
                    "post": post_feels_like,
                    "content": lambda: temp_format.format(temp=state[data_to_show])
                    + _TEMPERATURE_UNITS_REPRESENTATION[units],
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
                            "divider_highlight_group": "owmweather_divider",
                        }
                    )
                    segment = {
                        "contents": data["content"](),
                        "highlight_groups": [
                            "owmweather_{}".format(data_to_show),
                            "owmweather",
                        ],
                        "divider_highlight_group": "owmweather_divider",
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
                            "divider_highlight_group": "owmweather_divider",
                        }
                    )
                except KeyError:
                    pl.error("Got invalid data_to_show {0}, ignoring it.", data_to_show)

            #  segments.append(
            #      {
            #          "contents": " %d" % time_to_update,
            #          "highlight_groups": ["owmweather", "owmweather", "owmweather",],
            #          "divider_highlight_group": "owmweather_divider",
            #      }
            #  )
            return segments

    def _fetch_location(self):
        self.debug("Fetching location")
        location_request = Request(
            "https://ipapi.co/json", headers={"user-agent": "curl/7.64.0"}
        )
        try:
            location_response = (
                urlopen(location_request, timeout=10).read().decode("utf-8")
            )
            self.debug("location response: {0}", location_response)
        except HTTPError as exc:
            self.error("Error fetching location: {0}", exc)
            self.debug(
                "Using previous known location: {0}",
                WeatherSegment._state["prev_location_query"],
            )
            location_query = WeatherSegment._state["prev_location_query"]
        else:
            location_json = json.loads(location_response)
            location_query = "{}, {}".format(
                location_json["city"], location_json["country_code"]
            )
            WeatherSegment._state["prev_location_query"] = location_query
        return location_query

    def _fetch_weather(self, location_query, units, openweathermap_api_key):
        weather_url = "https://api.openweathermap.org/data/2.5/weather?q={}&units={}&appid={}".format(
            urllib.parse.quote(location_query),
            _TEMPERATURE_UNITS_NAMES.get(units, "metric"),
            openweathermap_api_key,
        )
        raw_response = urllib_read(weather_url)
        if not raw_response:
            self.error("Failed to get response")
            return None
        self.info("weather response: {0} {1}", raw_response, type(raw_response))
        try:
            weather_json = json.loads(raw_response)
            return {
                "condition": weather_json["weather"][0]["main"].lower(),
                "humidity": float(weather_json["main"]["humidity"]),
                "temp": float(weather_json["main"]["temp"]),
                "feels_like": float(weather_json["main"]["feels_like"]),
                "icon_info": {
                    "weather_id": weather_json["weather"][0]["id"],
                    "clouds": weather_json["clouds"]["all"],
                    "icon": weather_json["weather"][0]["icon"],
                },
                "updated": time.time(),
            }
        except (json.decoder.JSONDecodeError, KeyError, TypeError):
            self.error(
                "openweathermap returned malformed or unexpected response: {0}",
                raw_response,
            )
            return None


weather = WeatherSegment()
