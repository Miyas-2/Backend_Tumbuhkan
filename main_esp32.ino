// ============================================================
//                         LIBRARY
// ============================================================
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include <Adafruit_ADS1X15.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <LiquidCrystal_I2C.h>

// ============================================================
//                      WIFI & MQTT
// ============================================================
const char* ssid = "Narzo 50";
const char* password = "";
const char* mqtt_server = "broker.mqtt.cool";

const char* topic_sensor    = "tumbuhkan/sensor/data";
const char* topic_control   = "tumbuhkan/relay/control";
const char* topic_status    = "tumbuhkan/relay/status";
const char* topic_calib_ph  = "tumbuhkan/ph/calibration";
const char* topic_calib_tds = "tumbuhkan/tds/calibration";

WiFiClient espClient;
PubSubClient client(espClient);

// ============================================================
//                          LCD
// ============================================================
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ============================================================
//                        PIN SETUP
// ============================================================
#define LDR_PIN       34
#define DHT_PIN       13
#define DS18B20_PIN   18
#define TRIG_PIN      19
#define ECHO_PIN      23
#define FLOW_PIN      35

#define PH_UP   14
#define AB_MIX  27
#define PH_DOWN 26
#define PUMP    25
#define FAN     33
#define LED     32

int relayPins[] = {PH_UP, AB_MIX, PH_DOWN, PUMP};
const char* relayNames[] = {"PH_UP","AB_MIX","PH_DOWN","PUMP"};

// ============================================================
//                       RELAY STATE
// ============================================================
bool ledState=false, fanState=false;
bool relayActive[4]={false};
unsigned long relayStart[4], relayDuration[4];

// ============================================================
//                      SENSOR OBJECT
// ============================================================
DHT dht(DHT_PIN, DHT22);
OneWire oneWire(DS18B20_PIN);
DallasTemperature ds(&oneWire);
Adafruit_ADS1115 ads;

#define PH_CH  1
#define TDS_CH 0

// ============================================================
//                     SENSOR VARIABLES
// ============================================================
// ---- pH calibration
float v4=2.0667, v7=1.7954, v9=1.5525;
float a,b,c;

// ---- TDS calibration
#define TDS_DEFAULT_M 400.0
#define TDS_DEFAULT_C 0.0
#define TDS_SAMPLES 15
float tdsBuffer[TDS_SAMPLES];
int tdsIndex=0;
float tdsDisplay = 0;
bool tdsCalibrated = false;



float v500=0, v1000=0;
bool got500=false, got1000=false;
float tds_m=1, tds_c=0;

// ---- sensor value
float tempAir, tempUdara, hum;
float pH, tds;
float vPH, vTDS;
int ldr;
float jarak;
float flowLpm=0;

// ============================================================
//                       FLOW SENSOR
// ============================================================
volatile int pulse=0;
unsigned long lastFlow=0;
void IRAM_ATTR countPulse(){ pulse++; }

