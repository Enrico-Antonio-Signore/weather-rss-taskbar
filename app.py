from flask import Flask, Response, request, render_template
import requests
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "c261fa04a85ef65367fee878d0313041")  # Usa variabile d'ambiente o fallback

@app.route('/weather_rss')
def weather_rss():
    try:
        # 1. Ottieni coordinate da parametri URL (se forniti dal frontend JS) o via IP
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            # Fallback: geolocalizzazione via IP
            location_data = requests.get('https://ipapi.co/json/', timeout=5).json()
            lat, lon = str(location_data['latitude']), str(location_data['longitude'])
            city = location_data.get('city', 'Località sconosciuta')
        else:
            # Reverse geocoding per ottenere il nome della città
            reverse_geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={OPENWEATHER_API_KEY}"
            geo_data = requests.get(reverse_geo_url, timeout=5).json()
            city = geo_data[0].get('name', 'Località sconosciuta') if geo_data else 'Località sconosciuta'

        # 2. Chiamata all'API OpenWeather
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"
        weather_data = requests.get(weather_url, timeout=5).json()

        # 3. Estrazione dati meteo (formato compatto per la taskbar)
        temp = weather_data['main']['temp']
        condition = weather_data['weather'][0]['description'].capitalize()
        
        # 4. Emoji compatte per la taskbar
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

    # 5. Generazione RSS ottimizzato per Windhawk (testo breve)
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Meteo Live"
    
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = f"{icon} {temp}°C | {condition}"  # Testo per la taskbar
    ET.SubElement(item, "description").text = f"{city}"  # Dettagli aggiuntivi

    return Response(ET.tostring(rss), mimetype="application/xml")

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
