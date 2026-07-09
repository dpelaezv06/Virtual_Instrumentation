#include <Arduino.h>

const int PIN_SENSOR_TOQUE = 2; // Pin digital con soporte de interrupción
volatile bool eventoDetectado = false; // flag para indicar que se detectó un evento de toque
const int PIN_LM35 = A0; // Pin analógico para el LM35
const int PIN_RESISTENCIA = 8; // Pin digital conectado al transistor/relé de la resistencia
const int PIN_RED   = 9;
const int PIN_GREEN = 10;
const int PIN_BLUE  = 11;



void ISR_sensorToque();
bool leerEstadoSensor();
float leerTemperaturaLM35();
void controlarResistenciaSerial();
void controlarLedRGB(int dutyRed, int dutyGreen, int dutyBlue);
void controlarLedRGB(int dutyRed, int dutyGreen, int dutyBlue);



void setup() {
  pinMode(PIN_SENSOR_TOQUE, INPUT_PULLUP); // O INPUT según tu módulo
  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_TOQUE), ISR_sensorToque, RISING);
  pinMode(PIN_RESISTENCIA, OUTPUT);
  pinMode(PIN_RED, OUTPUT);
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_BLUE, OUTPUT);
  Serial.begin(115200);

}

void loop() {


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