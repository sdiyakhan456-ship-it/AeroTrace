import os
import requests
import pandas as pd

OPENAQ_API_KEY = os.environ["OPENAQ_API_KEY"]

SENSOR_ID = 12234787

url = f"https://api.openaq.org/v3/sensors/{SENSOR_ID}/measurements"

headers = {
    "X-API-Key": OPENAQ_API_KEY
}

params = {
    "limit": 1000
}

response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=30
)

response.raise_for_status()

data = response.json()["results"]

df = pd.DataFrame(data)

print("Records fetched:", len(df))
print(df.head())

df.to_csv("openaq_pm25_historical.csv", index=False)

print("CSV created successfully.")
