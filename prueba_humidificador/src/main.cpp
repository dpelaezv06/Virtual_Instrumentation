#include <Arduino.h>
#include "FspTimer.h"


const short int PIN_HUMIDIFICADOR = 2;

const unsigned long PERIODO_TIMER = 250; // Período del temporizador en milisegundos (250 ms)
const unsigned int PERIODO_PWM = 5000;
int duty = 0.5;
int contador_interrupciones = 0;

volatile unsigned long tiempo_actual = 0;
volatile bool done =false;
FspTimer temporizador1;

void configurarTimer(float frecuenciaHz);
void funcionInterrupcion(timer_callback_args_t *args);




typedef enum {
  INICIAL_OFF,
  TRANSICION_OFF_ON,
  ON,
  TRANSICION_ON_OFF,
  OFF
} Lugar;

Lugar lugar = INICIAL_OFF;

void setup() {
  pinMode(PIN_HUMIDIFICADOR, OUTPUT);
  digitalWrite(PIN_HUMIDIFICADOR, HIGH);
  configurarTimer(1.0f / (PERIODO_TIMER / 1000.0f)); // Configurar el temporizador para que interrumpa cada 250 ms  
  delay(500);
}

void loop() {

  tiempo_actual = millis();
  tiempo_actual = tiempo_actual % PERIODO_PWM;

  switch (lugar)
  {
  case INICIAL_OFF:
  if (!done) {
    digitalWrite(PIN_HUMIDIFICADOR, HIGH);
    done = true;
  }


  if (!(tiempo_actual < ((1 - duty) * PERIODO_PWM) - PERIODO_TIMER)) {
    lugar = TRANSICION_OFF_ON;
    done = false;
    temporizador1.start();
  }

    break;

  case TRANSICION_OFF_ON:

  if (contador_interrupciones == 2){
    temporizador1.stop();
    temporizador1.reset();
    lugar = ON;
    done = false;
    contador_interrupciones = 0;
  }

    break;

  case ON:

  if (tiempo_actual >= (duty * PERIODO_PWM) - 3 * PERIODO_TIMER) {
    lugar = TRANSICION_ON_OFF;
    done = false;
    temporizador1.start();
  }

  break;

  case TRANSICION_ON_OFF:
  if (contador_interrupciones == 4){
    temporizador1.stop();
    temporizador1.reset();
    lugar = OFF;
    done = false;
    contador_interrupciones = 0;
  }

    break;

  case OFF:
  if (tiempo_actual < ((1 - duty) * PERIODO_PWM) - 2 * PERIODO_TIMER) {
    lugar = TRANSICION_OFF_ON;  
    done = false;
    temporizador1.start();
  }
  break;
    

  
  default:
    break;
  }

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
    temporizador1.begin(TIMER_MODE_PERIODIC, tipo_timer, canal_timer, frecuenciaHz, 50.0f, funcionInterrupcion, nullptr);

    // 3. Habilitar la interrupción en el controlador de interrupciones (NVIC)
    temporizador1.setup_overflow_irq();

    // 4. Abrir el temporizador
    temporizador1.open();

}

void funcionInterrupcion(timer_callback_args_t *args) {
    static bool estadoHumidificador = false;
    contador_interrupciones++;
    estadoHumidificador = !estadoHumidificador;
    digitalWrite(PIN_HUMIDIFICADOR, estadoHumidificador ? HIGH : LOW);
}