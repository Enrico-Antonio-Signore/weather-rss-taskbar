from flask import Flask, Response, request, render_template, jsonify
import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime

app = Flask(__name__)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "c261fa04a85ef65367fee878d0313041")  # Chiave API OpenWeatherMap

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

def round_to_half(temp):
    return round(float(temp) * 2) / 2

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
            reverse_geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={OPENWEATHER_API_KEY}"
            geo_data = requests.get(reverse_geo_url, timeout=3).json()
            city = geo_data[0].get('name', 'Posizione sconosciuta') if geo_data else 'Posizione sconosciuta'
            country = geo_data[0].get('country', '') if geo_data else ''

        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"
        weather_data = requests.get(weather_url, timeout=3).json()

        temp = round_to_half(weather_data['main']['temp'])
        temp_str = f"{int(temp)}°C" if temp.is_integer() else f"{temp}°C"
        condition = weather_data['weather'][0]['description'].capitalize()
        icon = get_emoji(weather_data['weather'][0]['main'])

    except Exception as e:
        print("Errore in /weather_rss:", str(e))  # Log dell'errore
        city = "Roma"
        temp_str = "N/D"
        condition = "Dati non disponibili"
        icon = "❓"
        country = ""

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = f"{icon} {temp_str} {condition[:20]}"
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

        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"
        print(f"URL richiesta: {forecast_url}")  # Log dell'URL della richiesta

        response = requests.get(forecast_url, timeout=10)  # Aumenta il timeout a 10 secondi
        print(f"Risposta API: {response.status_code}, {response.text}")  # Log della risposta

        if response.status_code != 200:
            return {'error': 'Errore nella richiesta API'}, 500

        forecast_data = response.json()

        daily_forecast = {}
        for item in forecast_data['list']:
            date = item['dt_txt'].split(' ')[0]  # Estrai solo la data (YYYY-MM-DD)
            if date not in daily_forecast:
                daily_forecast[date] = {
                    'temp_min': float(item['main']['temp_min']),
                    'temp_max': float(item['main']['temp_max']),
                    'condition': item['weather'][0]['description'].capitalize(),
                }
            else:
                daily_forecast[date]['temp_min'] = min(daily_forecast[date]['temp_min'], float(item['main']['temp_min']))
                daily_forecast[date]['temp_max'] = max(daily_forecast[date]['temp_max'], float(item['main']['temp_max']))

        # Converti il dizionario in una lista per i primi 5 giorni
        result = []
        for i, (date, data) in enumerate(daily_forecast.items()):
            if i >= 5:  # Limita a 5 giorni
                break
            result.append({
                'date': int(datetime.strptime(date, '%Y-%m-%d').timestamp()),
                'temp_min': round_to_half(data['temp_min']),
                'temp_max': round_to_half(data['temp_max']),
                'condition': data['condition'],
                'uv_index': 0  # UV Index non disponibile con questo endpoint
            })

        return {
            'city': forecast_data['city']['name'],
            'forecast': result
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
