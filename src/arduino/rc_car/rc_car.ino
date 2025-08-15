// This code translates the output label from the model
// into instructions to move the rc car. It connects to a 
// wifi network. Each input will run the car for 500ms.

#include <SPI.h>
#include <WiFiNINA.h>

// arduino wifi chip credentials 
const char ssid[] = "SSID";  
const char pass[] = "PASSWORD";

// For powering wheels - channel A
const int drivePower = 9;
const int rearLDirection = 11;
const int rearRDirection = 8;

// For steering the car - channel B
const int steeringPower = 10;
const int frontLDirection = 12;
const int frontRDirection = 13;

// bool lastMovedFwd = false;

// set duration for how long each rc-car action should take (default is 500ms)
int timeSteps = 500;

// Telnet server on port 23
WiFiServer telnetServer(23);  
WiFiClient telnetClient;

// initialize variables and initiate the server
void setup() {

  pinMode(drivePower, OUTPUT);
  pinMode(rearLDirection, OUTPUT);
  pinMode(rearRDirection, OUTPUT);

  pinMode(steeringPower, OUTPUT);
  pinMode(frontLDirection, OUTPUT);
  pinMode(frontRDirection, OUTPUT);

  stop();

  // digitalWrite(drivePower, LOW);
  // digitalWrite(rearLDirection, LOW);
  // digitalWrite(rearRDirection, LOW);

  // digitalWrite(steeringPower, LOW);
  // digitalWrite(frontLDirection, LOW);
  // digitalWrite(frontRDirection, LOW);

  Serial.begin(9600);
  while (!Serial);

  // Connect to WiFi
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  while (WiFi.status() != WL_CONNECTED) {
    Serial.println("\tAttempting to reach access point");
    WiFi.begin(ssid, pass);
    delay(5000);
  }

  Serial.println("Connected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());  // Print assigned IP

  Serial.print("Signal Strength (RSSI): ");
  Serial.print(int(WiFi.RSSI()));
  Serial.println(" dBm");

  // Serial.begin(9600);
  // while (!Serial);

  // Serial.println("Starting BAM to RC-Car Access Point...");
  
  // WiFi.beginAP(ssid, pass);
  // Serial.println("Access Point Started!");

  // Serial.print("IP Address: ");
  // Serial.println(WiFi.localIP());

  telnetServer.begin();
}

int receiveInput() {

  // Check for new clients, request must be in the form: 
  // echo "123" | nc 192.168.4.1 23
  WiFiClient newClient = telnetServer.available();
  int arduinoCmd = -1;
  String receivedData = "";  // Buffer to store received data
  
  if (newClient) {
    if (telnetClient) {
      telnetClient.stop();  // Disconnect previous client
      Serial.println("Disconnected previous Telnet client.");
    }

    telnetClient = newClient;
    Serial.println("New Telnet client connected.");
    // telnetClient.println("Welcome! Send a number to echo it back.");
  }

  // If connected, read input and echo back
  if (telnetClient && telnetClient.connected()) {
    
    bool newData = false;        // Flag for new input

    while (telnetClient.available()) {
      char c = telnetClient.read();
      Serial.write(c);  // Print to Serial Monitor
      
      if (c == '\n' || c == '\r') {  // End of input
        newData = true;
        break;
      }
      
      receivedData += c;

    }

    // once new data received, acknowledge it
    if (newData && receivedData.length() > 0) {
     receivedData.trim();  // Remove leading/trailing spaces

      // Acknowledge the incoming data
      Serial.print("ACK: ");
      Serial.println(receivedData);

      telnetClient.println("ACK: " + receivedData);
      // telnetClient.println(receivedData);

    }

  } else if (!telnetClient.connected() && telnetClient) {
    Serial.println("Telnet client disconnected.");
    telnetClient.stop();  // disconnect stream
  }

    // convert incoming data to rc-car action
    if (receivedData == "blink") {
      arduinoCmd = 0;
    } else if (receivedData == "bite") {
      arduinoCmd = 1;
    } else if (receivedData == "brow") {
      arduinoCmd = 2;
    } else if (receivedData == "jaw") {
      arduinoCmd = 3;
    } else {
      arduinoCmd = -1;
    }

  return arduinoCmd;

} 

// Stop the car
void stop() {
  // digitalWrite(steeringPower, LOW);
  // digitalWrite(drivePower, LOW);
  digitalWrite(drivePower, LOW);
  digitalWrite(rearLDirection, LOW);
  digitalWrite(rearRDirection, LOW);

  digitalWrite(steeringPower, LOW);
  digitalWrite(frontLDirection, LOW);
  digitalWrite(frontRDirection, LOW);
}

// Go forward
void moveForward(bool turn = false, bool turnLeft = false) {

  // if turning requested, turn in the direction
  if (turn) {
    timeSteps = int(timeSteps * 1.5);
    // Serial.println("Steering powered");
    digitalWrite(steeringPower, HIGH);
    if (turnLeft) {
      // turn left
      steerLeft();
      // Serial.println("turning left");
      
    } else {
      // turn right
      steerRight();
      // Serial.println("turning right");

    }

    delay(100);

  } else {
    // go straight 
    digitalWrite(steeringPower, LOW);
    // Serial.println("Steering left off");
  
  }
  // Serial.println("Driving powered");

  for (int i = 0; i < timeSteps; i++) {

    digitalWrite(drivePower, HIGH);
    digitalWrite(rearLDirection, HIGH);
    digitalWrite(rearRDirection, LOW);
    delay(1);

  }

  digitalWrite(drivePower, LOW);
  delay(500);
  digitalWrite(steeringPower, LOW);
  timeSteps = 500;
  // Serial.println("Driving off");
  // Serial.println("Steering off - end of function");

}

// Go backward
void moveBackward() {
  digitalWrite(steeringPower, LOW);
  for (int i = 0; i < timeSteps; i++) {
    
    digitalWrite(drivePower, HIGH);
    digitalWrite(rearLDirection, LOW);
    digitalWrite(rearRDirection, HIGH);
    delay(1);

  }

  // digitalWrite(steeringPower, LOW);
  digitalWrite(drivePower, LOW);

}

// turn the car wheels left 
void steerLeft() {
  digitalWrite(steeringPower, HIGH);
  digitalWrite(frontLDirection, LOW);
  digitalWrite(frontRDirection, HIGH);
}

// turn the car wheels right
void steerRight() {
  digitalWrite(steeringPower, HIGH);
  digitalWrite(frontLDirection, HIGH);
  digitalWrite(frontRDirection, LOW);
}

void loop() {

  // check for incoming data (first time)
  int arduinoCmd = receiveInput();

  // convert incoming data to rc-car action
  switch (arduinoCmd) {

    // move forward in stright direction
    case 0:
      moveForward();
//       lastMovedFwd = true;
      break;

    // turn left 
    case 1:
      moveForward(true, true);
      // if (lastMovedFwd) {
      //   moveForward(true, true);
      // } else {
      //   moveBackward(true, true);
      // }
      break;

    // turn right
    case 2:
      moveForward(true, false);
//       if (lastMovedFwd) {
//         moveForward(true, false);
//       } else {
//         moveBackward(true, false);
//       }
      break;

    // move backward in stright direction
    case 3:
      moveBackward();
      // lastMovedFwd = false;
      break;

    // if there is no input stop the car by default
    default:
      stop();
      break;
  }
  
}

// void loop() {
//   // moveForward(false, false);
//   moveBackward();
//   delay(2500);
//   stop();
//   delay(1000);
// }
