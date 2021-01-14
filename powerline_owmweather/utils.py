_ICON_TRANSLATION_TABLE = {
    "01d": ("", 2),  # clear sky day
    "01n": ("", 2),  # clear sky night
    "02d": ("", 2),  # few clouds day
    "02n": ("", 2),  # few clouds night
    "03d": ("", 2),  # scattered clouds day
    "03n": ("", 2),  # scattered clouds night
    "04d": ("", 2),  # broken clouds day
    "04n": ("", 2),  # broken clouds night
    "09d": ("", 2),  # shower rain day
    "09n": ("", 2),  # shower rain night
    "10d": ("", 2),  # rain day
    "10n": ("", 2),  # rain night
    "11d": ("", 2),  # thunderstorm day
    "11n": ("", 2),  # thunderstorm night
    "13d": ("", 2),  # snow day
    "13n": ("", 2),  # snow night
    "50d": ("", 2),  # mist day
    "50n": ("", 2),  # mist night
}

_WEATHER_GROUP_ICONS = {
    #  Group 2xx: Thunderstorm (11d/n)
    200: ("   ", "   "),  # 200 Thunderstorm thunderstorm with light rain
    201: ("   ", "   "),  # 201 Thunderstorm thunderstorm with rain
    202: ("   ", "   "),  # 202 Thunderstorm thunderstorm with heavy rain
    210: ("   ", "   "),  # 210 Thunderstorm light thunderstorm
    211: ("   ", "   "),  # 211 Thunderstorm thunderstorm
    212: ("   ", "   "),  # 212 Thunderstorm heavy thunderstorm
    221: ("   ", "   "),  # 221 Thunderstorm ragged thunderstorm
    230: ("   ", "   "),  # 230 Thunderstorm thunderstorm with light drizzle
    231: ("   ", "   "),  # 231 Thunderstorm thunderstorm with drizzle
    232: ("   ", "   "),  # 232 Thunderstorm thunderstorm with heavy drizzle
    #  Group 3xx: Drizzle
    300: ("   ", "   "),  # 300 Drizzle light intensity drizzle     09d
    301: ("   ", "   "),  # 301 Drizzle drizzle     09d
    302: ("   ", "   "),  # 302 Drizzle heavy intensity drizzle     09d
    310: ("   ", "   "),  # 310 Drizzle light intensity drizzle rain     09d
    311: ("   ", "   "),  # 311 Drizzle drizzle rain     09d
    312: ("   ", "   "),  # 312 Drizzle heavy intensity drizzle rain     09d
    313: ("   ", "   "),  # 313 Drizzle shower rain and drizzle     09d
    314: ("   ", "   "),  # 314 Drizzle heavy shower rain and drizzle     09d
    321: ("   ", "   "),  # 321 Drizzle shower drizzle     09d
    #  Group 5xx: Rain
    500: ("   ", "   "),  # 500     Rain     light rain     10d
    501: ("   ", "   "),  # 501     Rain     moderate rain     10d
    502: ("   ", "   "),  # 502     Rain     heavy intensity rain     10d
    503: ("   ", "   "),  # 503     Rain     very heavy rain     10d
    504: ("   ", "   "),  # 504     Rain     extreme rain     10d
    511: ("   ", "   "),  # 511     Rain     freezing rain     13d
    520: ("   ", "   "),  # 520     Rain     light intensity shower rain     09d
    521: ("   ", "   "),  # 521     Rain     shower rain     09d
    522: ("   ", "   "),  # 522     Rain     heavy intensity shower rain     09d
    531: ("   ", "   "),  # 531     Rain     ragged shower rain     09d
    #  Group 6xx: Snow
    600: ("   ", "   "),  # 600 Snow light snow 13d
    601: ("   ", "   "),  # 601 Snow Snow 13d
    602: ("   ", "   "),  # 602 Snow Heavy snow     13d
    611: ("   ", "   "),  # 611 Snow Sleet 13d
    612: ("   ", "   "),  # 612 Snow Light shower sleet 13d
    613: ("   ", "   "),  # 613 Snow Shower sleet 13d
    615: ("   ", "   "),  # 615 Snow Light rain and snow 13d
    616: ("   ", "   "),  # 616 Snow Rain and snow 13d
    620: ("   ", "   "),  # 620 Snow Light shower snow 13d
    621: ("   ", "   "),  # 621 Snow Shower snow 13d
    622: ("   ", "   "),  # 622 Snow Heavy shower snow 13d
    #  Group 7xx: Atmosphere
    701: ("   ", "   "),  # 701 Mist     mist     50d
    711: ("   ", "   "),  # 711 Smoke    Smoke  50d
    721: ("   ", "   "),  # 721 Haze     Haze      50d
    731: ("   ", "   "),  # 731 Dust     sand/dust whirls  50d
    741: ("   ", "   "),  # 741 Fog      fog      50d
    751: ("   ", "   "),  # 751 sand     sand      50d
    761: ("   ", "   "),  # 761 Dust     dust      50d
    762: ("   ", "   "),  # 762 Ash      volcanic  ash   50d
    771: ("   ", "   "),  # 771 Squall   squalls   50d
    781: ("   ", "   "),  # 781 Tornado  tornado   50d
    #  Group 800: Clear
    800: ("   ", "   "),  # 800 Clear clear sky 01d
    #  Group 80x: Clouds
    801: ("   ", "   "),  # 801 Clouds few clouds: 11-25%     02d
    802: ("   ", "   "),  # 802 Clouds scattered clouds: 25-50%     03d
    803: ("   ", "   "),  # 803 Clouds broken clouds: 51-84%     04d
    804: ("   ", "   "),  # 804 Clouds overcast clouds: 85-100%     04d
}


def getConditionIcon(icon, weather_id, clouds):
    daytime = icon[-1] == "d"
    try:
        # We only have 3 cloud icons, divide the cloud pct in 3 instead of
        # using the 4 indications
        if weather_id in (801, 802, 803, 804):
            if clouds < 33:
                result = "   " if daytime else "   "
            elif clouds < 66:
                result = "   " if daytime else "   "
            else:
                result = "   "
        else:
            result = (
                _WEATHER_GROUP_ICONS[weather_id][0]
                if daytime
                else _WEATHER_GROUP_ICONS[weather_id][1]
            )
        #  return "(%s) %s" % (weather_id, result.strip().ljust(2))
        return result.strip().ljust(2)
    except KeyError:
        pass
    try:
        result, width = _ICON_TRANSLATION_TABLE[icon]
        return result.ljust(width)
    except KeyError:
        return icon


