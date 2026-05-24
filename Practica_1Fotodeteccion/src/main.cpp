#include <Arduino.h>

uint8_t valor_recibido;
const int DAC_PIN = A0;
const long BAUD_RATE = 115200;
int valor_dac = 0;


void setup() {


  Serial.begin(BAUD_RATE, SERIAL_8N1);
  pinMode(DAC_PIN, OUTPUT);
  analogReadResolution(12); // Configura la resolución de lectura analógica a 12 bits (0-4095)

}

void loop() {


  /* se lee el valor de la señal AM desde el puerto serial y se muestra en el monitor serial. */

  if (Serial.available() > 0) {
    valor_recibido = Serial.read();


  }

  analogWrite(DAC_PIN, valor_recibido); // Escribe el valor en el pin DAC


  //delay(20); // Pequeña pausa para evitar saturar el puerto serial
}

// put function definitions here:
