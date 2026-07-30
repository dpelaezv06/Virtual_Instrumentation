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
FspTimer temporizador1;
FspTimer temporizador2;

//Variables para guardar las temperaturas y humedades
float temperatura1 = 0;
float humedad1 = 0;
float temperatura2 = 0;
float humedad2 = 0;

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

void funcionInterpretarMensaje ();
void serialEvent();
void funcionPara_disparar ();
void toggle();

void maquinaDeEstados();

void setup() {
    Serial.begin(115200);
    dht1.begin();
    dht2.begin();
    configurarTimer(0.5f); // Configuramos el temporizador para que interrumpa cada 2 s
    pinMode(PIN_Humidificador, OUTPUT);
    digitalWrite(PIN_Humidificador,LOW);
    attachInterrupt(digitalPinToInterrupt(zero_cross), funcionPara_disparar, RISING); // Configuramos la interrupción para el cruce por cero
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
  switch (estadoActual) {
    case IDLE:
      break;

    case enviarDatos:
      funcion_enviarTemperatura();
      funcion_enviarNivelAgua();
      estadoActual = IDLE;
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

    // 4. Abrir e iniciar el temporizador
    temporizador1.open();
    temporizador1.start();

    Serial.print("Temporizador configurado en el canal: ");
    Serial.println(canal_timer);
}

void funcionInterrupcion(timer_callback_args_t *args) {
    estadoActual = enviarDatos; // Cambiamos al estado de enviar datos
   
}

void funcion_enviarTemperatura() {
    temperatura1 = dht1.readTemperature(); // Leer la temperatura en Celsius
    humedad1 = dht1.readHumidity(); // Leer la humedad relativa

    temperatura2 = dht2.readTemperature(); // Leer la temperatura en Celsius
    humedad2 = dht2.readHumidity(); // Leer la humedad relativa

    // Enviar los datos por el puerto serie
    Serial.print("Temperatura 1: ");
    Serial.print(temperatura1);
    Serial.print(" °C, Humedad 1: ");
    Serial.print(humedad1);
    Serial.println(" %");

    Serial.print("Temperatura 2: ");
    Serial.print(temperatura2);
    Serial.print(" °C, Humedad 2: ");
    Serial.print(humedad2);
    Serial.println(" %");
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
  Serial.print("Nivel de agua: ");
  Serial.println(nivel_agua); // Enviar el valor por el puerto serie

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
      if (mensajeRecibido == "F") {
        digitalWrite(PIN_Humidificador, HIGH);
        Serial.println("Led encendido");
        delay (5000);
        digitalWrite(PIN_Humidificador, LOW);
        delay (300);
        Serial.println ("Led apagado");
      } 
      else if (mensajeRecibido  == "T") {
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


