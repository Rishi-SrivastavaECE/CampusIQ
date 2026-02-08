#include <ESP8266WiFi.h>
#include <PicoMQTT.h>
#include <DHT.h>

const char* ssid = "ESP_Sensor_Net";
const char* password = "password123";

#define DHTPIN D4
#define DHTTYPE DHT22
#define TRIG_PIN D5
#define ECHO_PIN D6
#define MQ5_DIGITAL_PIN D7
#define LDR_ANALOG_PIN A0

PicoMQTT::Server mqtt;
DHT dht(DHTPIN, DHTTYPE);

unsigned long lastPublish = 0;
const long publishInterval = 2000;

void setup() {
  Serial.begin(115200);
  
  // Flash LED to show system reset
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW); // LED ON
  delay(1000);
  digitalWrite(LED_BUILTIN, HIGH); // LED OFF

  // --- FORCE AP MODE FIX ---
  WiFi.mode(WIFI_AP); 
  // -------------------------

  bool result = WiFi.softAP(ssid, password);
  
  if(result == true) {
    Serial.println("AP Created Successfully!");
  } else {
    Serial.println("AP Creation Failed!");
  }

  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(MQ5_DIGITAL_PIN, INPUT);

  dht.begin();
  mqtt.begin();
}

void loop() {
  mqtt.loop();

  // Blink LED every time we publish (Visual heartbeat)
  if (millis() - lastPublish > publishInterval) {
    lastPublish = millis();
    
    // Blink LED briefly
    digitalWrite(LED_BUILTIN, LOW); 
    delay(50); 
    digitalWrite(LED_BUILTIN, HIGH);

    float h = dht.readHumidity();
    float t = dht.readTemperature();
    int light = analogRead(LDR_ANALOG_PIN);
    int gas = digitalRead(MQ5_DIGITAL_PIN);

    long duration, distance;
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    duration = pulseIn(ECHO_PIN, HIGH);
    distance = duration * 0.034 / 2;

    if (!isnan(t)) {
      mqtt.publish("home/livingroom/temp", String(t));
      mqtt.publish("home/livingroom/humidity", String(h));
    }
    mqtt.publish("home/livingroom/distance", String(distance));
    mqtt.publish("home/livingroom/light", String(light));
    mqtt.publish("home/livingroom/gas", String(gas));
    
    Serial.println("Data sent...");
  }
}