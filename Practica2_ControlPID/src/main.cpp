#include <Arduino.h>

/* configuraciones del serial */
int const baudrate = 115200;
int const PWM_Frequency = 15; // Frecuencia de PWM en Hz
int const PWM_Resolution = 8; // Resolución de PWM en bits (0-255 para 8 bits)
int const PWM_ResistenciaChannel = 0;

/* pines necesarios para la temperatura */
//hardware
int const pinPWM_Resistencia = 14;
int const pinLM35 = 34;

//variables de proceso
float temperatura = 0.0;

//variables de control
float duttycycle_PWM_Resistencia = 0;

//funciones en temperatura
float leerTemperatura() {
  int valor_analogico = analogRead(pinLM35);
  float voltaje = valor_analogico * (3.3 / 4095.0); // Convertir el valor analógico a voltaje (3.3V es la referencia de voltaje del ESP32)
  //float temperatura = voltaje * 100.0; // Convertir el voltaje a temperatura (10mV por grado Celsius para el LM35)
  return voltaje;
}



void setup() {
  /* configuracion del serial para enviar datos al pc (el pc se encargara de realizar el control PID), el esp se encargara
  unicamente de responder a los comandos que el pc le envia */
  Serial.begin(baudrate);
  pinMode(pinPWM_Resistencia, OUTPUT);
  pinMode(pinLM35, INPUT);
  ledcSetup(PWM_ResistenciaChannel, PWM_Frequency, PWM_Resolution); // Configura el canal 0 para PWM con una frecuencia de 5 kHz y una resolución de 8 bits
  ledcAttachPin(pinPWM_Resistencia, PWM_ResistenciaChannel); // Asocia el pin de la resistencia al canal 0 de PWM

}

void loop() {
  /*para la temperatura */
  temperatura = leerTemperatura();
  /* enviamos la temperatura por serial */
  Serial.println(temperatura);

}

