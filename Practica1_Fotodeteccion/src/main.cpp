#include <Arduino.h>

// put function declarations here:
int myFunction(int, int);

void setup() {
  const int PIN_RX_UART = 16;
  const int PIN_TX_UART = 17;

  const long BAUD_RATE = 115200;

  Serial.begin(BAUD_RATE, SERIAL_8N1);

}

void loop() {
  // put your main code here, to run repeatedly:

  Serial.println("Hello, world!");

  if (Serial.available() > 0) {
    String respuesta = Serial.readStringUntil('\n');

  }

  delay(1000);

}

// put function definitions here:
int myFunction(int x, int y) {
  return x + y;
}