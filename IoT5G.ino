#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

const char* ssid = "VITC-EVENT";
const char* password = "Eve@07&08#$";

const char* mqtt_server = "79a024032c3340f1b31ae7145332b97d.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "campusiq";
const char* mqtt_pass = "camPusiq@404";

const char* ROOM = "A101";

#define DHTPIN D3
#define DHTTYPE DHT22
#define MQ5_PIN D7

DHT dht(DHTPIN, DHTTYPE);
WiFiClientSecure espClient;
PubSubClient client(espClient);

void setup_wifi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi FAILED");
  }
}


void reconnect() {
  while (!client.connected()) {
    Serial.print("MQTT connecting...");
    if (client.connect("ESP8266_A101", mqtt_user, mqtt_pass)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

void publishSensor(const char* sensor, float value) {
  StaticJsonDocument<128> doc;
  doc["room"] = ROOM;
  doc["sensor"] = sensor;
  doc["value"] = value;
  char buffer[128];
  serializeJson(doc, buffer);
  String topic = String("campus/") + ROOM + "/" + sensor;
  client.publish(topic.c_str(), buffer);
}

void setup() {
  Serial.begin(115200);
  pinMode(MQ5_PIN, INPUT);
  dht.begin();
  randomSeed(analogRead(A0));
  setup_wifi();
  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  float t = dht.readTemperature();
  float h = dht.readHumidity();

  int gasDigital = digitalRead(MQ5_PIN);
  int gasStatus = (gasDigital == LOW) ? 1 : 0;

  int powerValue = random(200, 801);

  if (!isnan(t)) publishSensor("temp", t);
  if (!isnan(h)) publishSensor("humidity", h);
  publishSensor("gas", gasStatus);
  publishSensor("power", powerValue);

  delay(5000);
}
