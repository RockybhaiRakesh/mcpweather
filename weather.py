import os
import re
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def extract_city(text: str):
    match = re.search(r"in ([a-zA-Z\s]+)", text.lower())
    return match.group(1).strip() if match else None

def extract_day(text: str):
    text = text.lower()
    if "today" in text:
        return 0
    elif "tomorrow" in text:
        return 1
    elif "day after tomorrow" in text:
        return 2
    else:
        match = re.search(r"in (\d+) days", text)
        if match:
            return int(match.group(1))
    return None  # fallback to today if not found

def get_weather_for_day(city: str, day_offset: int = 0):
    if day_offset > 4:
        return "Sorry, I can only provide forecasts up to 5 days ahead."

    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={api_key}"
    res = requests.get(url).json()

    if "list" not in res:
        return f"Could not retrieve forecast for {city}."

    target_date = (datetime.utcnow() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
    forecasts = [item for item in res["list"] if item["dt_txt"].startswith(target_date)]

    if not forecasts:
        return f"No forecast found for {city} on {target_date}."

    avg_temp = sum(f["main"]["temp"] for f in forecasts) / len(forecasts)
    desc = forecasts[0]["weather"][0]["description"]

    label = ["Today's", "Tomorrow's", "Day after tomorrow's"]
    prefix = label[day_offset] if day_offset < len(label) else f"Weather on {target_date}"

    return f"{prefix} in {city}: {desc}, average temperature: {avg_temp:.1f}°C."

def get_forecast(city: str):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={api_key}"
    res = requests.get(url).json()

    if "list" not in res:
        return f"Could not retrieve forecast for {city}."

    daily_summary = {}
    for entry in res["list"]:
        date = entry["dt_txt"].split(" ")[0]
        if date not in daily_summary:
            daily_summary[date] = {
                "temps": [],
                "description": entry["weather"][0]["description"]
            }
        daily_summary[date]["temps"].append(entry["main"]["temp"])

    forecast_lines = [f"Weather forecast for {city}:"]
    for date, data in list(daily_summary.items())[:5]:
        min_temp = min(data["temps"])
        max_temp = max(data["temps"])
        forecast_lines.append(f"{date}: {data['description']}, {min_temp:.1f}°C - {max_temp:.1f}°C")

    return "\n".join(forecast_lines)
