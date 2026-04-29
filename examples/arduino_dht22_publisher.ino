/*
 * Publicador MQTT para Arduino/ESP con sensor DHT22
 * ===================================================
 * 
 * Este código está diseñado para placas Arduino/ESP con:
 * - ESP32
 * - ESP8266
 * - Arduino con shield WiFi/Ethernet
 * 
 * Librerías requeridas (instalar desde Arduino Library Manager):
 * - DHT sensor library (por Adafruit)
 * - PubSubClient (por Nick O'Leary)
 * - WiFi (incluida en ESP32/ESP8266) o Ethernet (para Arduino)
 * - ArduinoJson (por Benoit Blanchon)
 * 
 * Conexiones DHT22:
 * - VCC  -> 3.3V o 5V
 * - DATA -> Pin definido en DHT_PIN
 * - GND  -> GND
 * - Resistencia 4.7kΩ entre DATA y VCC (si no viene en el módulo)
 */

#include <WiFi.h>          // Para ESP32/ESP8266
// #include <Ethernet.h>   // Para Arduino con shield Ethernet
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ============================================
// CONFIGURACIÓN - Ajustar según tu entorno
// ============================================

// Configuración WiFi
const char* WIFI_SSID = "tu_wifi_ssid";
const char* WIFI_PASSWORD = "tu_wifi_password";

// Configuración MQTT
const char* MQTT_BROKER = "192.168.1.100";  // IP del servidor con el middleware
const int MQTT_PORT = 1883;
const char* MQTT_USERNAME = "iot_user";      // Opcional, NULL si no requiere autenticación
const char* MQTT_PASSWORD = "iot_password";  // Opcional, NULL si no requiere autenticación
const char* MQTT_CLIENT_ID = "dht22_arduino_001";

// Configuración del sensor DHT22
#define DHT_TYPE DHT22
#define DHT_PIN 4  // Pin donde está conectado el sensor

// Configuración de tópicos MQTT
const char* MQTT_TOPIC_TEMPERATURE = "iot/proyecto_demo/casa_living/dht22_arduino/temperatura";
const char* MQTT_TOPIC_HUMIDITY = "iot/proyecto_demo/casa_living/dht22_arduino/humedad";

// Intervalo de lectura (milisegundos)
const unsigned long READ_INTERVAL = 30000;  // 30 segundos

// ============================================
// OBJETOS GLOBALES
// ============================================

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
DHT dht(DHT_PIN, DHT_TYPE);

unsigned long lastReadTime = 0;
int consecutiveErrors = 0;
const int MAX_ERRORS = 5;

// ============================================
// FUNCIONES
// ============================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("🚀 Iniciando publicador DHT22 MQTT (Arduino)...");
  Serial.printf("📌 Sensor: DHT22 en pin %d\n", DHT_PIN);
  Serial.printf("📌 Intervalo: %lu ms\n", READ_INTERVAL);
  
  // Inicializar sensor
  dht.begin();
  
  // Conectar WiFi
  connectWiFi();
  
  // Configurar cliente MQTT
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  
  // Conectar MQTT
  connectMQTT();
}

void loop() {
  // Mantener conexión MQTT
  if (!mqttClient.connected()) {
    Serial.println("⚠️  Desconectado de MQTT. Reconectando...");
    connectMQTT();
  }
  mqttClient.loop();
  
  // Leer y publicar datos según intervalo
  unsigned long currentTime = millis();
  if (currentTime - lastReadTime >= READ_INTERVAL) {
    lastReadTime = currentTime;
    readAndPublish();
  }
  
  delay(100);  // Pequeño delay para evitar sobrecarga
}

void connectWiFi() {
  Serial.print("Conectando a WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ Conectado a WiFi");
    Serial.print("   IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ Error conectando a WiFi");
  }
}

void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Conectando a MQTT broker: ");
    Serial.print(MQTT_BROKER);
    Serial.print(":");
    Serial.println(MQTT_PORT);
    
    if (mqttClient.connect(MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.println("✅ Conectado al broker MQTT");
      consecutiveErrors = 0;
    } else {
      Serial.print("❌ Error de conexión MQTT. Código: ");
      Serial.println(mqttClient.state());
      Serial.println("Reintentando en 5 segundos...");
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // Callback para mensajes recibidos (no usado en este caso)
  Serial.print("Mensaje recibido en: ");
  Serial.println(topic);
}

void readAndPublish() {
  // Leer sensor
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // Verificar si la lectura fue exitosa
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("⚠️  Error leyendo sensor DHT22");
    consecutiveErrors++;
    
    if (consecutiveErrors >= MAX_ERRORS) {
      Serial.println("❌ Demasiados errores. Reiniciando conexión...");
      WiFi.disconnect();
      delay(1000);
      connectWiFi();
      connectMQTT();
      consecutiveErrors = 0;
    }
    return;
  }
  
  // Obtener timestamp (epoch time)
  unsigned long timestamp = millis() / 1000;  // Simplificado, idealmente usar NTP
  
  // Publicar temperatura
  publishTemperature(temperature, timestamp);
  
  // Publicar humedad
  publishHumidity(humidity, timestamp);
  
  Serial.printf("✅ Datos publicados: Temp=%.2f°C, Hum=%.2f%%\n", temperature, humidity);
  consecutiveErrors = 0;
}

void publishTemperature(float temp, unsigned long ts) {
  // Crear JSON
  StaticJsonDocument<256> doc;
  doc["valor"] = round(temp * 100) / 100.0;  // Redondear a 2 decimales
  doc["unidad"] = "celsius";
  doc["timestamp"] = ts;
  doc["tipo"] = "temperatura";
  doc["sensor_id"] = MQTT_CLIENT_ID;
  
  JsonObject metadata = doc.createNestedObject("metadata");
  metadata["sensor_type"] = "DHT22";
  metadata["location"] = "living_room";
  metadata["pin"] = DHT_PIN;
  metadata["platform"] = "arduino";
  
  // Serializar JSON
  char payload[256];
  serializeJson(doc, payload);
  
  // Publicar
  if (mqttClient.publish(MQTT_TOPIC_TEMPERATURE, payload, true)) {
    Serial.printf("📤 Temperatura: %.2f°C\n", temp);
  } else {
    Serial.println("❌ Error publicando temperatura");
  }
}

void publishHumidity(float hum, unsigned long ts) {
  // Crear JSON
  StaticJsonDocument<256> doc;
  doc["valor"] = round(hum * 100) / 100.0;  // Redondear a 2 decimales
  doc["unidad"] = "porcentaje";
  doc["timestamp"] = ts;
  doc["tipo"] = "humedad";
  doc["sensor_id"] = MQTT_CLIENT_ID;
  
  JsonObject metadata = doc.createNestedObject("metadata");
  metadata["sensor_type"] = "DHT22";
  metadata["location"] = "living_room";
  metadata["pin"] = DHT_PIN;
  metadata["platform"] = "arduino";
  
  // Serializar JSON
  char payload[256];
  serializeJson(doc, payload);
  
  // Publicar
  if (mqttClient.publish(MQTT_TOPIC_HUMIDITY, payload, true)) {
    Serial.printf("📤 Humedad: %.2f%%\n", hum);
  } else {
    Serial.println("❌ Error publicando humedad");
  }
}
