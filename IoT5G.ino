#include <DHT.h>

#define DHTPIN D3     
#define DHTTYPE DHT22 

#define TRIG_PIN D5   
#define ECHO_PIN D6   

#define MQ5_DIGITAL_PIN D7  
#define LDR_ANALOG_PIN A0   

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(MQ5_DIGITAL_PIN, INPUT);
  
  dht.begin();
  
  Serial.println("\n--- ESP8266 Sensor System Started ---");
  delay(2000);
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  long duration, distance;
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  duration = pulseIn(ECHO_PIN, HIGH);
  distance = duration * 0.034 / 2;

  int lightIntensity = analogRead(LDR_ANALOG_PIN);
  int gasAlarm = digitalRead(MQ5_DIGITAL_PIN);

  Serial.println("-----------------------------");

  Serial.print("Temperature: ");
  if (isnan(t)) Serial.print("Error");
  else Serial.print(t);
  Serial.println(" °C");

  Serial.print("Humidity:    ");
  if (isnan(h)) Serial.print("Error");
  else Serial.print(h);
  Serial.println(" %");

  Serial.print("Distance:    ");
  Serial.print(distance);
  Serial.println(" cm");

  Serial.print("Light Level: ");
  Serial.print(lightIntensity);
  Serial.println(" (0-1024)");

  Serial.print("Gas Status:  ");
  if (gasAlarm == LOW) {
    Serial.println("!!! DANGER - GAS DETECTED !!!");
  } else {
    Serial.println("Safe");
  }

  delay(1000);
}
