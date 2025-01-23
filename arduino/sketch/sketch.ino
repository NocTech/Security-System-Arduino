#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>

// RFID Setup
#define RST_PIN 9
#define SS_PIN 10
MFRC522 rfid(SS_PIN, RST_PIN);

//Led Setup
const int redPin = 6;
const int yellowPin = 7;
const int greenPin = 8;

// Wi-Fi Credentials
const char *ssid = "";    // Replace with your Wi-Fi SSID
const char *password = ""; // Replace with your Wi-Fi password

// Server IP and port
const char *serverIP = "192.168.50.31";  // Replace with your Python API's IP
const int serverPort = 3000; // Replace with your Python API's port

WiFiClient client;

void setup() {
  Serial.begin(9600);
  SPI.begin();
  rfid.PCD_Init();
  // Set the LED pin as output
  pinMode(redPin, OUTPUT);
  pinMode(yellowPin, OUTPUT);
  pinMode(greenPin, OUTPUT);

  // Connect to Wi-Fi
  Serial.print("Connecting to Wi-Fi...");
  WiFi.begin(ssid, password);
  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startTime < 30000) {  // 30-second timeout
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWi-Fi connection failed. Restarting...");
  }
}

void loop() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    delay(50);
    return;
  }

  // Read and format UID
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (i > 0) uid += ":";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  Serial.println("Card UID: " + uid);

  // Connect to server and send UID
  if (client.connect(serverIP, serverPort)) {
    Serial.println("Connected to server!");
    // Send UID
    client.print(uid);

    // Wait for a response from the server
    unsigned long timeout = millis();
    while (!client.available() && millis() - timeout < 5000) {  // 5-second timeout
      delay(10);
    }

    if (client.available()) {
      String response = client.readString();
      Serial.println("Server Response: " + response);

      if (response == "User found") {
        rgbled("green");
      } else if (response == "User not found") {
        rgbled("red");
      }
    } else {
      Serial.println("No response from server.");
    }

    client.stop();
  } else {
    Serial.println("Connection to server failed.");
  }

  delay(3000);  // Adjust based on requirements
  rgbled("yellow");
}

void rgbled(String color) {
  if (color == "red") {
    Serial.println("LED RED");
    digitalWrite(redPin, HIGH);    // Turn LED on
    digitalWrite(yellowPin, LOW);  // Turn LED off
    digitalWrite(greenPin, LOW);   // Turn LED off
  } else if (color == "yellow") {
    Serial.println("LED YELLOW");
    digitalWrite(redPin, LOW);      // Turn LED off
    digitalWrite(yellowPin, HIGH);  // Turn LED on
    digitalWrite(greenPin, LOW);    // Turn LED off
  } else if (color == "green") {
    Serial.println("LED GREEN");
    digitalWrite(redPin, LOW);     // Turn LED off
    digitalWrite(yellowPin, LOW);  // Turn LED off
    digitalWrite(greenPin, HIGH);  // Turn LED on
  } else {
    Serial.println("Invalid color");
  }
}
