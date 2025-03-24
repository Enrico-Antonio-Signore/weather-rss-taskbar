from flask import Flask, Response, request
import requests
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "c261fa04a85ef65367fee878d0313041")

@app.route('/weather_rss')
def weather_rss():
    try:
        # Geolocalizzazione via IP o parametri
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            location_data = requests.get('https://ipapi.co/json/', timeout=5).json()
            lat, lon = str(location_data['latitude']), str(location_data['longitude'])
            city = location_data.get('city', 'Località sconosciuta')
        else:
            reverse_geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={OPENWEATHER_API_KEY}"
            geo_data = requests.get(reverse_geo_url, timeout=5).json()
            city = geo_data[0].get('name', 'Località sconosciuta') if geo_data else 'Località sconosciuta'

        # Chiamata API meteo
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"
        weather_data = requests.get(weather_url, timeout=5).json()

        # Estrazione dati
        temp = round(weather_data['main']['temp'], 1)
        condition = weather_data['weather'][0]['description'].capitalize()
        
        # Emoji per condizioni meteo
        weather_icons = {
            'clear': '☀️',
            'clouds': '☁️',
            'rain': '🌧️',
            'thunderstorm': '⛈️',
            'snow': '❄️',
            'mist': '🌫️'
        }
        icon = weather_icons.get(weather_data['weather'][0]['main'].lower(), '🌡️')

    except Exception as e:
        # Fallback in caso di errore
        city = "Roma"
        temp = "N/D"
        condition = "Dati non disponibili"
        icon = "❓"

    # Generazione RSS perfettamente formattato
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    item = ET.SubElement(channel, "item")
    
    # Titolo compatto per la taskbar (con emoji)
    ET.SubElement(item, "title").text = f"{icon} {temp}°C {condition}"
    ET.SubElement(item, "description").text = city

    # Formattazione XML corretta
    xml_str = ET.tostring(rss, encoding='unicode', method='xml')
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
    
    return Response(xml_str, mimetype="application/xml")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
