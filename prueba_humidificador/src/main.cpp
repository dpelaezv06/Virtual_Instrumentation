#include <Arduino.h>
#include "FspTimer.h"

const short int PIN_HUMIDIFICADOR = 2;

const unsigned long PERIODO_TIMER = 250; // 250 ms por cada "movimiento" del botón
const unsigned int PERIODO_PWM = 5000;   // 5 segundos en total

// 1. CORRECCIÓN: duty debe ser float para soportar decimales (0.5)
float duty = 0.5; 

// 2. CORRECCIÓN: Las variables modificadas en interrupciones deben ser volatile
volatile int contador_interrupciones = 0;

// Reemplazamos el % por el método seguro de intervalos de tiempo
unsigned long tiempo_ultimo_cambio = 0;

FspTimer temporizador1;

void configurarTimer(float frecuenciaHz);
void funcionInterrupcion(timer_callback_args_t *args);

typedef enum {
  INICIAL_OFF,
  TRANSICION_OFF_ON,
  ON,
  TRANSICION_ON_OFF
} Lugar;

Lugar lugar = INICIAL_OFF;

void setup() {
  pinMode(PIN_HUMIDIFICADOR, OUTPUT);
  // Asumimos que HIGH es botón SIN PULSAR y LOW es botón PULSADO
  digitalWrite(PIN_HUMIDIFICADOR, HIGH); 
  
  configurarTimer(1.0f / (PERIODO_TIMER / 1000.0f)); 
  delay(500);
  
  tiempo_ultimo_cambio = millis(); // Inicializamos el contador de tiempo
}

void loop() {
  // Calculamos el tiempo descontando lo que toma físicamente hacer los "clicks"
  // 2 interrupciones = 500ms
  unsigned long tiempo_apagado = ((1.0 - duty) * PERIODO_PWM) - (2 * PERIODO_TIMER);
  // 4 interrupciones = 1000ms
  unsigned long tiempo_encendido = (duty * PERIODO_PWM) - (4 * PERIODO_TIMER); 

  switch (lugar) {
    case INICIAL_OFF:
      // Espera el tiempo de reposo antes de encender
      if (millis() - tiempo_ultimo_cambio >= tiempo_apagado) {
        lugar = TRANSICION_OFF_ON;
        contador_interrupciones = 0;
        temporizador1.start();
      }
      break;

    case TRANSICION_OFF_ON:
      // 2 interrupciones = Baja y sube 1 vez (1 click para encender)
      if (contador_interrupciones >= 2) {
        temporizador1.stop();
        temporizador1.reset();
        digitalWrite(PIN_HUMIDIFICADOR, HIGH); // Aseguramos soltar el botón
        lugar = ON;
        tiempo_ultimo_cambio = millis();
      }
      break;

    case ON:
      // Espera el tiempo encendido antes de apagar
      if (millis() - tiempo_ultimo_cambio >= tiempo_encendido) {
        lugar = TRANSICION_ON_OFF;
        contador_interrupciones = 0;
        temporizador1.start();
      }
      break;

    case TRANSICION_ON_OFF:
      // 4 interrupciones = Baja, sube, baja, sube (2 clicks para apagar)
      if (contador_interrupciones >= 4) {
        temporizador1.stop();
        temporizador1.reset();
        digitalWrite(PIN_HUMIDIFICADOR, HIGH); // Aseguramos soltar el botón
        lugar = INICIAL_OFF;
        tiempo_ultimo_cambio = millis();
      }
      break;
  }
}

void configurarTimer(float frecuenciaHz) {
    uint8_t tipo_timer = 0;
    int canal_timer = 0;

    if (!FspTimer::get_available_timer(tipo_timer, canal_timer)) {
        Serial.println("Error: No hay temporizadores disponibles.");
        return;
    }

    temporizador1.begin(TIMER_MODE_PERIODIC, tipo_timer, canal_timer, frecuenciaHz, 50.0f, funcionInterrupcion, nullptr);
    temporizador1.setup_overflow_irq();
    temporizador1.open();
}

void funcionInterrupcion(timer_callback_args_t *args) {
    // 3. CORRECCIÓN: Empezar asumiendo que el botón está libre (HIGH)
    static bool estadoBoton = HIGH;
    
    // En la primera interrupción (250ms) pasará a LOW (Pulsa el botón)
    // En la segunda interrupción (500ms) pasará a HIGH (Suelta el botón)
    estadoBoton = !estadoBoton; 
    digitalWrite(PIN_HUMIDIFICADOR, estadoBoton);
    
    contador_interrupciones++;
}