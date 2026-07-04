#include <Arduino.h>

int const baudrate = 115200;
int const pinPWM_Resistencia = 5;
int const pinLM35 = A0;

// Pines del Driver del motor
int const in1 = 2;
int const in2 = 4;
int const pinEncoder = 3; 

volatile long contador = 0;
String serialBuffer = ""; 

// Muestreo optimizado a 30 ms (Evita saturación y es excelente para PID)
unsigned long tiempoAnterior = 0;
const unsigned long Ts = 30000;   // 30 ms (33 Hz)
// Velocidad = (pulsos / 100 ranuras) * (60 s / dt) -> RPM
float dt = Ts / 1000000.0;

int duttycycle_PWM_Resistencia = 0;
int duttycycle_PWM_in1 = 45;

float leerTemperatura() {
  int valor_analogico = analogRead(pinLM35);
  // Conversión optimizada directo a float
  return ((valor_analogico * 5.0 / 1023.0) * 100.0) - 6.0;
}

void procesarComandoSerial(const String &comando) {
  int valor = comando.substring(2).toInt();
  if (valor < 0 || valor > 255) return;

  if (comando.startsWith("t_")) {
    duttycycle_PWM_Resistencia = valor;
    Serial.println("ack_t");
  } else if (comando.startsWith("v_")) {
    duttycycle_PWM_in1 = valor;
    Serial.println("ack_v");
  }
}

void leerComandoSerial() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      serialBuffer.trim();
      if (serialBuffer.length() > 0) {
        procesarComandoSerial(serialBuffer);
      }
      serialBuffer = "";
    } else if (c != '\r') {
      serialBuffer += c;
      if (serialBuffer.length() > 16) { // Buffer más corto, comandos pequeños
        serialBuffer = ""; 
      }
    }
  }
}

void encoderISR() {
  contador++;
}

void setup() {
  Serial.begin(baudrate);
  pinMode(pinLM35, INPUT);
  pinMode(pinPWM_Resistencia, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  digitalWrite(in2, LOW); // Dirección fija del motor
  pinMode(pinEncoder, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(pinEncoder), encoderISR, RISING);
}

void loop() {
  leerComandoSerial();

  analogWrite(pinPWM_Resistencia, duttycycle_PWM_Resistencia);
  analogWrite(in1, duttycycle_PWM_in1);

  unsigned long tiempoActual = micros();
  if (tiempoActual - tiempoAnterior >= Ts) {
    tiempoAnterior = tiempoActual; // Corrección de deriva temporal

    // 1. Enviar Temperatura con formato correcto
    float temp = leerTemperatura();
    Serial.print("t_");
    Serial.println(temp, 2);

    // 2. Calcular y enviar velocidad (Cálculo sin Strings)
    // Desactivar interrupciones momentáneamente para lectura segura de variable volatile
    noInterrupts();
    long pulsos = contador;
    contador = 0;
    interrupts();

    // Ts está en microsegundos, convertimos a segundos dividiendo por 1,000,000

    long velocidadRPM = (pulsos / 100.0) * (60.0 / dt);

    Serial.print("v_");
    Serial.println(velocidadRPM); 
  }
}