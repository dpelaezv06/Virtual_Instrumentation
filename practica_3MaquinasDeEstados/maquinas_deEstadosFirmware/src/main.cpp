#include <Arduino.h>

const int PIN_SENSOR_TOQUE = 2; // Pin digital con soporte de interrupción
volatile bool eventoDetectado = false; // flag para indicar que se detectó un evento de toque
const int PIN_LM35 = A0; // Pin analógico para el LM35
const int PIN_RESISTENCIA = 8; // Pin digital conectado al transistor/relé de la resistencia
const int PIN_RED   = 11; 
const int PIN_GREEN = 10;
const int PIN_BLUE  = 9;



void ISR_sensorToque();
bool leerEstadoSensor();
float leerTemperaturaLM35();
void controlarResistenciaSerial();
void controlarLedRGB(int dutyRed, int dutyGreen, int dutyBlue);
void controlarLedRGB(int dutyRed, int dutyGreen, int dutyBlue);

float temp = 0.0; // Variable para almacenar la temperatura leída del LM35

String mensajeRecibido = "";     // Aquí se guardará el texto final (sin el '_')
String bufferTemporal = "";      // Va acumulando los caracteres que van llegando

//Estados posibles de la máquina de estados
typedef enum {
  interpretarComando,
  RGB_resistencia,
  RGB_toque,
  enviarTemperatura,
  encenderResistencia,
  apagarResistencia,
  IDLE,
  
} Estado;

//Tipo de color para la resistencia
typedef enum{
  azul,
  rojo,
  verde,
  policromatico,

}escalaColor_resistencia;

escalaColor_resistencia color = azul; // Color inicial para la resistencia

//Tipo de color para el LED RGB al detectar un toque
typedef enum{
  azulToque,
  rojoToque,
  verdeToque,
  blancoToque,
  violetaToque,
  amarilloToque,

}colorLED_Toque;
colorLED_Toque colorToque = azulToque; // Color inicial para el LED RGB al detectar un toque

Estado estadoActual = interpretarComando; // Estado inicial




void setup() {
  pinMode(PIN_SENSOR_TOQUE, INPUT_PULLUP); // O INPUT según tu módulo
  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_TOQUE), ISR_sensorToque, RISING);
  pinMode(PIN_RESISTENCIA, OUTPUT);
  pinMode(PIN_RED, OUTPUT);
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_BLUE, OUTPUT);
  Serial.begin(115200);
  digitalWrite(PIN_RESISTENCIA, LOW);

}

void loop() {
  maquinaEstados();
  
 

}

