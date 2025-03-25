from flask import Flask, Response, request, render_template, jsonify
import requests
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)
WEATHER_API_KEY = "534016f5b5f34a0ca29102123252503"  # Chiave API WeatherAPI

def get_emoji(weather_main):
    weather_icons = {
        'clear': '☀️',
        'clouds': '☁️',
        'rain': '🌧️',
        'thunderstorm': '⛈️',
        'snow': '❄️',
        'mist': '🌫️',
        'drizzle': '🌦️',
        'fog': '🌁'
    }
    return weather_icons.get(weather_main.lower(), '🌡️')

@app.route('/weather_rss')
def weather_rss():
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            location_data = requests.get('https://ipinfo.io/json', timeout=3).json()  # Usa ipinfo.io
            loc = location_data.get('loc', '44.0647,12.4692')  # Default: coordinate di Rimini
            lat, lon = loc.split(',')
            city = location_data.get('city', 'Posizione sconosciuta')
            country = location_data.get('country', '')
        else:
            reverse_geo_url = f"http://api.weatherapi.com/v1/search.json?key={WEATHER_API_KEY}&q={lat},{lon}"
            geo_data = requests.get(reverse_geo_url, timeout=3).json()
            city = geo_data[0].get('name', 'Posizione sconosciuta') if geo_data else 'Posizione sconosciuta'
            country = geo_data[0].get('country', '') if geo_data else ''

        weather_url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={lat},{lon}"
        weather_data = requests.get(weather_url, timeout=3).json()

        temp = weather_data['current']['temp_c']
        condition = weather_data['current']['condition']['text'].capitalize()
        icon = get_emoji(weather_data['current']['condition']['text'])

    except Exception as e:
        print("Errore in /weather_rss:", str(e))  # Log dell'errore
        city = "Roma"
        temp = "N/D"
        condition = "Dati non disponibili"
        icon = "❓"
        country = ""

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = f"{icon} {temp}°C {condition[:20]}"
    ET.SubElement(item, "description").text = f"{city}, {country}" if country else city

    xml_str = ET.tostring(rss, encoding='unicode', method='xml')
    return Response(f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}', mimetype="application/xml")

@app.route('/weather_forecast')
def weather_forecast():
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')

        if not lat or not lon:
            location_data = requests.get('https://ipinfo.io/json', timeout=3).json()  # Usa ipinfo.io
            loc = location_data.get('loc', '44.0647,12.4692')  # Default: coordinate di Rimini
            lat, lon = loc.split(',')

        forecast_url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={lat},{lon}&days=7&aqi=no&alerts=no"
        print(f"URL richiesta: {forecast_url}")  # Log dell'URL della richiesta

        response = requests.get(forecast_url, timeout=10)  # Aumenta il timeout a 10 secondi
        print(f"Risposta API: {response.status_code}, {response.text}")  # Log della risposta

        if response.status_code != 200:
            return {'error': 'Errore nella richiesta API'}, 500

        forecast_data = response.json()

        daily_forecast = []
        for day in forecast_data['forecast']['forecastday']:
            daily_forecast.append({
                'date': day['date'],
                'temp_min': day['day']['mintemp_c'],
                'temp_max': day['day']['maxtemp_c'],
                'condition': day['day']['condition']['text'],
                'icon': day['day']['condition']['icon']
            })

        return {
            'city': forecast_data['location']['name'],
            'forecast': daily_forecast
        }

    except Exception as e:
        print("Errore in /weather_forecast:", str(e))  # Log dell'errore completo
        return {'error': 'Impossibile recuperare i dati meteo.'}, 500

@app.route('/')
def homepage():
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
