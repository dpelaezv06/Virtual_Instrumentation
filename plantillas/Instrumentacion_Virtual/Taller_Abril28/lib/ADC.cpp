#include "Arduino.h"

// Definicion del pin a utilizar. Revise si el pin tiene el ADC disponible.
const int PIN_SEÑAL = 34; 

void setup() {
 
    // Configura el pin de señal como entrada.
    pinMode(PIN_SEÑAL, INPUT);

}

void loop() {

  // Lee el valor digitalizado del pin. El resultado sera un numero entre 0 y 4095 (para resolucion de 12 bits).
  int valorCrudo = analogRead(PIN_SEÑAL);

  // Convierte el valor numerico crudo a un valor de voltaje aproximado.
  // Se hace la conversión considerando que se tiene una referencia de voltaje de 3.3V 
  float voltaje = valorCrudo * (3.3 / 4095.0);

  voltaje = analogReadMilliVolts(PIN_SEÑAL)/1000; // Es equivalente a lo anterior
  
  delay(50);

}