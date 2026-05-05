#include <Arduino.h>

//Definimos primero los pines a utilizar
const int WriteAMSignalPin = 25;
const int ReadAMSignalPin = 34;

// Se definen los pines Rx y Tx. Revise el pinout de su placa para determinar los pines disponibles
const int PIN_RX_MODULO = 16;
const int PIN_TX_MODULO = 17;

//Definimos el baudrate
const int baudrate = 115200;

// put function declarations here:
int myFunction(int, int);

void setup() {
  pinMode(WriteAMSignalPin, DAC1); // Configuramos el pin 25 como salida DAC
  pinMode(ReadAMSignalPin, ADC_2_5db); // Configuramos el pin 34 como entrada

  // Se inicializa el puerto Serial
  // Parametros: Velocidad, Formato estandar (8 bits de datos, sin paridad, 1 bit de parada), pin RX, pin TX.
  Serial.begin(baudrate, SERIAL_8N1, PIN_RX_MODULO, PIN_TX_MODULO);
}

void loop() {

}

// put function definitions here:
int myFunction(int x, int y) {
  return x + y;
}