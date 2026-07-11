#include <Arduino.h>
#include "FspTimer.h"

// Instancia global del temporizador
FspTimer temporizador;

const int PIN_SENSOR_TOQUE = 2; // Pin digital con soporte de interrupción
const int PIN_LM35 = A0; // Pin analógico para el LM35
const int PIN_RESISTENCIA = 8; // Pin digital conectado al transistor/relé de la resistencia
const int PIN_RED   = 11; 
const int PIN_GREEN = 10;
const int PIN_BLUE  = 9;
volatile bool flagInterrupcion = false; // Bandera para indicar que se ha producido una interrupción


void ISR_sensorToque();
bool leerEstadoSensor();
float leerTemperaturaLM35();
void controlarResistenciaSerial();
void controlarLedRGB(int dutyRed, int dutyGreen, int dutyBlue);
void controlarLedRGB(int dutyRed, int dutyGreen, int dutyBlue);
int calcular_duttyMonocromatico(float p_temp);
void maquinaEstados();
void miFuncionInterrupcion(timer_callback_args_t *args);
void configurarTimer(float frecuenciaHz);
void serialEvent();

float temp = 0.0; // Variable para almacenar la temperatura leída del LM35
String mensajeRecibido = "";     // Aquí se guardará el texto final (sin el '_')
String bufferTemporal = "";      // Va acumulando los caracteres que van llegando

