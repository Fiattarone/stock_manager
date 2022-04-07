import os
import re
import requests
from twilio.rest import Client
from twilio.http.http_client import TwilioHttpClient
import datetime as dt
from datetime import timedelta

STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"
ALPHAVANTAGE_API_KEY: str
ALPHAVANTAGE_URL: str
NEWSAPI_API_KEY: str
NEWSAPI_URL: str
twilio_SID_key: str
twilio_auth: str


def cleanhtml(raw_html):
    cleantext = re.sub(CLEANR, '', raw_html)
    return cleantext


current_day = str(dt.datetime.now()).split(" ")[0]
yesterday = str(dt.datetime.today() - timedelta(1)).split(" ")[0]

alpha_parameters = {
    "function": "TIME_SERIES_DAILY",
    "interval": 1,
    "symbol": STOCK,
    "apikey": ALPHAVANTAGE_API_KEY
}

news_parameters = {
    "apiKey": NEWSAPI_API_KEY,
    "q": COMPANY_NAME,
    "from": current_day,
    "sortBy": "date"
}

response = requests.get(url=ALPHAVANTAGE_URL, params=alpha_parameters)
response.raise_for_status()

try:
    data = [float(response.json()["Time Series (Daily)"][current_day]["4. close"]),
            float(response.json()["Time Series (Daily)"][yesterday]["4. close"])]
except KeyError:
    day_before_yesterday = str(dt.datetime.today() - timedelta(2)).split(" ")[0]
    data = [float(response.json()["Time Series (Daily)"][yesterday]["4. close"]),
            float(response.json()["Time Series (Daily)"][day_before_yesterday]["4. close"])]

day_variance = (data[0]-data[1])/data[0]

if abs(day_variance) > .04:
    CLEANR = re.compile('<.*?>')
    symbol: str
    if day_variance > 0:
        symbol = "🔺"
    else:
        symbol = "🔻"
    print(f"Day variance is: {symbol}{round(abs(day_variance*100), 4)}%.")
    news_response = requests.get(url=NEWSAPI_URL, params=news_parameters)
    news_response.raise_for_status()
    symbol_pack = f"{symbol} {round(abs(day_variance*100), 4)}"
    for article in news_response.json()["articles"][0:3]:

        proxy_client = TwilioHttpClient()
        # proxy_client.session.proxies = {"https": os.environ["http-proxy"]}

        client = Client(twilio_SID_key, twilio_auth, http_client=proxy_client)
        message = client.messages.create(
            body=f"|\n\nTicker: {STOCK} {symbol_pack}%\n\nTitle: {str(article['title'])}\n\nAuthor: {str(article['author'])}\n\n"
                 f"Description:\n\"{cleanhtml(str(article['description']))}\"\n\nURL: {str(article['url'])}",
            from_="+14707307976",
            to="+18317373286"
        )
        print(message.status)

