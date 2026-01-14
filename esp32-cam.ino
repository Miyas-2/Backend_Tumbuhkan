#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>

// ============================================
// WiFi Credentials
// ============================================
const char* ssid = "ICT-LAB WORKSPACE";
const char* password = "ICTLAB2024";

// ============================================
// fastAPI Server Configuration
// ============================================
const char* fastAPIServerIP = "192.168.1.193";  
const int fastAPIServerPort = 8000;
String uploadEndpoint = "/api/v1/prediction/growth/detect";

// ============================================
// Upload Interval
// ============================================
const unsigned long UPLOAD_INTERVAL = 60000; // 1 menit (testing)
// const unsigned long UPLOAD_INTERVAL = 43200000; // 12 jam (production)
unsigned long lastUploadTime = 0;

// ============================================
// Web Server (Port 80)
// ============================================
WebServer server(80);

// ============================================
// Camera Pin Configuration (AI-Thinker)
// ============================================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ============================================
// Flash LED
// ============================================
#define FLASH_GPIO_NUM     4

// ============================================
// Global Variables
// ============================================
bool cameraInitialized = false;
int uploadCount = 0;

// ============================================
// SETUP
// ============================================
void setup() {
  Serial.begin(115200);
  Serial.println("\n╔════════════════════════════════════╗");
  Serial.println("║   ESP32-CAM Tumbuhkan v2.0        ║");
  Serial.println("╚════════════════════════════════════╝");
  
  // Flash LED OFF
  pinMode(FLASH_GPIO_NUM, OUTPUT);
  digitalWrite(FLASH_GPIO_NUM, LOW);

  // Connect WiFi
  connectWiFi();

  // Initialize Camera
  initCamera();

  // Setup endpoints
  server.on("/stream", HTTP_GET, handleStream);
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/status", HTTP_GET, handleStatus);
  server.begin();
  
  Serial.println("\n✅ ESP32-CAM Ready!");
  Serial.println("📹 Stream: http://" + WiFi.localIP().toString() + "/stream");
  Serial.println("📷 Capture: http://" + WiFi.localIP().toString() + "/capture");
  Serial.println("⏰ Auto-upload: Every 1 minute");
  Serial.println("═══════════════════════════════════\n");
}

// ============================================
// MAIN LOOP
// ============================================
void loop() {
  // Handle HTTP requests
  server.handleClient();

  // WiFi watchdog
  static unsigned long lastWiFiCheck = 0;
  if (millis() - lastWiFiCheck > 30000) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("⚠️ WiFi lost! Reconnecting...");
      connectWiFi();
    }
    lastWiFiCheck = millis();
  }

  // Auto-upload setiap 1 menit
  if (millis() - lastUploadTime >= UPLOAD_INTERVAL) {
    Serial.println("\n⏰ Auto-upload triggered");
    uploadPhotoTofastAPI();
    lastUploadTime = millis();
  }

  delay(10);
}


// ============================================
// WiFi CONNECTION
// ============================================
void connectWiFi() {
  Serial.println("🌐 Connecting to: " + String(ssid));

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(false);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.println("   IP: " + WiFi.localIP().toString());
    Serial.println("   Signal: " + String(WiFi.RSSI()) + " dBm");
  } else {
    Serial.println("\n❌ WiFi Failed! Restarting...");
    delay(5000);
    ESP.restart();
  }
}

// ============================================
// CAMERA INIT
// ============================================
void initCamera() {
  Serial.println("📷 Initializing Camera...");

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // Frame size
  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;   // 640x480
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_CIF;   // 400x296
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // Initialize
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Camera init failed: 0x%x\n", err);
    delay(3000);
    ESP.restart();
    return;
  }

  // Auto settings
  sensor_t* s = esp_camera_sensor_get();
  s->set_brightness(s, 0);
  s->set_contrast(s, 0);
  s->set_saturation(s, 0);
  s->set_whitebal(s, 1);
  s->set_awb_gain(s, 1);
  s->set_exposure_ctrl(s, 1);
  s->set_gain_ctrl(s, 1);
  s->set_hmirror(s, 0);
  s->set_vflip(s, 0);

  cameraInitialized = true;
  Serial.println("✅ Camera Ready!");
}

