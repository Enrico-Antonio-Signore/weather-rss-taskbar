from flask import Flask, Response
import requests
import xml.etree.ElementTree as ET
import os

app = Flask(__name__)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "c261fa04a85ef65367fee878d0313041")  # Usa variabile d'ambiente o fallback

@app.route('/weather_rss')
def weather_rss():
    try:
        # 1. Ottieni coordinate geografiche automaticamente via IP
        location_data = requests.get('https://ipapi.co/json/', timeout=5).json()
        lat, lon = str(location_data['latitude']), str(location_data['longitude'])
        city = location_data.get('city', 'Località sconosciuta')
        country = location_data.get('country_name', '')

        # 2. Chiamata all'API OpenWeather
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"
        weather_data = requests.get(weather_url, timeout=5).json()

        # 3. Estrazione dati meteo
        temp = weather_data['main']['temp']
        condition = weather_data['weather'][0]['description'].capitalize()
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']
        
        # 4. Emoji per condizioni meteo
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

    # 5. Generazione RSS
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = f"Meteo attuale a {city}"
    
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = f"{icon} {city}: {temp}°C, {condition}"
    ET.SubElement(item, "description").text = (
        f"📍 {city}, {country}\n"
        f"{icon} Condizioni: {condition}\n"
        f"🌡 Temperatura: {temp}°C\n"
        f"💧 Umidità: {humidity}%\n"
        f"🌬 Vento: {wind_speed} km/h"
    )

    return Response(ET.tostring(rss), mimetype="application/xml")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
