#include <Arduino.h>
#include <DHT.h>
#include "FspTimer.h"


//Definimos el pin y el tipo de sensor
#define DHTPIN1 A1 // Pin donde está conectado
#define DHTPIN2 A2 
#define DHTTYPE DHT11 // Tipo de sensor

//Definimos el pin para el control de humedad
const int PIN_Humidificador = 2;
//Pines para el control de la bombilla
const int zero_cross = 3;
const int disparador = 4;


DHT dht1(DHTPIN1, DHTTYPE);
DHT dht2(DHTPIN2, DHTTYPE);

//Pines del invernadero
const int pin_sensorNivelagua = A0; // Pin analógico para el sensor de nivel de agua

// Instancia global del temporizador 1
FspTimer temporizador;
FspTimer temporizador2;

//Variables para guardar las temperaturas y humedades
float temperatura1 = 0;
float humedad1 = 0;
float temperatura2 = 0;
float humedad2 = 0;
float temperaturaPromedio = 0;
float humedadPromedio = 0;

//Variable para almacenar el nivel del agua
float nivel_agua = 0;

//Bandera para detener el timer2
volatile bool disparar = false;

//Variables para usar el serial de momento
String mensajeRecibido = "";     // Aquí se guardará el texto final (sin el '_')
String bufferTemporal = "";      // Va acumulando los caracteres que van llegando

//Variable para gurdar la frecuencia de disparo
float frecuencia_disparo = 120*8; // Frecuencia de disparo en Hz

unsigned long tiempoAnterior = 0;
//Posibles estados que puede tener la maquina de estados
typedef enum {
  IDLE,
  enviarDatos,
} Estado;

Estado estadoActual = IDLE;

//Funciones para el manejo de la maquina de estados
void funcion_enviarTemperatura();
void funcion_enviarNivelAgua();
void configurarTimer(float frecuenciaHz);
void funcionInterrupcion(timer_callback_args_t *args);
void funcionInterrupcion1(timer_callback_args_t *args);

void funcionInterpretarMensaje ();
void serialEvent();
void funcionPara_disparar ();
void toggle();
void inicializarHumidificador();
void configurarTimer1(float frecuenciaHz);

void controlHumidificador(float duty);

void maquinaDeEstados();

void setup() {
    Serial.begin(115200);
    dht1.begin();
    dht2.begin();
    configurarTimer(0.5f); // Configuramos el temporizador para que interrumpa cada 2 s
    digitalWrite(PIN_Humidificador,LOW);
    //attachInterrupt(digitalPinToInterrupt(zero_cross), funcionPara_disparar, RISING); // Configuramos la interrupción para el cruce por cero
    pinMode(disparador,OUTPUT);

}

void loop() {
  serialEvent();
  maquinaDeEstados();

  if(disparar){
    disparar=false;
    digitalWrite(disparador,LOW);
    delay(6);
    digitalWrite(disparador,HIGH);
 
}
}

