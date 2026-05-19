#include <Arduino.h>

uint8_t valor_recibido;
const int PIN_DAC = 25;
const int PIN_ADC = 34;
const long BAUD_RATE = 115200;
int valor_dac = 0;


void setup() {


  Serial.begin(BAUD_RATE, SERIAL_8N1);
  pinMode(PIN_ADC, INPUT);

}

void loop() {


  /* se lee el valor de la señal AM desde el puerto serial y se muestra en el monitor serial. */

  if (Serial.available() > 0) {
    valor_recibido = Serial.read();
    Serial.print("Valor recibido: ");
    Serial.println(valor_recibido);

  }

  dacWrite(PIN_DAC, valor_recibido); // Escribe el valor en el pin DAC

  //delay(20); // Pequeña pausa para evitar saturar el puerto serial
}

// put function definitions here:
