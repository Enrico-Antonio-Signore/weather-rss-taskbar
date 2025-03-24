from flask import Flask, Response
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
OPENWEATHER_API_KEY = "c261fa04a85ef65367fee878d0313041" 

@app.route('/weather_rss')
def weather_rss():
    # Ottieni posizione approssimativa con ipapi.co
    location = requests.get('https://ipapi.co/json/').json()
    lat, lon = location['latitude'], location['longitude']

    # Chiama l'API di OpenWeather
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"
    weather_data = requests.get(weather_url).json()

    # Crea un RSS fittizio
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Meteo Attuale"
    ET.SubElement(channel, "description").text = "Feed meteo generato da OpenWeather"

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = f"{weather_data['name']}: {weather_data['weather'][0]['description']}, {weather_data['main']['temp']}°C"
    ET.SubElement(item, "description").text = (
        f"Condizioni: {weather_data['weather'][0]['description']}\n"
        f"Temperatura: {weather_data['main']['temp']}°C\n"
        f"Umidità: {weather_data['main']['humidity']}%\n"
        f"Vento: {weather_data['wind']['speed']} km/h"
    )

    return Response(ET.tostring(rss), mimetype="application/xml")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
