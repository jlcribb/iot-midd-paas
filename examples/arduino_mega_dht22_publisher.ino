/*
 * Publicador MQTT para Arduino Mega 2560 con sensor DHT22
 * =========================================================
 * 
 * IMPORTANTE: Arduino Mega 2560 NO tiene WiFi nativo.
 * Necesitas uno de estos:
 * - Ethernet Shield (recomendado)
 * - WiFi Shield (Arduino WiFi Shield)
 * - Módulo ESP8266 como cliente WiFi (más económico)
 * 
 * Este código está configurado para Ethernet Shield.
 * Si usas WiFi Shield, descomenta la sección WiFi.
 * 
 * Librerías requeridas (instalar desde Arduino Library Manager):
 * - DHT sensor library (por Adafruit)
 * - PubSubClient (por Nick O'Leary)
 * - Ethernet (incluida en Arduino IDE) o WiFi (si usas WiFi Shield)
 * - ArduinoJson (por Benoit Blanchon) - versión 6.x
 * 
 * Conexiones DHT22:
 * - VCC  -> 5V
 * - DATA -> Pin 4 (ajustar si necesario)
 * - GND  -> GND
 * - Resistencia 4.7kΩ entre DATA y VCC (si no viene en el módulo)
 */

// ============================================
// OPCIÓN 1: ETHERNET SHIELD (Recomendado)
// ============================================
#include <Ethernet.h>
#include <EthernetClient.h>

// Configuración Ethernet (ajustar según tu red)
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };  // MAC address única
IPAddress ip(192, 168, 1, 50);  // IP estática (ajustar según tu red)
IPAddress gateway(192, 168, 1, 1);  // Gateway
IPAddress subnet(255, 255, 255, 0);  // Máscara de subred
IPAddress dns(8, 8, 8, 8);  // DNS (Google)

EthernetClient ethClient;

// ============================================
// OPCIÓN 2: WIFI SHIELD (Descomentar si usas WiFi Shield)
// ============================================
/*
#include <WiFi.h>
#include <WiFiClient.h>

const char* WIFI_SSID = "tu_wifi_ssid";
const char* WIFI_PASSWORD = "tu_wifi_password";

WiFiClient wifiClient;
*/

// ============================================
// LIBRERÍAS COMUNES
// ============================================
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ============================================
// CONFIGURACIÓN MQTT - AJUSTAR SEGÚN EL BROKER
// ============================================
const char* mqtt_server = "192.168.1.100";  // IP de tu broker MQTT (servidor del middleware)
const int mqtt_port = 1883;
const char* mqtt_user = "iot_user";         // Usuario MQTT (según config.yaml)
const char* mqtt_password = "iot_password"; // Contraseña MQTT (según config.yaml)
const char* mqtt_client_id = "arduino_mega_dht22_001";

// ============================================
// TÓPICOS MQTT - Formato del middleware
// ============================================
const char* topic_temp = "iot/proyecto_demo/casa_living/dht22_arduino/temperatura";
const char* topic_hum = "iot/proyecto_demo/casa_living/dht22_arduino/humedad";
const char* topic_status = "iot/proyecto_demo/casa_living/dht22_arduino/status";

// ============================================
// CONFIGURACIÓN DEL SENSOR DHT22
// ============================================
#define DHTPIN 4           // Pin donde conectaste el DHT22 (ajustar si necesario)
#define DHTTYPE DHT22      // Tipo de sensor
DHT dht(DHTPIN, DHTTYPE);

// ============================================
// VARIABLES GLOBALES
// ============================================
PubSubClient client(ethClient);  // Cambiar a wifiClient si usas WiFi Shield
// PubSubClient client(wifiClient);  // Descomentar si usas WiFi Shield

unsigned long lastMsg = 0;
const long interval = 30000;  // Enviar datos cada 30 segundos (ajustar según necesidad)

// ============================================
// FUNCIÓN: CONEXIÓN ETHERNET
// ============================================
void setup_ethernet() {
  Serial.println("Iniciando conexión Ethernet...");
  
  // Iniciar Ethernet con DHCP (recomendado)
  if (Ethernet.begin(mac) == 0) {
    Serial.println("⚠️  DHCP falló, usando IP estática...");
    Ethernet.begin(mac, ip, dns, gateway, subnet);
  }
  
  delay(1000);
  
  Serial.println("✅ Ethernet conectado");
  Serial.print("📡 Dirección IP: ");
  Serial.println(Ethernet.localIP());
  Serial.print("📡 Gateway: ");
  Serial.println(Ethernet.gatewayIP());
}

// ============================================
// FUNCIÓN: CONEXIÓN WiFi (si usas WiFi Shield)
// ============================================
/*
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando a WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("✅ WiFi conectado");
    Serial.print("📡 Dirección IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("");
    Serial.println("❌ Error conectando a WiFi");
  }
}
*/

