#include "Arduino.h"

// Se definen los pines Rx y Tx. Revise el pinout de su placa para determinar los pines disponibles
const int PIN_RX_MODULO = 16;
const int PIN_TX_MODULO = 17;

// Se define la velocidad de comunicacion. Debe coincidir exactamente con la del dispositivo externo.
const long Baudrate = 9600;

void setup() {
  // Se inicializa el puerto Serial
  // Parametros: Velocidad, Formato estandar (8 bits de datos, sin paridad, 1 bit de parada), pin RX, pin TX.
  Serial.begin(Baudrate, SERIAL_8N1, PIN_RX_MODULO, PIN_TX_MODULO);
}

void loop() {

  // --- PROCEDIMIENTO DE ENVIO ---
  
  // Se envia un comando hacia el modulo externo.
  Serial.println(0x01);  


  // --- PROCEDIMIENTO DE RECEPCION ---
  
  // Se verifica si hay bytes en el bufer de entrada esperando a ser leidos.
  if (Serial.available() > 0) {
    
    // Se lee todo el contenido recibido hasta encontrar un salto de linea.
    String respuesta = Serial.readStringUntil('\n');
    
    // El procesamiento del texto recibido dependera del formato del sensor.
  }
  
  delay(1000);
}