#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverName = "http://your-flask-app-url.com/predict";

const int SOIL_PIN = 34; 
const int RELAY_PIN = 26; 

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW); 

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    int rawValue = analogRead(SOIL_PIN);
    
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    String httpRequestData = "{\"soil_moisture\":" + String(rawValue) + "}";
    
    int httpResponseCode = http.POST(httpRequestData);

    if (httpResponseCode > 0) {
      String response = http.getString();
      float duration = response.toFloat(); 
      
      if (duration > 0) {
        Serial.print("Actuating pump for: ");
        Serial.println(duration);
        
        digitalWrite(RELAY_PIN, HIGH); 
        delay(duration * 1000);        
        digitalWrite(RELAY_PIN, LOW);  
      }
    }
    http.end();
  }
  
  delay(3600000); 
}