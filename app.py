from flask import Flask, Response, request
import requests
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "c261fa04a85ef65367fee878d0313041")

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
    """Arrotonda la temperatura a multipli di 0.5"""
    return round(float(temp) * 2) / 2

@app.route('/weather_rss')
def weather_rss():
    try:
        # 1. GEOLOCALIZZAZIONE
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            location_data = requests.get('https://ipapi.co/json/', timeout=3).json()
            lat, lon = str(location_data['latitude']), str(location_data['longitude'])
            city = location_data.get('city', 'Posizione sconosciuta')
            country = location_data.get('country_name', '')
        else:
            reverse_geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={OPENWEATHER_API_KEY}"
            geo_data = requests.get(reverse_geo_url, timeout=3).json()
            city = geo_data[0].get('name', 'Posizione sconosciuta') if geo_data else 'Posizione sconosciuta'
            country = geo_data[0].get('country', '') if geo_data else ''

        # 2. DATI METEO
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"
        weather_data = requests.get(weather_url, timeout=3).json()

        # Arrotondamento e formattazione
        temp = round_to_half(weather_data['main']['temp'])
        temp_str = f"{int(temp)}°C" if temp.is_integer() else f"{temp}°C"
        
        condition = weather_data['weather'][0]['description'].capitalize()
        icon = get_emoji(weather_data['weather'][0]['main'])

    except Exception as e:
        # Fallback
        city = "Roma"
        temp_str = "N/D"
        condition = "Dati non disponibili"
        icon = "❓"
        country = ""

    # 3. GENERAZIONE RSS (senza barra "|")
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = f"{icon} {temp_str} {condition[:20]}"  # <-- Rimossa la barra "|"
    ET.SubElement(item, "description").text = f"{city}, {country}" if country else city

    xml_str = ET.tostring(rss, encoding='unicode', method='xml')
    return Response(f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}', mimetype="application/xml")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