// ============================================
// ENDPOINT: /stream
// ============================================
void handleStream() {
  if (!cameraInitialized) {
    server.send(503, "text/plain", "Camera not ready");
    return;
  }

  Serial.println("📹 Client connected");
  
  WiFiClient client = server.client();
  
  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  server.sendContent(response);

  while (client.connected()) {
    // ⚠️ CEK AUTO-UPLOAD saat streaming
    if (millis() - lastUploadTime >= UPLOAD_INTERVAL) {
      Serial.println("⏰ Upload during stream");
      uploadPhotoTofastAPI();
      lastUploadTime = millis();
    }

    camera_fb_t* fb = esp_camera_fb_get();
    
    if (!fb) {
      delay(100);
      continue;
    }

    client.print("--frame\r\n");
    client.print("Content-Type: image/jpeg\r\n\r\n");
    client.write(fb->buf, fb->len);
    client.print("\r\n");

    esp_camera_fb_return(fb);
    
    delay(100); // 10 FPS
  }

  Serial.println("📹 Client disconnected");
}

// ============================================
// UPLOAD PHOTO TO fastAPI
// ============================================
void uploadPhotoTofastAPI() {
  if (!cameraInitialized || WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ Cannot upload (camera/wifi not ready)");
    return;
  }

  Serial.println("═══════════════════════════════════");
  Serial.println("📸 Capturing photo...");

  // Flash ON (optional, comment jika ganggu)
  digitalWrite(FLASH_GPIO_NUM, HIGH);
  delay(200);

  camera_fb_t* fb = esp_camera_fb_get();

  digitalWrite(FLASH_GPIO_NUM, LOW);

  if (!fb) {
    Serial.println("❌ Capture failed!");
    Serial.println("═══════════════════════════════════\n");
    return;
  }

  Serial.printf("✅ Photo: %d bytes\n", fb->len);

  // Upload to fastAPI
  HTTPClient http;
  String serverPath = "http://" + String(fastAPIServerIP) + ":" + String(fastAPIServerPort) + uploadEndpoint;

  Serial.println("📤 Uploading to: " + serverPath);

  http.begin(serverPath);
  http.setTimeout(20000);

  String boundary = "----ESP32CAM";
  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);

  String body = "--" + boundary + "\r\n";
  body += "Content-Disposition: form-data; name=\"file\"; filename=\"growth.jpg\"\r\n";
  body += "Content-Type: image/jpeg\r\n\r\n";

  String footer = "\r\n--" + boundary + "--\r\n";

  int totalLen = body.length() + fb->len + footer.length();

  uint8_t* buffer = (uint8_t*)malloc(totalLen);
  if (!buffer) {
    Serial.println("❌ Memory allocation failed!");
    esp_camera_fb_return(fb);
    http.end();
    Serial.println("═══════════════════════════════════\n");
    return;
  }

  memcpy(buffer, body.c_str(), body.length());
  memcpy(buffer + body.length(), fb->buf, fb->len);
  memcpy(buffer + body.length() + fb->len, footer.c_str(), footer.length());

  int httpCode = http.POST(buffer, totalLen);

  free(buffer);
  esp_camera_fb_return(fb);

  if (httpCode > 0) {
    Serial.printf("✅ Upload SUCCESS! Code: %d\n", httpCode);
    Serial.println("📩 Response: " + http.getString());
    uploadCount++;
  } else {
    Serial.printf("❌ Upload FAILED! Code: %d\n", httpCode);
    Serial.println("   Error: " + http.errorToString(httpCode));
  }

  http.end();
  
  Serial.printf("📊 Total uploads: %d\n", uploadCount);
  Serial.println("═══════════════════════════════════\n");
}

// ============================================
// HANDLE /capture - Single Image Capture
// ============================================
void handleCapture() {
  if (!cameraInitialized) {
    server.send(500, "text/plain", "Camera not initialized");
    return;
  }

  Serial.println("📷 Capture request received");

  // Capture photo
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Capture failed");
    server.send(500, "text/plain", "Capture failed");
    return;
  }

  Serial.printf("✅ Captured %d bytes\n", fb->len);

  // Send JPEG response
  server.sendHeader("Content-Type", "image/jpeg");
  server.sendHeader("Content-Disposition", "inline; filename=capture.jpg");
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send_P(200, "image/jpeg", (const char*)fb->buf, fb->len);

  esp_camera_fb_return(fb);
  Serial.println("📤 Image sent to client");
}

// ============================================
// HANDLE /status - ESP32-CAM Status
// ============================================
void handleStatus() {
  String json = "{";
  json += "\"status\":\"ok\",";
  json += "\"camera\":" + String(cameraInitialized ? "true" : "false") + ",";
  json += "\"wifi\":\"" + String(WiFi.status() == WL_CONNECTED ? "connected" : "disconnected") + "\",";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"rssi\":" + String(WiFi.RSSI()) + ",";
  json += "\"uploads\":" + String(uploadCount) + ",";
  json += "\"uptime\":" + String(millis() / 1000);
  json += "}";

  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
}