// ============================================================
//                    MQTT CALLBACK
// ============================================================
void mqttCallback(char* topic, byte* payload, unsigned int length){
  StaticJsonDocument<512> doc;
  deserializeJson(doc, payload, length);

  // ===== RELAY CONTROL =====
  if(String(topic)==topic_control){
    if(doc.containsKey("LED")){
      ledState = String(doc["LED"]["state"])=="ON";
      digitalWrite(LED,ledState);
    }
    if(doc.containsKey("FAN")){
      fanState = String(doc["FAN"]["state"])=="ON";
      digitalWrite(FAN,fanState);
    }

    for(int i=0;i<4;i++){
      if(doc.containsKey(relayNames[i])){
        int dur = doc[relayNames[i]]["duration"];
        if(dur>0){
          digitalWrite(relayPins[i],HIGH);
          relayActive[i]=true;
          relayStart[i]=millis();
          relayDuration[i]=dur;
        }
      }
    }
    publishRelayStatus();
  }

  // ===== PH CALIBRATION =====
  if(String(topic)==topic_calib_ph){
    if(doc.containsKey("v4")) v4=doc["v4"];
    if(doc.containsKey("v7")) v7=doc["v7"];
    if(doc.containsKey("v9")) v9=doc["v9"];
    calibratePH();
  }

  // ===== TDS CALIBRATION =====
  if(String(topic)==topic_calib_tds){
    int ppm=doc["ppm"];
    float v=getTDSVoltageMedian();
    if(ppm==500){v500=v;got500=true;}
    if(ppm==1000){v1000=v;got1000=true;}
    if(got500&&got1000){
      tds_m=(1000.0-500.0)/(v1000-v500);
      tds_c=500.0-tds_m*v500;
    }
  }

    // ===== TDS FAST CALIBRATION =====
  if(String(topic) == topic_calib_tds){

    // --- FAST WAY (m & c) ---
    if(doc.containsKey("m") && doc.containsKey("c")){
      tds_m = doc["m"];
      tds_c = doc["c"];
      got500 = true;
      got1000 = true;

      Serial.println("[TDS] Fast calibration loaded:");
      Serial.printf("m = %.4f\n", tds_m);
      Serial.printf("c = %.4f\n", tds_c);
      return;
    }

    // --- LEGACY WAY (500 / 1000) ---
    int ppm = doc["ppm"];
    float v = getTDSVoltageMedian();

    if(ppm == 500){
      v500 = v;
      got500 = true;
    }
    if(ppm == 1000){
      v1000 = v;
      got1000 = true;
    }

    if(got500 && got1000){
      tds_m = (1000.0 - 500.0) / (v1000 - v500);
      tds_c = 500.0 - tds_m * v500;

      Serial.println("[TDS] 2-point calibration done:");
      Serial.printf("m = %.4f | c = %.4f\n", tds_m, tds_c);
    }
  }

}

// ============================================================
//                     MQTT CONNECT
// ============================================================
void reconnect(){
  while(!client.connected()){
    if(client.connect("ESP32-Tumbuhkan")){
      client.subscribe(topic_control);
      client.subscribe(topic_calib_ph);
      client.subscribe(topic_calib_tds);
      publishRelayStatus();
    } else delay(2000);
  }
}

// ============================================================
//                          SETUP
// ============================================================
void setup(){
  Serial.begin(115200);

  pinMode(TRIG_PIN,OUTPUT);
  pinMode(ECHO_PIN,INPUT);
  pinMode(LDR_PIN,INPUT);

  pinMode(LED,OUTPUT);
  pinMode(FAN,OUTPUT);
  for(int i=0;i<4;i++){
    pinMode(relayPins[i],OUTPUT);
    digitalWrite(relayPins[i],LOW);
  }

  pinMode(FLOW_PIN,INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(FLOW_PIN),countPulse,RISING);

  dht.begin();
  ds.begin();
  ads.begin();
  ads.setGain(GAIN_TWOTHIRDS);

  lcd.init();
  lcd.backlight();

  WiFi.begin(ssid,password);
  while(WiFi.status()!=WL_CONNECTED) delay(300);

  client.setServer(mqtt_server,1883);
  client.setCallback(mqttCallback);

  calibratePH();
}

// ============================================================
//                          LOOP
// ============================================================
void loop(){
  if(!client.connected()) reconnect();
  client.loop();

  // ----- relay timer -----
  for(int i=0;i<4;i++){
    if(relayActive[i] && millis()-relayStart[i]>=relayDuration[i]){
      digitalWrite(relayPins[i],LOW);
      relayActive[i]=false;
      publishRelayStatus();
    }
  }

  // ----- flow -----
  if(millis()-lastFlow>=1000){
    flowLpm=pulse/4.5;
    pulse=0;
    lastFlow=millis();
  }

  // ----- sensors -----
  ds.requestTemperatures();
  tempAir=ds.getTempCByIndex(0);
  hum=dht.readHumidity();
  tempUdara=dht.readTemperature();
  ldr=analogRead(LDR_PIN);

  jarak=getDistance();

  vPH=getVoltage(PH_CH);
  pH=a*vPH*vPH+b*vPH+c;

  vTDS=getTDSVoltageMedian();
  if(got500 && got1000){
  tds = tds_m * vTDS + tds_c;
  tdsCalibrated = true;
} else {
  // default sementara sebelum kalibrasi
  tds = TDS_DEFAULT_M * vTDS + TDS_DEFAULT_C;
  tdsCalibrated = false;
}

  showLCD();
  printSerial();
  publishSensor();

  delay(1000);
}

