#include <Arduino.h>

//Definimos el pin ADC
const int PIN_ADC = 34;
const long sampling_rate = 1000; // Frecuencia de muestreo en Hz
const long BAUD_RATE = 115200;
const long sampling_period = 1/sampling_rate;
const long initial_time = 0;


void setup() {
  // put your setup code here, to run once:
  pinMode(PIN_ADC, INPUT);
  Serial.begin(BAUD_RATE);
}

void loop() {
  const long current_time = millis();
  if (current_time - initial_time >= sampling_period) {
    // Lee el valor del ADC 
    int adc_value = analogRead(PIN_ADC);
    // Process the ADC value as needed
    //Enviamos el adc_value al puerto serial como int
    Serial.println(adc_value);
   
}
