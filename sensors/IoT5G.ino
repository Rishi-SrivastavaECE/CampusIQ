#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

const char* ssid="VITC-EVENT";
const char* password="Eve@07&08#$";

const char* mqtt_server="79a024032c3340f1b31ae7145332b97d.s1.eu.hivemq.cloud";
const int mqtt_port=8883;
const char* mqtt_user="campusiq";
const char* mqtt_pass="camPusiq@404";

const char* ROOM="KASTURBA HALL";

#define DHTPIN D3
#define DHTTYPE DHT22
#define MQ5_PIN D7
#define LDR_PIN A0
#define TRIG_PIN D5
#define ECHO_PIN D6

DHT dht(DHTPIN,DHTTYPE);
WiFiClientSecure espClient;
PubSubClient client(espClient);

void printWiFiInfo(){
Serial.println("----- WiFi Info -----");
Serial.print("SSID: ");Serial.println(WiFi.SSID());
Serial.print("IP: ");Serial.println(WiFi.localIP());
Serial.println("---------------------");
}

void printSensorData(float t,float h,int gas,int ldr,int power,long dist){
Serial.println("----- Sensor Data -----");
Serial.print("Temp: ");if(isnan(t))Serial.println("Error");else{Serial.print(t);Serial.println(" C");}
Serial.print("Humidity: ");if(isnan(h))Serial.println("Error");else{Serial.print(h);Serial.println(" %");}
Serial.print("Gas: ");Serial.println(gas==1?"UNSAFE":"SAFE");
Serial.print("LDR: ");Serial.println(ldr);
Serial.print("Power: ");Serial.print(power);Serial.println(" W");
Serial.print("Distance: ");Serial.print(dist);Serial.println(" cm");
Serial.println("-----------------------");
}

void setup_wifi(){
Serial.println("Connecting to WiFi...");
WiFi.mode(WIFI_STA);
WiFi.begin(ssid,password);
int attempts=0;
while(WiFi.status()!=WL_CONNECTED&&attempts<20){
delay(500);
Serial.print(".");
attempts++;
}
if(WiFi.status()==WL_CONNECTED){
Serial.println("\nWiFi Connected");
printWiFiInfo();
}else{
Serial.println("\nWiFi FAILED");
}
}

void reconnect(){
while(!client.connected()){
Serial.print("MQTT connecting...");
if(client.connect("ESP8266_A101",mqtt_user,mqtt_pass)){
Serial.println("connected");
}else{
Serial.print("failed, rc=");
Serial.println(client.state());
delay(2000);
}
}
}

void publishSensor(const char* sensor,float value){
StaticJsonDocument<128> doc;
doc["room"]=ROOM;
doc["sensor"]=sensor;
doc["value"]=value;
char buffer[128];
serializeJson(doc,buffer);
String topic=String("campus/")+ROOM+"/"+sensor;
client.publish(topic.c_str(),buffer);
}

long readUltrasonic(){
digitalWrite(TRIG_PIN,LOW);
delayMicroseconds(2);
digitalWrite(TRIG_PIN,HIGH);
delayMicroseconds(10);
digitalWrite(TRIG_PIN,LOW);
long duration=pulseIn(ECHO_PIN,HIGH,30000);
long distance=duration*0.034/2;
return distance;
}

void setup(){
Serial.begin(115200);
pinMode(MQ5_PIN,INPUT);
pinMode(TRIG_PIN,OUTPUT);
pinMode(ECHO_PIN,INPUT);
dht.begin();
randomSeed(analogRead(A0));
setup_wifi();
espClient.setInsecure();
client.setServer(mqtt_server,mqtt_port);
}

void loop(){
if(!client.connected())reconnect();
client.loop();

float t=dht.readTemperature();
float h=dht.readHumidity();

int gasDigital=digitalRead(MQ5_PIN);
int gasStatus=(gasDigital==LOW)?1:0;

int ldrValue=analogRead(LDR_PIN);
int powerValue=random(200,801);
long distance=readUltrasonic();

if(!isnan(t))publishSensor("temp",t);
if(!isnan(h))publishSensor("humidity",h);
publishSensor("gas",gasStatus);
publishSensor("ldr",ldrValue);
publishSensor("power",powerValue);
publishSensor("distance",distance);

printSensorData(t,h,gasStatus,ldrValue,powerValue,distance);

delay(5000);
}
