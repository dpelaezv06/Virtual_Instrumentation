#include <Arduino.h>

const int BAUD_RATE = 115200;
const int pinLM35 = 32;
const int pinFotorresistencia = 27;
const int pinLedLM35 = 19;
const int pinLedFotorresistencia = 23;

int ADC_LM35Value = 0;
int ADC_FotorresistenciaValue = 0;
int pwmValue = 0;

int valorLM35();
int valorFotorresistencia();
int calcularPWMLM35(int pValorLM35);
void configurarPWMLM35(int pValorPWM);
int calcularPWMLedFotorresistencia(int pValorFotorresistencia);
void configurarPWMLedFotorresistencia(int pValorPWM);
void reconocerComandoModo();
void enviarDatosRaw();

enum Modo {
  temperatura,
  fotorresistencia
};

int modoActual = fotorresistencia;

void setup() {
  Serial.begin(BAUD_RATE);
  
  pinMode(pinLM35, INPUT);
  pinMode(pinFotorresistencia, INPUT);
  
  pinMode(pinLedLM35, OUTPUT);
  pinMode(pinLedFotorresistencia, OUTPUT);
}

void loop() {
  switch (modoActual) {
    case temperatura:
      ADC_LM35Value = valorLM35();
      pwmValue = calcularPWMLM35(ADC_LM35Value);
      configurarPWMLM35(pwmValue);
      analogWrite(pinLedFotorresistencia, 0);
      enviarDatosRaw();
      break;

    case fotorresistencia:
      ADC_FotorresistenciaValue = valorFotorresistencia();
      pwmValue = calcularPWMLedFotorresistencia(ADC_FotorresistenciaValue);
      configurarPWMLedFotorresistencia(pwmValue);
      analogWrite(pinLedLM35, 0);
      break;

    default:
      modoActual = temperatura;
      break;
  }

  reconocerComandoModo();
  delay(200);
}

int valorLM35() {
  int valor = 0;
  valor = analogRead(pinLM35);
  return valor;
}

int calcularPWMLM35(int pValorLM35) {
  float calculoPWM = pValorLM35 * 500.0 / 4095.0;
  calculoPWM = (14.0 / 3.0) * calculoPWM - (205.0 / 3.0);
  
  int valorPWM = (int)calculoPWM;
  
  if (valorPWM < 0) {
    valorPWM = 0;
  }

  if (valorPWM > 255) {
    valorPWM = 255;
  }

  valorPWM = constrain(valorPWM, 0, 255);
  return valorPWM;
}

void configurarPWMLM35(int pValorPWM) {
  analogWrite(pinLedLM35, pValorPWM);
}

int calcularPWMLedFotorresistencia(int pValorFotorresistencia) {
  float calculoPWM = (17.0 / 273.0) * pValorFotorresistencia;
  
  int valorPWM = (int)calculoPWM;
  
  if (valorPWM < 0) {
    valorPWM = 0;
  }

  if (valorPWM > 255) {
    valorPWM = 255;
  }

  valorPWM = constrain(valorPWM, 0, 255);
  return valorPWM;
}

void configurarPWMLedFotorresistencia(int pValorPWM) {
  analogWrite(pinLedFotorresistencia, pValorPWM);
}

int valorFotorresistencia() {
  int valor = 0;
  valor = analogRead(pinFotorresistencia);
  return valor;
}

void enviarDatosRaw() {
  uint16_t dato = ADC_LM35Value;
  Serial.write((uint8_t*)&dato, 2);
}

void reconocerComandoModo() {
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('_');

    if (comando == "T") {
      modoActual = temperatura;
    } else if (comando == "F") {
      modoActual = fotorresistencia;
    }
  }
}