// ============================================================
//                     SENSOR FUNCTION
// ============================================================
float getDistance(){
  digitalWrite(TRIG_PIN,LOW); delayMicroseconds(2);
  digitalWrite(TRIG_PIN,HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN,LOW);
  long d=pulseIn(ECHO_PIN,HIGH,30000);
  return d==0? -1 : d*0.034/2;
}

float getVoltage(int ch){
  long sum=0;
  for(int i=0;i<10;i++) sum+=ads.readADC_SingleEnded(ch);
  return (sum/10.0/32767.0)*4.096;
}

float getTDSVoltageMedian(){
  tdsBuffer[tdsIndex++]=ads.readADC_SingleEnded(TDS_CH);
  delay(40);
  if(tdsIndex>=TDS_SAMPLES) tdsIndex=0;

  float s[TDS_SAMPLES];
  memcpy(s,tdsBuffer,sizeof(s));
  for(int i=0;i<TDS_SAMPLES-1;i++)
    for(int j=i+1;j<TDS_SAMPLES;j++)
      if(s[i]>s[j]){float t=s[i];s[i]=s[j];s[j]=t;}

  return (s[TDS_SAMPLES/2]/32767.0)*4.096;
}

// ============================================================
//                     PH CALIBRATION
// ============================================================
void calibratePH(){
  float A[3][3]={{v4*v4,v4,1},{v7*v7,v7,1},{v9*v9,v9,1}};
  float Y[3]={4.01,6.86,9.18};

  for(int i=0;i<3;i++){
    float d=A[i][i];
    for(int j=0;j<3;j++)A[i][j]/=d;
    Y[i]/=d;
    for(int k=0;k<3;k++){
      if(k!=i){
        float f=A[k][i];
        for(int j=0;j<3;j++)A[k][j]-=f*A[i][j];
        Y[k]-=f*Y[i];
      }
    }
  }
  a=Y[0]; b=Y[1]; c=Y[2];
}

// ============================================================
//                  LCD, SERIAL, MQTT
// ============================================================
void showLCD(){
  lcd.setCursor(0,0);
  lcd.print("                "); // clear line
  lcd.setCursor(0,0);
  lcd.printf("pH:%.2f TDS:%4.0f", pH, tds);

  lcd.setCursor(0,1);
  lcd.print("                "); // clear line
  lcd.setCursor(0,1);
  lcd.printf("T:%.1fC H:%3.0f%%", tempAir, hum);
}

void printSerial(){
  Serial.println("===== SENSOR DEBUG =====");
  Serial.printf("pH  : %.2f (V=%.4f)\n",pH,vPH);
  Serial.printf("TDS : %.0f ppm (V=%.4f)\n",tds,vTDS);
  Serial.printf("Air : %.2f C\n",tempAir);
  Serial.printf("Udara: %.2f C\n",tempUdara);
  Serial.printf("Hum : %.2f %%\n",hum);
  Serial.printf("LDR : %d\n",ldr);
  Serial.printf("Jarak: %.1f cm\n",jarak);
  Serial.printf("Flow: %.2f L/m\n",flowLpm);
  Serial.println("========================\n");
}

void publishSensor(){
  StaticJsonDocument<512> doc;
  doc["ph"]=pH;
  doc["ph_voltage"]=vPH;
  doc["tds"]=tds;
  doc["tds_voltage"]=vTDS;
  doc["temp_air"]=tempAir;
  doc["temp_udara"]=tempUdara;
  doc["humidity"]=hum;
  doc["ldr"]=ldr;
  doc["distance"]=jarak;
  doc["flow"]=flowLpm;

  char buf[512];
  serializeJson(doc,buf);
  client.publish(topic_sensor,buf);
}

void publishRelayStatus(){
  StaticJsonDocument<256> doc;
  doc["LED"]=ledState?"ON":"OFF";
  doc["FAN"]=fanState?"ON":"OFF";
  for(int i=0;i<4;i++)
    doc[relayNames[i]]=relayActive[i]?"ON":"OFF";

  char buf[256];
  serializeJson(doc,buf);
  client.publish(topic_status,buf,true);
}
