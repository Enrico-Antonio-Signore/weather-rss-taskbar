from flask import Flask, Response, request, render_template_string
import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta

app = Flask(__name__)
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "c261fa04a85ef65367fee878d0313041")

def get_emoji(weather_main):
    icons = {
        'clear': '☀️',
        'clouds': '☁️',
        'rain': '🌧️',
        'thunderstorm': '⛈️',
        'snow': '❄️',
        'mist': '🌫️',
        'drizzle': '🌦️',
        'fog': '🌁'
    }
    return icons.get(weather_main.lower(), '🌡️')

def round_to_half(temp):
    return round(float(temp) * 2) / 2

def get_daily_forecast(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"
    response = requests.get(url, timeout=5)
    data = response.json()
    
    daily_data = {}
    for item in data['list']:
        date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
        if date not in daily_data:
            daily_data[date] = {
                'temp_min': item['main']['temp_min'],
                'temp_max': item['main']['temp_max'],
                'conditions': [],
                'icon': get_emoji(item['weather'][0]['main']),
                'humidity': item['main']['humidity'],
                'wind': item['wind']['speed']
            }
        daily_data[date]['conditions'].append(item['weather'][0]['description'])
    
    # Prendi i prossimi 7 giorni
    forecast = []
    for i in range(7):
        day = datetime.now() + timedelta(days=i)
        date_str = day.strftime('%Y-%m-%d')
        if date_str in daily_data:
            day_data = daily_data[date_str]
            forecast.append({
                'date': day.strftime('%a %d %b'),
                'icon': day_data['icon'],
                'temp_min': round_to_half(day_data['temp_min']),
                'temp_max': round_to_half(day_data['temp_max']),
                'condition': max(set(day_data['conditions']), key=day_data['conditions'].count),
                'humidity': day_data['humidity'],
                'wind': day_data['wind']
            })
    
    return forecast

@app.route('/')
def homepage():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meteo 7 Giorni</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #4361ee;
                --secondary: #3f37c9;
                --light: #f8f9fa;
                --dark: #212529;
                --success: #4cc9f0;
                --warning: #f8961e;
                --danger: #f72585;
            }
            
            body {
                font-family: 'Roboto', sans-serif;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                color: var(--dark);
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                padding: 30px;
                backdrop-filter: blur(5px);
            }
            
            h1 {
                color: var(--primary);
                text-align: center;
                margin-bottom: 30px;
                font-weight: 500;
            }
            
            .current-weather {
                background: white;
                border-radius: 12px;
                padding: 25px;
                margin-bottom: 30px;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
            }
            
            .current-temp {
                font-size: 3.5rem;
                font-weight: 300;
                margin: 10px 0;
                color: var(--primary);
            }
            
            .current-condition {
                font-size: 1.5rem;
                margin: 5px 0;
            }
            
            .current-location {
                font-size: 1.2rem;
                opacity: 0.8;
                margin-bottom: 15px;
            }
            
            .current-details {
                display: flex;
                gap: 20px;
                margin-top: 15px;
            }
            
            .detail-item {
                display: flex;
                align-items: center;
                gap: 5px;
                font-size: 0.9rem;
            }
            
            .forecast {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                gap: 15px;
            }
            
            .forecast-day {
                background: white;
                border-radius: 10px;
                padding: 15px;
                text-align: center;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
                transition: transform 0.3s, box-shadow 0.3s;
            }
            
            .forecast-day:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            }
            
            .day-name {
                font-weight: 500;
                margin-bottom: 10px;
                color: var(--secondary);
            }
            
            .day-icon {
                font-size: 2rem;
                margin: 5px 0;
            }
            
            .day-temp {
                display: flex;
                justify-content: center;
                gap: 10px;
                margin: 10px 0;
            }
            
            .temp-max {
                color: var(--danger);
                font-weight: 500;
            }
            
            .temp-min {
                color: var(--primary);
                opacity: 0.7;
            }
            
            .day-condition {
                font-size: 0.8rem;
                opacity: 0.8;
                margin-top: 5px;
            }
            
            .loading {
                text-align: center;
                padding: 50px;
                font-size: 1.2rem;
                color: var(--primary);
            }
            
            @media (max-width: 768px) {
                .forecast {
                    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
                }
                
                .current-temp {
                    font-size: 2.5rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Previsioni Meteo 7 Giorni</h1>
            
            <div id="current-weather" class="current-weather">
                <div class="loading">Caricamento dati meteo...</div>
            </div>
            
            <div class="forecast" id="forecast-container">
                <!-- Forecast days will be inserted here by JavaScript -->
            </div>
        </div>

        <script>
            async function loadWeather() {
                try {
                    // Ottieni posizione
                    const position = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject);
                    });
                    
                    const { latitude: lat, longitude: lon } = position.coords;
                    
                    // Carica dati meteo attuali
                    const currentResponse = await fetch(`/weather_rss?lat=${lat}&lon=${lon}`);
                    const currentXml = await currentResponse.text();
                    const parser = new DOMParser();
                    const currentDoc = parser.parseFromString(currentXml, "text/xml");
                    
                    const currentTitle = currentDoc.querySelector('item > title').textContent;
                    const currentDesc = currentDoc.querySelector('item > description').textContent;
                    
                    // Estrai dati dalla stringa (formato: "☀️ 23°C Sereno")
                    const currentMatch = currentTitle.match(/(.{1,3}) ([0-9.]+°C) (.+)/);
                    
                    // Carica previsioni 7 giorni
                    const forecastResponse = await fetch(`/forecast?lat=${lat}&lon=${lon}`);
                    const forecast = await forecastResponse.json();
                    
                    // Aggiorna UI
                    document.getElementById('current-weather').innerHTML = `
                        <div class="current-icon">${currentMatch[1]}</div>
                        <div class="current-temp">${currentMatch[2]}</div>
                        <div class="current-condition">${currentMatch[3]}</div>
                        <div class="current-location">${currentDesc}</div>
                        <div class="current-details">
                            <
