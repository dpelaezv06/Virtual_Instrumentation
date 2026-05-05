#include "Arduino.h"

// Se define el pin de salida donde se generara la señal PWM.
const int PIN_PWM = 2;

// Se define el ciclo de trabajo deseado (rango de 0 a 255).
// Un valor de 127 representa aproximadamente el 50% del ciclo de trabajo.
const int CICLO_TRABAJO = 127;

void setup() {
  // Se configura el pin como salida digital.
  pinMode(PIN_PWM, OUTPUT);

  // Se inicia la generacion de la señal PWM en el pin especificado.
  // El hardware interno del ESP32 mantendra esta señal activa de forma continua en segundo plano.
  analogWrite(PIN_PWM, CICLO_TRABAJO); // ledcWrite(PIN_PWM, CICLO_TRABAJO); también es una opción 
}

void loop() {

    //...
}