void maquinaEstados() {
  switch (estadoActual) {
    case interpretarComando:
   ; // Leer hasta el final de línea
      if (mensajeRecibido == "R") {
        estadoActual = RGB_resistencia;
      } 
      else if (mensajeRecibido  == "T") {
        estadoActual = RGB_toque;
      }
      else if (mensajeRecibido == "ON") {
        estadoActual = enviarTemperatura;
      }
      else if (mensajeRecibido == "OFF") {
        estadoActual = apagarResistencia;
      }
      else if (mensajeRecibido == "escalaAzul") {
        color = azul;
      }
      else if (mensajeRecibido == "escalaRojo") {
        color = rojo;
      }
      else if (mensajeRecibido == "escalaVerde") {
        color = verde;
      }
      else if (mensajeRecibido == "escalaPolicromatico") {
        color = policromatico;
      }
      else if (mensajeRecibido == "colorAzul") {
        colorLED_Toque color = azulToque;
      }
      else if (mensajeRecibido == "colorRojo") {
        colorLED_Toque color = rojoToque;
      }
      else if (mensajeRecibido == "colorVerde") {
        colorLED_Toque color = verdeToque;
      }
      else if (mensajeRecibido == "colorBlanco") {
        colorLED_Toque color = blancoToque;
      }
      else if (mensajeRecibido == "colorVioleta") {
        colorLED_Toque color = violetaToque;
      }
      else if (mensajeRecibido == "colorAmarillo") {
        colorLED_Toque color = amarilloToque;
      }
      else {
        // Comando no reconocido, volver a IDLE
        estadoActual = IDLE;
      }

      estadoActual = IDLE;
      break;

    case RGB_resistencia:
      temp = leerTemperaturaLM35();
      switch (color) {
        case azul:
          controlarLedRGB(0, 0, 255); // Azul
          break;
        case rojo:
          controlarLedRGB(255, 0, 0); // Rojo
          break;
        case verde:
          controlarLedRGB(0, 255, 0); // Verde
          break;
        case policromatico:
          // Cambiar colores de manera cíclica
          for (int i = 0; i < 3; i++) {
            controlarLedRGB(255, 0, 0); // Rojo
            delay(500);
            controlarLedRGB(0, 255, 0); // Verde
            delay(500);
            controlarLedRGB(0, 0, 255); // Azul
            delay(500);
          }
          break;
      }
      estadoActual = IDLE;
      break;

    case RGB_toque:
      if (leerEstadoSensor()) {
        // Cambiar color del LED RGB al detectar un toque
        controlarLedRGB(255, 0, 0); // Ejemplo: rojo
        delay(500); // Mantener el color por un tiempo
        controlarLedRGB(0, 0, 0);   // Apagar LED
      }
      estadoActual = IDLE;
      break;

    case enviarTemperatura:
      Serial.print("t_");
      Serial.println(temp, 2);
      estadoActual = IDLE;
      break;
    
    case encenderResistencia:
      digitalWrite(PIN_RESISTENCIA, HIGH);
      estadoActual = IDLE;
      break;
    case apagarResistencia:
      digitalWrite(PIN_RESISTENCIA, LOW);
      estadoActual = IDLE;
      break;
    case IDLE:
    default:
      // Estado de espera, no hacer nada
      break;
  }
}
// --- Función de Interrupción (ISR) ---
void ISR_sensorToque() {
  // Esta función debe ser lo más corta y rápida posible
  eventoDetectado = true;
}

// --- Función individual para verificar el estado en tu loop() ---
bool leerEstadoSensor() {
  if (eventoDetectado) {
    eventoDetectado = false; // Reiniciamos la bandera
    return true;             // Hubo un toque/evento
  }
  return false;
}


float leerTemperaturaLM35() {
  int lecturaADC = analogRead(PIN_LM35);
  
  // Convertimos el valor del ADC a voltaje (en Voltios) y luego a Celsius
  float voltaje = (lecturaADC * 5.0) / 1023.0;
  float temperaturaCelsius = voltaje * 100.0;
  
  return temperaturaCelsius;
}


void controlarResistenciaSerial() {
  if (Serial.available() > 0) {
    char comando = Serial.read();
    
    if (comando == 'H') {
      digitalWrite(PIN_RESISTENCIA, HIGH); // Encender resistencia
    } 
    else if (comando == 'O') {
      digitalWrite(PIN_RESISTENCIA, LOW);  // Apagar resistencia
    }
  }
}

void controlarLedRGB(int dutyRed, int dutyGreen, int dutyBlue) {
  // Aseguramos que los valores estén en el rango de 8 bits (0 a 255)
  dutyRed   = constrain(dutyRed, 0, 255);
  dutyGreen = constrain(dutyGreen, 0, 255);
  dutyBlue  = constrain(dutyBlue, 0, 255);

  // Escribimos el duty cycle en cada pin para formar el color
  analogWrite(PIN_RED, dutyRed);
  analogWrite(PIN_GREEN, dutyGreen);
  analogWrite(PIN_BLUE, dutyBlue);
}

void serialEvent() {
  // Mientras haya bytes en el búfer de hardware, los procesamos de inmediato
  while (Serial.available()) {
    char caracterEntrante = (char)Serial.read();
    
    // Si encontramos el carácter indicador '_'
    if (caracterEntrante == '_') {
      mensajeRecibido = bufferTemporal; // Guardamos TODO el texto acumulado HASTA AHORA
      bufferTemporal = "";              // Limpiamos el buffer para el siguiente mensaje
      estadoActual = interpretarComando; // Cambiamos al estado de interpretación de comando
    } 
    // Si no es el '_', y tampoco son caracteres basura de control (como el salto de línea)
    else if (caracterEntrante != '\n' && caracterEntrante != '\r') {
      bufferTemporal += caracterEntrante; // Seguimos acumulando el texto
    }
  }
}