from flask import Flask, request, jsonify
import joblib
import numpy as np
import json
import os
import requests
from datetime import datetime

app = Flask(__name__)

try:
    model = joblib.load('irrigation_model.pkl')
    crop_encoder = joblib.load('crop_encoder.pkl')
    type_encoder = joblib.load('type_encoder.pkl')
    print("--- AI Systems Online (R2: 0.96) ---")
except Exception as e:
    print(f"Model Load Error: {e}")

groups = {
    'rice': 'wetland', 'maize': 'cereal', 'jute': 'cereal', 'cotton': 'cereal',
    'chickpea': 'legume', 'lentil': 'legume', 'banana': 'tropical', 'mango': 'orchard'
}


def get_growth_stage(sowing_date_str):
    sowing_date = datetime.strptime(sowing_date_str, '%Y-%m-%d')
    days_passed = (datetime.now() - sowing_date).days
    stage = 1 + (days_passed / 30.0)
    return min(4.0, max(1.0, stage))

def get_weather_forecast(config):
    API_KEY = config['api_key']
    LAT, LON = config['lat'], config['lon']
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
    
    res = requests.get(url).json()
    current = res['list'][0]
    
    weather_features = {
        'temp': current['main']['temp'],
        'humid': current['main']['humidity'],
        'wind': current['wind']['speed'],
        'rain_now': current.get('rain', {}).get('3h', 0) / 3 
    }
    
    future_blocks = res['list'][1:5]
    rain_probs = [block.get('pop', 0) for block in future_blocks]
    max_rain_prob = max(rain_probs) 
    
    return weather_features, max_rain_prob


@app.route('/predict', methods=['POST'])
def predict():
    try:
        sensor_data = request.get_json()
        soil_moisture = float(sensor_data['soil_moisture'])
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        crop_name = config['crop_name'].lower().strip()
        growth_stage = get_growth_stage(config['sowing_date'])
        category = groups.get(crop_name, 'cereal')
        
        weather, rain_risk = get_weather_forecast(config)
        
        if rain_risk > 0.75: 
            return jsonify({
                "status": "postponed",
                "reason": f"High rain probability ({int(rain_risk*100)}%) in next 12h.",
                "total_liters_required": 0
            })

        crop_enc = crop_encoder.transform([crop_name])[0]
        type_enc = type_encoder.transform([category])[0]

       
        sunlight = 10.0 if 6 <= datetime.now().hour <= 18 else 0.0
        
        features = np.array([[
            weather['temp'], weather['humid'], weather['rain_now'],
            soil_moisture, sunlight, weather['wind'],
            growth_stage, type_enc, crop_enc
        ]])
        
        prediction_mm = model.predict(features)[0]
        total_liters = round(prediction_mm * config['area_sq_meter'], 2)

        return jsonify({
            "status": "success",
            "prediction_mm": round(prediction_mm, 2),
            "total_liters_required": total_liters,
            "debug_info": {
                "das_stage": round(growth_stage, 2),
                "future_rain_risk": rain_risk,
                "humidity_percent": weather['humid'],
                "wind_speed_kmh": round(weather['wind'] * 3.6, 1),
                "current_temp": weather['temp']
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)