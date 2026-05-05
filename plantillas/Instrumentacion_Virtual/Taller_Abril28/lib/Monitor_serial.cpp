#include "Arduino.h"

void setup() {
  // Se inicializa el puerto serial indicando la velocidad en baudios.
  // 115200 es la velocidad recomendada para el ESP32.
  Serial.begin(115200);

  // Se pueden enviar mensajes para verificar procesos o estados del programa. 
  Serial.println("Holi");
}

void loop() {

  // --- PROCEDIMIENTO DE RECEPCION (Leer lo que manda el PC) ---
  
  // Se verifica si hay caracteres en el bufer esperando a ser leidos.
  if (Serial.available() > 0) {
    
    // Se lee todo el texto recibido hasta que el usuario presiona "Enter" (salto de linea).
    String mensajeRecibido = Serial.readStringUntil('\n');
    
    // Se elimina cualquier espacio en blanco o salto de linea accidental al inicio o final.
    mensajeRecibido.trim();


    // --- PROCEDIMIENTO DE ENVIO (Escribir al PC) ---
    
    // Se imprime una respuesta en la consola para confirmar lo que se recibio.
    Serial.print("Se recibió: ");
    Serial.println(mensajeRecibido);
    
  }
}