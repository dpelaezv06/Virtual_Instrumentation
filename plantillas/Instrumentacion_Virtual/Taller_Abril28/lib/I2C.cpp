#include "Arduino.h"

// Se incluye la libreria estandar para comunicacion I2C.
#include <Wire.h>

/* I2C comm*/
  TwoWire I2C_ONE = TwoWire(0);
  #define I2C_SDA1 1
  #define I2C_SCL1 2

 // Sensor objects
 Adafruit_VEML7700 VEML1;  // Lux sensor on I2C_ONE

void setup() {

    // Initialize the VEML7700 lux sensor on I2C_ONE
    /** */
    if (!VEML1.begin(&I2C_ONE)) {
        while (1);
    }

    // Initialize I2C buses for the sensor
    I2C_ONE.begin(I2C_SDA1, I2C_SCL1, 50000);  // I2C Bus 1
}

void loop() {

 // Reads lux sensor
    float Medicion_luz = VEML1.readLux(VEML_LUX_AUTO);   // Via I2C bus 1
}