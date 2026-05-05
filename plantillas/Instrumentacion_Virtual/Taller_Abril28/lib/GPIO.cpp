#include "Arduino.h"

// Definicion de pines a utilizar. 
const int PIN_SALIDA = 2; 
const int PIN_ENTRADA = 4;

int LecturaEntrada = 0;

void setup() {

  // Configuracion del pin de salida.
  pinMode(PIN_SALIDA, OUTPUT); //INPUT, OUTPUT, INPUT_PULLUP, INPUT_PULLDOWN, OPEN_DRAIN, OUTPUT_OPEN_DRAIN, ANALOG

  // Configuracion del pin de entrada. Se activa la resistencia interna pull-up.
  // El estado por defecto sera HIGH. Al conectar el pin a tierra, pasara a LOW.
  pinMode(PIN_ENTRADA, INPUT);
}

void loop() {

  // Lee el estado actual del pin de entrada y lo almacena en una variable.
   LecturaEntrada = digitalRead(PIN_ENTRADA);

  // Evalua el estado leido para tomar una accion.
  if (LecturaEntrada == LOW) {
    // Si el estado es bajo, se activa el pin de salida asignando un estado alto.
    digitalWrite(PIN_SALIDA, HIGH);

  } else {
    // Si el estado es alto, se desactiva el pin de salida asignando un estado bajo.
    digitalWrite(PIN_SALIDA, LOW);
  }

  delay(50);
}


