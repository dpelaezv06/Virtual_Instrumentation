#include <Arduino.h>

//Definimos el pin ADC
const int PIN_ADC = 34;
const long sampling_rate = 1000; // Frecuencia de muestreo en Hz
const long BAUD_RATE = 115200;

void setup() {
  // put your setup code here, to run once:
  pinMode(PIN_ADC, INPUT);
  Serial.begin(BAUD_RATE);
}

void loop() {
  int adc_value = analogRead(PIN_ADC);
  
  // Process the ADC value as needed
  //Enviamos el adc_value al puerto serial como int
  Serial.println(adc_value);

}