void maquinaDeEstados() {
  switch (modoControl) {
    case automatico:
      // En modo automático, ejecutamos la máquina de estados normal
        switch (estadoActual) {
          case IDLE:
            break;

          case enviarDatos:
            funcion_enviarTemperatura();
            funcion_enviarNivelAgua();
            estadoActual = IDLE;
            break;
          }
      break;

    case manual:
      // En modo manual, no hacemos nada en la máquina de estados
      break;;

    default:
      // Si por alguna razón el modo de control es inválido, también salimos
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
    temporizador.begin(TIMER_MODE_PERIODIC, tipo_timer, canal_timer, frecuenciaHz, 50.0f, funcionInterrupcion, nullptr);

    // 3. Habilitar la interrupción en el controlador de interrupciones (NVIC)
    temporizador.setup_overflow_irq();

    // 4. Abrir e iniciar el temporizador
    temporizador.open();
    temporizador.start();

    Serial.print("Temporizador configurado en el canal: ");
    Serial.println(canal_timer);
}

void configurarTimer1(float frecuenciaHz) {
    uint8_t tipo_timer = 0;
    int canal_timer = 1;

    if (!FspTimer::get_available_timer(tipo_timer, canal_timer)) {
        Serial.println("Error: No hay temporizadores disponibles.");
        return;
    }

    temporizador1.begin(TIMER_MODE_PERIODIC, tipo_timer, canal_timer, frecuenciaHz, 50.0f, funcionInterrupcion1, nullptr);
    temporizador1.setup_overflow_irq();
    temporizador1.open();
}

void funcionInterrupcion(timer_callback_args_t *args) {
    estadoActual = enviarDatos; // Cambiamos al estado de enviar datos
   
}

void funcion_enviarTemperatura() {
    temperatura1 = dht1.readTemperature(); // Leer la temperatura en Celsius
    humedad1 = dht1.readHumidity(); // Leer la humedad relativa

    temperatura2 = dht2.readTemperature(); // Leer la temperatura en Celsius
    humedad2 = dht2.readHumidity(); // Leer la humedad relativa

    temperaturaPromedio = (temperatura1 + temperatura2) / 2;
    humedadPromedio = (humedad1 + humedad2) / 2;


    // Enviar los datos por el puerto serie
    Serial.print("t_");
    Serial.print(temperaturaPromedio);
    Serial.print("h_");
    Serial.print(humedadPromedio);

}


void funcion_enviarNivelAgua (){
  float lecturaADC = analogRead(pin_sensorNivelagua); // Leer el valor del sensor de nivel de agua

  // Convertir la lectura ADC a voltaje (0-5V)
  float voltaje = lecturaADC *  (5/ 1023.0); 
  if (voltaje <= 2.9) {
    nivel_agua = 5*voltaje;
  }
  else if (voltaje > 2.9 && voltaje <= 3.1 ){
    nivel_agua = 7*voltaje;
  }
  else if (voltaje > 3.1 && voltaje<= 3.2){
    nivel_agua = 10*voltaje;
  }
  else{
    nivel_agua = 14.2*voltaje;
  }
  Serial.print("n_");
  Serial.println(int(nivel_agua)); // Enviar el valor por el puerto serie

}

void serialEvent() {
  // Mientras haya bytes en el búfer de hardware, los procesamos de inmediato
  while (Serial.available()) {
    char caracterEntrante = (char)Serial.read();
    
    // Si encontramos el carácter indicador '_'
    if (caracterEntrante == '_') {
      mensajeRecibido = bufferTemporal; // Guardamos TODO el texto acumulado HASTA AHORA
      bufferTemporal = "";              // Limpiamos el buffer para el siguiente mensaje
      funcionInterpretarMensaje(); // Cambiamos al estado de interpretación de comando
    } 
    // Si no es el '_', y tampoco son caracteres basura de control (como el salto de línea)
    else if (caracterEntrante != '\n' && caracterEntrante != '\r') {
      bufferTemporal += caracterEntrante; // Seguimos acumulando el texto
    }
  }
}

void funcionInterpretarMensaje (){
  // Leer hasta el final de línea
      if (mensajeRecibido == "A") {
        modoControl = automatico;

      } 
      else if (mensajeRecibido  == "M") {
        modoControl = manual;
      }
      else if(mensajeRecibido == "V1"){
        digitalWrite(ventilador,HIGH);
      }
      else if(mensajeRecibido == "V0"){
        digitalWrite(ventilador,LOW);
      }
      else if (mensajeRecibido == "B1"){
         attachInterrupt(digitalPinToInterrupt(zero_cross), funcionPara_disparar, RISING);
      }
      else if (mensajeRecibido == "B0"){
        //DEsactivamos la interrupción para el cruce por cero
        detachInterrupt(digitalPinToInterrupt(zero_cross));

      
      }
      else {
        // Comando no reconocido, volver a IDLE
        estadoActual = IDLE;
      }
}

void funcionPara_disparar (){
    //disparar = true;
    digitalWrite(disparador,LOW);
    delay(6);
    digitalWrite(disparador,HIGH);
}

void controlHumidificador(float duty)
{
    unsigned long tiempo_apagado =
        ((1.0 - duty) * PERIODO_PWM) - (2 * PERIODO_TIMER);

    unsigned long tiempo_encendido =
        (duty * PERIODO_PWM) - (4 * PERIODO_TIMER);

    switch (lugar)
    {

    case INICIAL_OFF:

        if (millis() - tiempo_ultimo_cambio >= tiempo_apagado)
        {
            lugar = TRANSICION_OFF_ON;

            contador_interrupciones = 0;

            temporizador1.start();
        }

        break;

    case TRANSICION_OFF_ON:

        if (contador_interrupciones >= 2)
        {
            temporizador1.stop();

            temporizador1.reset();

            digitalWrite(PIN_HUMIDIFICADOR, HIGH);

            lugar = ON;

            tiempo_ultimo_cambio = millis();
        }

        break;

    case ON:

        if (millis() - tiempo_ultimo_cambio >= tiempo_encendido)
        {
            lugar = TRANSICION_ON_OFF;

            contador_interrupciones = 0;

            temporizador1.start();
        }

        break;

    case TRANSICION_ON_OFF:

        if (contador_interrupciones >= 4)
        {
            temporizador1.stop();

            temporizador1.reset();

            digitalWrite(PIN_HUMIDIFICADOR, HIGH);

            lugar = INICIAL_OFF;

            tiempo_ultimo_cambio = millis();
        }

        break;
    }
}

void inicializarHumidificador()
{
    pinMode(PIN_HUMIDIFICADOR, OUTPUT);
    digitalWrite(PIN_HUMIDIFICADOR, HIGH);
    configurarTimer(1.0f / (PERIODO_TIMER / 1000.0f));
    delay(500);
    tiempo_ultimo_cambio = millis();
}

void funcionInterrupcion1(timer_callback_args_t *args) {
    // 3. CORRECCIÓN: Empezar asumiendo que el botón está libre (HIGH)
    static bool estadoBoton = HIGH;
    
    // En la primera interrupción (250ms) pasará a LOW (Pulsa el botón)
    // En la segunda interrupción (500ms) pasará a HIGH (Suelta el botón)
    estadoBoton = !estadoBoton; 
    digitalWrite(PIN_HUMIDIFICADOR, estadoBoton);
    
    contador_interrupciones++;
}