//Estados posibles de la máquina de estados
typedef enum {
  interpretarComando,
  controlRGB,
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

typedef enum{
  controlResistencia,
  controlToque,
}tipoControl;
tipoControl control = controlResistencia; // Control inicial

Estado estadoActual = interpretarComando; // Estado inicial

// Estructura para almacenar los valores de cada LED
struct RGB {
    int r;
    int g;
    int b;
};

RGB dutty = {0, 0, 0}; // Estructura para almacenar los valores de cada LED

RGB calcularDutyCycleRGB(float p_temp);


void setup() {
  pinMode(PIN_SENSOR_TOQUE, INPUT_PULLUP); // O INPUT según tu módulo
  attachInterrupt(digitalPinToInterrupt(PIN_SENSOR_TOQUE), ISR_sensorToque, RISING);
  pinMode(PIN_RESISTENCIA, OUTPUT);
  pinMode(PIN_RED, OUTPUT);
  pinMode(PIN_GREEN, OUTPUT);
  pinMode(PIN_BLUE, OUTPUT);
  Serial.begin(115200);
  digitalWrite(PIN_RESISTENCIA, LOW);
  configurarTimer(50.0f);

}

void loop() {
  serialEvent() ; // Procesar datos entrantes del puerto serie
  maquinaEstados();

}

void maquinaEstados() {
  switch (estadoActual) {
    case interpretarComando:
   ; // Leer hasta el final de línea
      if (mensajeRecibido == "R") {
        control = controlResistencia;
      } 
      else if (mensajeRecibido  == "T") {
        control = controlToque;
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
        colorToque = azulToque;
      }
      else if (mensajeRecibido == "colorRojo") {
        colorToque= rojoToque;
      }
      else if (mensajeRecibido == "colorVerde") {
        colorToque= verdeToque;
      }
      else if (mensajeRecibido == "colorBlanco") {
        colorToque= blancoToque;
      }
      else if (mensajeRecibido == "colorVioleta") {
        colorToque= violetaToque;
      }
      else if (mensajeRecibido == "colorAmarillo") {
        colorToque = amarilloToque;
      }
      else {
        // Comando no reconocido, volver a IDLE
        estadoActual = IDLE;
      }

      break;

    case controlRGB:
    switch (control) {
      case controlResistencia:

      switch (color) {

        case azul:
        dutty.b = calcular_duttyMonocromatico(temp);
        controlarLedRGB(0, 0, dutty.b);
        estadoActual = IDLE; // Cambiar al estado de enviar temperatura
        break;

        case rojo:
            dutty.r = calcular_duttyMonocromatico(temp);
            controlarLedRGB(dutty.r, 0, 0);
            estadoActual = IDLE; // Cambiar al estado de enviar temperatura
          break;

        case verde:
            dutty.g = calcular_duttyMonocromatico(temp);
            controlarLedRGB(0, dutty.g, 0);
            estadoActual = IDLE; // Cambiar al estado de enviar temperatura
          break;


        case policromatico:
            calcularDutyCycleRGB(temp);
            estadoActual = IDLE; // Cambiar al estado de enviar temperatura
 
          break;
      }
      estadoActual = IDLE;
      break;
      
      case controlToque:
      switch (colorToque) {
        case azulToque:
          controlarLedRGB(0, 0, 255);
          estadoActual = IDLE;
          break;
        case rojoToque:
          controlarLedRGB(255, 0, 0);
          estadoActual = IDLE;
          break;
        case verdeToque:
          controlarLedRGB(0, 255, 0);
          estadoActual = IDLE;
          break;
        case blancoToque:
          controlarLedRGB(255, 255, 255);
          estadoActual = IDLE;
          break;
        case violetaToque:
          controlarLedRGB(180, 0, 255);
          estadoActual = IDLE;
          break;
        case amarilloToque:
          controlarLedRGB(255, 255, 0);
          estadoActual = IDLE;
          break;
      }
      estadoActual = IDLE;
      break;
    }
    break;


    case enviarTemperatura:
      temp = leerTemperaturaLM35();
      Serial.print("t_");
      Serial.println(temp, 2);
      Serial.print("R");
      Serial.print(dutty.r);
      Serial.print("B");
      Serial.print(dutty.b);
      Serial.print("G");
      Serial.println(dutty.g);
      estadoActual = IDLE;
      if (control == controlResistencia) {
        estadoActual = controlRGB; // Volver al estado de control RGB si estamos en control de resistencia
      }
      else {
        estadoActual = IDLE; // Volver al estado de espera si estamos en control de toque
      }
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
      if (flagInterrupcion) {
        flagInterrupcion = false; // Limpiar la bandera
        estadoActual = enviarTemperatura; // Cambiar al estado de enviar temperatura
      }
      break;
    default:
      // Estado de espera, no hacer nada
      break;
  }
}
// --- Función de Interrupción (ISR) ---
void ISR_sensorToque() {
  estadoActual = controlRGB; // Cambiamos al estado de control RGB
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

int calcular_duttyMonocromatico(float p_temp){
  int dutty = 0;
  dutty = 10.2 * p_temp - 255;
  return dutty;
}

// Función auxiliar para mapear valores intermedios (regla de tres lineal)
float mapear(float x, float in_min, float in_max, float out_min, float out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

RGB calcularDutyCycleRGB(float p_temp) {
    RGB led;

    // Caso 1: Frío (Menor o igual a 28°C) -> Violeta fijo
    if (p_temp <= 28.0) {
        led.r = 180; led.g = 0; led.b = 255;
    }
    // Caso 2: De Violeta a Azul (28°C a 32.4°C)
    else if (p_temp > 28.0 && p_temp <= 32.4) {
        led.r = (int)mapear(p_temp, 28.0, 32.4, 180, 0);
        led.g = 0;
        led.b = 255;
    }
    // Caso 3: De Azul a Verde (32.4°C a 36.8°C)
    else if (p_temp > 32.4 && p_temp <= 36.8) {
        led.r = 0;
        led.g = (int)mapear(p_temp, 32.4, 36.8, 0, 255);
        led.b = (int)mapear(p_temp, 32.4, 36.8, 255, 0);
    }
    // Caso 4: De Verde a Amarillo (36.8°C a 41.2°C)
    else if (p_temp > 36.8 && p_temp <= 41.2) {
        led.r = (int)mapear(p_temp, 36.8, 41.2, 0, 255);
        led.g = 255;
        led.b = 0;
    }
    // Caso 5: De Amarillo a Naranja (41.2°C a 45.6°C)
    else if (p_temp > 41.2 && p_temp <= 45.6) {
        led.r = 255;
        led.g = (int)mapear(p_temp, 41.2, 45.6, 255, 128);
        led.b = 0;
    }
    // Caso 6: De Naranja a Rojo (45.6°C a 50.0°C)
    else if (p_temp > 45.6 && p_temp < 50.0) {
        led.r = 255;
        led.g = (int)mapear(p_temp, 45.6, 50.0, 128, 0);
        led.b = 0;
    }
    // Caso 7: Muy caliente (Mayor o igual a 50°C) -> Rojo fijo
    else {
        led.r = 255; led.g = 0; led.b = 0;
    }

    return led;
}

void configurarTimer(float frecuenciaHz) {
    uint8_t tipo_timer = 0;
    int canal_timer = 0;

    // 1. Buscar un canal de temporizador AGT (Asynchronous General-Purpose Timer) disponible
    if (!FspTimer::get_available_timer(tipo_timer, canal_timer)) {
        Serial.println("Error: No hay temporizadores disponibles.");
        return;
    }

    // 2. Configurar las propiedades del temporizador
    // Usamos el modo PERIODIC y el temporizador AGT seleccionado
    temporizador.begin(TIMER_MODE_PERIODIC, tipo_timer, canal_timer, frecuenciaHz, 50.0f, miFuncionInterrupcion, nullptr);

    // 3. Habilitar la interrupción en el controlador de interrupciones (NVIC)
    temporizador.setup_overflow_irq();

    // 4. Abrir e iniciar el temporizador
    temporizador.open();
    temporizador.start();

    Serial.print("Temporizador configurado en el canal: ");
    Serial.println(canal_timer);
}

void miFuncionInterrupcion(timer_callback_args_t *args) {
    flagInterrupcion = true; // Establecemos la bandera de interrupción
   
}
