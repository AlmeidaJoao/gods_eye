import json
import requests
import boto3
import os

from datetime import datetime

client = boto3.client("events")

def notifier(event, context):
    city = "Inhambane"
    params = {
        "q": city,
        "appid": os.getenv("OPEN_WEATHER_API_KEY"),
        "limit": 1
    }
    geo_data = requests.get(url=os.getenv("GEO_API_URL"), params=params).json()
    lat = geo_data[0]["lat"]
    lon = geo_data[0]["lon"]

    params = {
        "lat": lat,
        "lon": lon,
        "appid": os.getenv("OPEN_WEATHER_API_KEY")
    }
    weather_data = requests.get(url=os.getenv("OPEN_WEATHER_API_URL"), params=params).json()
    current_wind_speed = weather_data["wind"]["speed"]

    next_five_days_wind = []
    params = {
        "lat": lat,
        "lon": lon,
        "appid": os.getenv("OPEN_WEATHER_API_KEY")
    }
    # This API provides the 5 five days weather in 3 hours steps
    # It was the preferred option as it is free :)
    next_days_weather = requests.get(url=os.getenv("OPEN_WEATHER_API_DAILY_URL"), params=params).json()["list"]
    for i in range(0, len(next_days_weather), 8):
        next_five_days_wind.append(next_days_weather[i]["wind"]["speed"])

    next_five_days_wind.insert(0, current_wind_speed)
    responses = []
    # TODO: Create alerts types in a different file
    # TODO: Notify for today, tomorrow, after tomorrow

    event_buses = client.list_event_buses(
        NamePrefix="NotifierEvent",
        Limit=1
    )
    event_bus_name = event_buses["EventBuses"][0]["Arn"]

    for wind in next_five_days_wind:
        if wind > 2:
            # TODO: Adjust to send events on match with the alert types
            # Send data to event bus
            data = {
                "city": city,
                "wind_speed": wind
            }
            responses.append(client.put_events(
                Entries=[
                    {
                        "Time": datetime.now(),
                        "Source": "com.almeidadealmeida.godseye",
                        "Resources": [],
                        "DetailType": "weather",
                        "Detail": json.dumps(data),
                        "EventBusName": event_bus_name
                    }
                ]
            )
            )
            break
    return responses
