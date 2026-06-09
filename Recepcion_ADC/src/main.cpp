#include <Arduino.h>

//Definimos el pin ADC
const int PIN_ADC = 32;
const long BAUD_RATE = 115200;

const uint32_t sampling_rate = 1000;
const uint32_t sampling_period = 1000000 / sampling_rate;

uint32_t last_sample = 0;

void setup() {
  // put your setup code here, to run once:
  pinMode(PIN_ADC, INPUT);
  Serial.begin(BAUD_RATE);
}

void loop() {

    uint32_t time_now = micros();

    if(time_now - last_sample >= sampling_period){

        last_sample += sampling_period;

        uint16_t adc_value = analogRead(PIN_ADC);

        Serial.write((uint8_t*)&adc_value, sizeof(adc_value));
    }
}
