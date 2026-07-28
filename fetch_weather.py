from typing import Any
import requests
import datetime
import inquirer # type: ignore[import-untyped]
from tabulate import tabulate

#API Url
BASE_URL: str = "https://api.open-meteo.com/v1/forecast"

# The weather data we want to collect
VARIABLE_LABEL: dict[str, str] = {
    "temperature_2m": "Temperature", 
    "relative_humidity_2m": "Humidity", 
    "cloud_cover": "Clouds", 
    "precipitation": "Precipitation", 
    "visibility": "Visibility"
    }

TIME_ZONE: str = "Asia/Taipei"

CURRENT_TIME: datetime.datetime = datetime.datetime.now()
CURRENT_HOUR: int = int(CURRENT_TIME.hour)

locations: dict[str, list[str]] = {
    "Taipei": ["25.0351", "121.507"],
    "Taichung": ["24.1477", "120.6736"],
    "Kaohsiung": ["22.62", "120.31"]
}


def prompt_location() -> str:
    questions = [
        inquirer.List(
            "location",
            message="Select your current location.",
            choices=["Taipei", "Taichung", "Kaohsiung"]
        )
    ]
    answers: dict[str, str] | None = inquirer.prompt(questions)
    if answers is None:
        raise KeyboardInterrupt("Location selection cancelled.")
    return answers['location']

def prompt_duration() -> int:
    duration = int(input("Set duration (hrs): "))
    if (CURRENT_HOUR + duration > 144):
        raise ValueError("No forecast data for more than 7 days.")
    return duration

def fetch_series(data: dict[str, list[int | float]], variable: str, duration: int) -> tuple[str, list[str | int | float]]:
    result: list[str | int | float] = [
        data[variable][CURRENT_HOUR + i] if (
            i < len(data[variable]) and data[variable][CURRENT_HOUR + i] is not None
        ) else "N/A"
        for i in range(duration)
    ]
    return (VARIABLE_LABEL[variable], result)

def forecast(latitude: str, longitude: str, duration: int) -> None:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(VARIABLE_LABEL.keys()),
        "timezone": TIME_ZONE,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout = 10)
        response.raise_for_status() # raise an exception when status code returned > 400
        data = response.json()

        # "hourly" is a dict in a dict called "data"
        hourly_data = data.get("hourly", {})   

        output: list = []
        headers: list[str] = [] + hourly_data.get("time", [])[CURRENT_HOUR : CURRENT_HOUR + duration]

        # Don't use append -- "<expr> for x in <expr>" is a generator expression, it will append a generator object in "output", braking the list
        # output.append(fetch_series(hourly_data, var, duration) for var in VARIABLE_LABEL.keys())

        # Use "extend" instead -- [fetch_series()...] first completes, then "extend" iterates through its items and append to "output"
        # extend(iterable) v.s. append(x)
        series: list[tuple[str, list[str | int | float]]] = [fetch_series(hourly_data, var, duration) for var in VARIABLE_LABEL.keys()]
        output.extend([[label] + row for label, row in series])

        print(tabulate(output, headers=headers, tablefmt="grid"))

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    location: str = prompt_location()
    duration: int = prompt_duration()

    LATITUDE: str = locations[location][0]
    LONGITUDE: str = locations[location][1]    
    forecast(LATITUDE, LONGITUDE, duration)