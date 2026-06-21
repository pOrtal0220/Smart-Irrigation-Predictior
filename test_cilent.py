import requests

url = 'http://127.0.0.1:5000/predict'
test_payload = {"soil_moisture": 1200}

try:
    response = requests.post(url, json=test_payload)
    if response.status_code == 200:
        data = response.json()
        print(f"Server Response: {data['status']}")
        
        if data.get("total_liters_required", 0) > 0:
            print(f"Required Volume: {data['total_liters_required']} Liters")
            print(f"Predicted Irrigation Duration: {round(data['total_liters_required'] / 0.5, 2)} seconds")
        else:
            print("Reason:", data.get("reason", "No irrigation needed"))
    else:
        print(f"Server Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")