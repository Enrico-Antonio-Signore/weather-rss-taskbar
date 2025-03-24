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
        # 1. GEOLOCALIZZAZIONE (parametri > GPS browser > IP)
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

        # Arrotondamento a 0.5 gradi e formattazione
        temp = round_to_half(weather_data['main']['temp'])
        temp_str = f"{int(temp)}°C" if temp.is_integer() else f"{temp}°C"
        
        condition = weather_data['weather'][0]['description'].capitalize()
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']
        icon = get_emoji(weather_data['weather'][0]['main'])

    except Exception as e:
        # Fallback
        city = "Roma"
        temp_str = "N/D"
        condition = "Dati non disponibili"
        icon = "❓"
        country = ""
        humidity = "N/D"
        wind_speed = "N/D"

    # 3. GENERAZIONE RSS
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    
    # Item principale (ottimizzato per taskbar)
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = f"{icon} {temp_str} | {condition[:20]}"
    ET.SubElement(item, "description").text = f"{city}, {country}" if country else city
    
    # Item esteso (per debug)
    debug_item = ET.SubElement(channel, "item")
    ET.SubElement(debug_item, "title").text = "Dettagli completi"
    ET.SubElement(debug_item, "description").text = (
        f"Posizione: {lat}, {lon}\n"
        f"Temperatura: {temp_str}\n"
        f"Condizioni: {condition}\n"
        f"Umidità: {humidity}%\n"
        f"Vento: {wind_speed} km/h"
    )

    xml_str = ET.tostring(rss, encoding='unicode', method='xml')
    return Response(f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}', mimetype="application/xml")

@app.route('/')
def homepage():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Meteo Live</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
            #weather { margin-top: 20px; padding: 15px; background: #f0f8ff; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>Meteo Live 🌦️</h1>
        <div id="weather">Caricamento in corso...</div>
        
        <script>
            function updateWeather(lat, lon) {
                fetch(`/weather_rss?lat=${lat}&lon=${lon}`)
                    .then(r => r.text())
                    .then(xml => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(xml, "text/xml");
                        const title = doc.querySelector('item > title').textContent;
                        const desc = doc.querySelector('item > description').textContent;
                        document.getElementById('weather').innerHTML = `
                            <h2>${title}</h2>
                            <p>${desc}</p>
                            <small>Coordinate: ${lat}, ${lon}</small>
                        `;
                    });
            }

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    pos => updateWeather(pos.coords.latitude, pos.coords.longitude),
                    err => {
                        console.error("Errore geolocalizzazione:", err);
                        fetch('/weather_rss')
                            .then(r => r.text())
                            .then(xml => {
                                document.getElementById('weather').innerHTML = 
                                    new DOMParser().parseFromString(xml, "text/xml")
                                        .querySelector('item > title').textContent;
                            });
                    }
                );
            } else {
                fetch('/weather_rss')
                    .then(r => r.text())
                    .then(xml => {
                        document.getElementById('weather').innerHTML = 
                            new DOMParser().parseFromString(xml, "text/xml")
                                .querySelector('item > title').textContent;
                    });
            }
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
