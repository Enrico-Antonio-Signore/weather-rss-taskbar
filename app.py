<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meteo Settimanale</title>
    <style>
        /* Stile moderno e pulito */
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background: linear-gradient(to right, #f79d00, #64b5f6);
            color: white;
            margin: 0;
            padding: 0;
        }
        h1 {
            font-size: 28px;
            margin-bottom: 20px;
        }
        #weather-container {
            margin: 20px auto;
            max-width: 600px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
        }
        .forecast {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
        }
        .day {
            background: rgba(255, 255, 255, 0.3);
            padding: 15px;
            border-radius: 8px;
            width: calc(50% - 20px);
            text-align: left;
            font-size: 16px;
            transition: transform 0.3s ease;
        }
        .day:hover {
            transform: scale(1.05);
        }
        .loading {
            font-size: 16px;
            margin-top: 10px;
            color: yellow;
        }
        .day-title {
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 5px;
        }
        .day-info {
            font-size: 14px;
        }
        .day-icon img {
            width: 50px;
            height: 50px;
        }
    </style>
</head>
<body>
    <h1>🌤️ Previsioni Meteo Settimanali</h1>
    <div id="weather-container">
        <p class="loading">Caricamento dati...</p>
        <div id="weather-display"></div>
        <div class="forecast" id="forecast-container"></div>
    </div>

    <script>
        function fetchForecast(lat, lon) {
            fetch(`/weather_forecast?lat=${lat}&lon=${lon}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Errore HTTP: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("Dati ricevuti:", data);

                    const container = document.getElementById("forecast-container");
                    container.innerHTML = ""; // Pulisci il contenitore

                    if (data.error) {
                        container.innerHTML = `<p>Errore nel caricamento delle previsioni.</p>`;
                        return;
                    }

                    document.querySelector(".loading").style.display = "none";
                    document.getElementById("weather-display").innerHTML = `<h2>${data.city}</h2>`;

                    data.forecast.forEach(day => {
                        const date = new Date(day.date).toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long' });

                        const dayDiv = document.createElement("div");
                        dayDiv.classList.add("day");
                        dayDiv.innerHTML = `
                            <div class="day-title">${date}</div>
                            <div class="day-icon"><img src="${day.icon}" alt="${day.condition}"></div>
                            <div class="day-info">Condizioni: ${day.condition}</div>
                            <div class="day-info">Min: ${day.temp_min}°C | Max: ${day.temp_max}°C</div>
                        `;
                        container.appendChild(dayDiv);
                    });
                })
                .catch(error => {
                    console.error("Errore nel caricamento delle previsioni:", error);
                    document.getElementById("forecast-container").innerHTML = `<p>Errore nel caricamento dei dati meteo.</p>`;
                });
        }

        function getLocationAndFetchForecast() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    position => {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        fetchForecast(lat, lon);
                    },
                    error => {
                        console.error("Errore nella geolocalizzazione:", error);
                        fetchForecast(44.0647, 12.4692); // Posizione di default (Rimini, Italia)
                    }
                );
            } else {
                fetchForecast(44.0647, 12.4692); // Posizione di default
            }
        }

        getLocationAndFetchForecast();
    </script>
</body>
</html>