// ============================================
// FUNCIÓN: CONEXIÓN MQTT
// ============================================
void reconnect() {
  while (!client.connected()) {
    Serial.print("🔄 Intentando conexión MQTT...");
    Serial.print("Broker: ");
    Serial.print(mqtt_server);
    Serial.print(":");
    Serial.println(mqtt_port);
    
    String clientId = mqtt_client_id;
    clientId += "-";
    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("✅ MQTT conectado");
      
      // Publicar estado online
      StaticJsonDocument<128> statusDoc;
      statusDoc["status"] = "online";
      statusDoc["timestamp"] = millis() / 1000;
      statusDoc["device"] = "arduino_mega_dht22";
      
      char statusMsg[128];
      serializeJson(statusDoc, statusMsg);
      client.publish(topic_status, statusMsg);
      
    } else {
      Serial.print("❌ Error, rc=");
      Serial.print(client.state());
      Serial.println(" Reintentando en 5 segundos...");
      delay(5000);
    }
  }
}

// ============================================
// FUNCIÓN: LEER SENSOR Y ENVIAR DATOS
// ============================================
void readAndSendData() {
  // Leer sensor
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  
  // Verificar lectura
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("⚠️ Error leyendo sensor DHT22");
    return;
  }
  
  // Obtener timestamp (epoch time en segundos)
  unsigned long timestamp = millis() / 1000;
  
  // ============================================
  // PREPARAR MENSAJE TEMPERATURA (formato del middleware)
  // ============================================
  StaticJsonDocument<256> tempDoc;
  tempDoc["valor"] = round(temperature * 100) / 100.0;  // Redondear a 2 decimales
  tempDoc["unidad"] = "celsius";
  tempDoc["timestamp"] = timestamp;
  tempDoc["tipo"] = "temperatura";
  tempDoc["sensor_id"] = "arduino_mega_01";
  
  JsonObject metadata = tempDoc.createNestedObject("metadata");
  metadata["sensor_type"] = "DHT22";
  metadata["location"] = "living_room";
  metadata["pin"] = DHTPIN;
  metadata["platform"] = "arduino_mega";
  
  char tempMsg[256];
  serializeJson(tempDoc, tempMsg);
  
  // ============================================
  // PREPARAR MENSAJE HUMEDAD (formato del middleware)
  // ============================================
  StaticJsonDocument<256> humDoc;
  humDoc["valor"] = round(humidity * 100) / 100.0;  // Redondear a 2 decimales
  humDoc["unidad"] = "porcentaje";
  humDoc["timestamp"] = timestamp;
  humDoc["tipo"] = "humedad";
  humDoc["sensor_id"] = "arduino_mega_01";
  
  JsonObject humMetadata = humDoc.createNestedObject("metadata");
  humMetadata["sensor_type"] = "DHT22";
  humMetadata["location"] = "living_room";
  humMetadata["pin"] = DHTPIN;
  humMetadata["platform"] = "arduino_mega";
  
  char humMsg[256];
  serializeJson(humDoc, humMsg);
  
  // ============================================
  // PUBLICAR DATOS
  // ============================================
  if (client.publish(topic_temp, tempMsg, true)) {  // true = retain
    Serial.print("📤 Temperatura enviada: ");
    Serial.print(temperature);
    Serial.println("°C");
  } else {
    Serial.println("❌ Error publicando temperatura");
  }
  
  if (client.publish(topic_hum, humMsg, true)) {  // true = retain
    Serial.print("📤 Humedad enviada: ");
    Serial.print(humidity);
    Serial.println("%");
  } else {
    Serial.println("❌ Error publicando humedad");
  }
  
  Serial.println("---");
}

// ============================================
// CONFIGURACIÓN INICIAL
// ============================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("========================================");
  Serial.println("🚀 Sistema DHT22 + MQTT - Arduino Mega");
  Serial.println("========================================");
  Serial.print("📌 Sensor DHT22 en pin: ");
  Serial.println(DHTPIN);
  Serial.print("📌 Intervalo de envío: ");
  Serial.print(interval / 1000);
  Serial.println(" segundos");
  Serial.print("📌 Broker MQTT: ");
  Serial.print(mqtt_server);
  Serial.print(":");
  Serial.println(mqtt_port);
  Serial.println("========================================");
  
  // Inicializar sensor
  dht.begin();
  Serial.println("✅ Sensor DHT22 inicializado");
  
  // Conectar Ethernet o WiFi
  setup_ethernet();
  // setup_wifi();  // Descomentar si usas WiFi Shield
  
  // Configurar cliente MQTT
  client.setServer(mqtt_server, mqtt_port);
  Serial.println("✅ Cliente MQTT configurado");
  
  Serial.println("========================================");
}

// ============================================
// LOOP PRINCIPAL
// ============================================
void loop() {
  // Mantener conexión Ethernet (si es necesario)
  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println("⚠️  Enlace Ethernet perdido. Reintentando...");
    setup_ethernet();
  }
  
  // Mantener conexión MQTT
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Enviar datos periódicamente
  unsigned long now = millis();
  if (now - lastMsg > interval) {
    lastMsg = now;
    readAndSendData();
  }
  
  delay(100);  // Pequeño delay para evitar sobrecarga
}
