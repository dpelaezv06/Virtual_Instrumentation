#include <Arduino.h>

/* configuraciones del serial */
int const baudrate = 115200;
int const PWM_Frequency = 15; // Frecuencia de PWM (no usada en UNO clásico)
int const PWM_Resolution = 8; // Resolución de PWM en bits (0-255 para 8 bits)
int const PWM_ResistenciaChannel = 0; // Valor no usado en Arduino UNO

/* pines necesarios para la temperatura */
//hardware
// Use a PWM-capable pin for la resistencia (ej. 3,5,6,9,10,11 en UNO)
int const pinPWM_Resistencia = 5;
// Use an analog pin for LM35 (A0..A5). A0 equivale a 14 en Arduino UNO
int const pinLM35 = A0;

//variables de proceso
float temperatura = 0.0;

//variables de control
int duttycycle_PWM_Resistencia = 0;

//funciones en temperatura
float leerTemperatura() {
  int valor_analogico = analogRead(pinLM35);
  // En Arduino UNO el ADC es de 10 bits (0..1023) y la referencia por defecto es 5V
  float voltaje = valor_analogico * (5.0 / 1023.0);
  // LM35 entrega 10 mV por grado Celsius -> temperatura en ºC
  float temperatura_c = voltaje * 100.0;
  return temperatura_c;
}

// Inicializa un pin para PWM en Arduino UNO R4 WiFi
void initPWM(uint8_t pin) {
  pinMode(pin, OUTPUT);
}

// Establece el duty cycle en rango 0..255 (8 bits). Para porcentaje, mapear externamente.
void setPWMDuty(uint8_t pin, uint8_t duty) {
  analogWrite(pin, duty);
}



void setup() {
  /* configuracion del serial para enviar datos al pc (el pc se encargara de realizar el control PID), el esp se encargara
  unicamente de responder a los comandos que el pc le envia */
  Serial.begin(baudrate);
  pinMode(pinLM35, INPUT);
  // Inicializar PWM usando función wrapper para Arduino
  initPWM(pinPWM_Resistencia);
  // Si desea cambiar resolución global (según core), podría usarse analogWriteResolution(),
  // pero en la mayoría de cores AVR la resolución es 8 bits (0-255).
  

}

void loop() {
  /*para la temperatura */
  temperatura = leerTemperatura();
  /* enviamos la temperatura por serial */
  Serial.write((uint8_t*)&temperatura, sizeof(temperatura)); // Enviar temperatura como bytes
  //Serial.println(temperatura);
  
}

