#include <Arduino.h>
#include <DHT.h>
#include "FspTimer.h"


//Definimos el pin y el tipo de sensor
#define DHTPIN1 A1 // Pin donde está conectado
#define DHTPIN2 A2 
#define DHTTYPE DHT11 // Tipo de sensor

//Definimos el pin para el control de humedad
const int PIN_Humidificador = 5;
//Pines para el control de la bombilla
const int zero_cross = 3;
const int disparador = 4;
const int ventilador = 8;


DHT dht1(DHTPIN1, DHTTYPE);
DHT dht2(DHTPIN2, DHTTYPE);

//Pines del invernadero
const int pin_sensorNivelagua = A0; // Pin analógico para el sensor de nivel de agua

// Instancia global del temporizador 1
FspTimer temporizador1;

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

//Variables para el control PID del piezoeléctrico

// Duty cycle (0 - 100 %)
volatile float duty = 40.0;
int setpoint = 75; // Valor de referencia para la humedad relativa

//Posibles estados que puede tener la maquina de estados
typedef enum {
  IDLE,
  enviarDatos,
  medirTemperatura,
  tempAlta,
  medirRH_Talta,
  RHbaja_Talta,
  RHalta_Talta,
  medirRH_Tbaja,
  RHbaja_Tbaja,
  RHalta_Tbaja,
  RHmedia_Tbaja,
} Estado;

Estado estadoActual = IDLE;

typedef enum {
  automatico,
  manual
} Modo;
Modo modoControl = automatico;


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

void calcularDutyCycle();
void controlHumidificador();

void maquinaDeEstados();

void setup() {
    Serial.begin(115200);
    dht1.begin();
    dht2.begin();
    configurarTimer(0.5f); // Configuramos el temporizador para que interrumpa cada 2 s
    pinMode(PIN_Humidificador, OUTPUT);
    digitalWrite(PIN_Humidificador,LOW);
    pinMode(zero_cross, INPUT); // Configuramos el pin del cruce por cero como entrada
    //attachInterrupt(digitalPinToInterrupt(zero_cross), funcionPara_disparar, RISING); // Configuramos la interrupción para el cruce por cero
    pinMode(disparador,OUTPUT);
    digitalWrite(ventilador,HIGH);
    digitalWrite(disparador,LOW);

}

void loop() {
  serialEvent();
  maquinaDeEstados();


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
            //Condicional para generar el estado de alarma
            if (nivel_agua < 7){
              Serial.println("A_");
            }

            estadoActual = IDLE;
            break;

          case medirTemperatura:
              temperatura1 = dht1.readTemperature(); // Leer la temperatura en Celsius
              temperatura2 = dht2.readTemperature(); // Leer la temperatura en Celsius
              temperaturaPromedio = (temperatura1 + temperatura2) / 2;

              if (temperaturaPromedio > 40){
                estadoActual = tempAlta;
              }
              else{
                estadoActual = medirRH_Tbaja;
              }
              break;

          case tempAlta:
              // Si la temperatura es alta, encendemos el ventilador
              detachInterrupt(digitalPinToInterrupt(zero_cross)); // Deshabilitamos la interrupción del cruce por cero
              digitalWrite(disparador,LOW);
              digitalWrite(ventilador, LOW); // Encender el ventilador
              estadoActual = medirRH_Talta;
              break;

          
          case medirRH_Talta:
              humedad1 = dht1.readHumidity(); // Leer la humedad relativa
              humedad2 = dht2.readHumidity(); // Leer la humedad relativa
              humedadPromedio = (humedad1 + humedad2) / 2;

              if (humedadPromedio < 70){
                estadoActual = RHbaja_Talta;
              }
              else{
                estadoActual = RHalta_Talta;
              }
              break;

          case RHbaja_Talta:
              calcularDutyCycle(); // Calculamos el duty cycle para el humidificador
              controlHumidificador(); // Controlamos el humidificador con el duty cycle calculado
              estadoActual = medirTemperatura; // Volvemos a medir la humedad
              break;

          case RHalta_Talta:
              digitalWrite(PIN_Humidificador,LOW); // Apagamos el humidificador
              estadoActual = medirTemperatura; // Volvemos a medir la humedad
              break;

          case medirRH_Tbaja:
              humedad1 = dht1.readHumidity(); // Leer la humedad relativa
              humedad2 = dht2.readHumidity(); // Leer la humedad relativa
              humedadPromedio = (humedad1 + humedad2) / 2;

              if (humedadPromedio < 70){
                estadoActual = RHbaja_Tbaja;
              }
              else if (humedadPromedio >= 70 && humedadPromedio <= 80){
                estadoActual = RHmedia_Tbaja;
              }
              else{
                estadoActual = RHalta_Tbaja;
              }
              break;
          
          case RHbaja_Tbaja:
              calcularDutyCycle(); // Calculamos el duty cycle para el humidificador
              controlHumidificador(); // Controlamos el humidificador con el duty cycle calculado
              digitalWrite(disparador,LOW);
              detachInterrupt(digitalPinToInterrupt(zero_cross)); // Deshabilitamos la interrupción del cruce por cero
              digitalWrite(ventilador, HIGH); // Encender el ventilador
              estadoActual = medirTemperatura; // Volvemos a medir la humedad
              break;

          case RHmedia_Tbaja:
              digitalWrite(disparador,LOW);
              detachInterrupt(digitalPinToInterrupt(zero_cross)); // Deshabilitamos la interrupción del cruce por cero
              digitalWrite(ventilador, LOW); // Encender el ventilador
              digitalWrite(PIN_Humidificador,LOW); // Apagamos el humidificador
              estadoActual = medirTemperatura; // Volvemos a medir la humedad
              break;

          case RHalta_Tbaja:
              attachInterrupt(digitalPinToInterrupt(zero_cross), funcionPara_disparar, RISING); // Habilitamos la interrupción del cruce por cero
              digitalWrite(ventilador, HIGH); // Apagamos el ventilador
              digitalWrite(PIN_Humidificador,LOW); // Apagamos el humidificador
              estadoActual = medirTemperatura; // Volvemos a medir la humedad
              break;

          default:
            // Si por alguna razón el estado es inválido, volvemos a IDLE
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
        if (modoControl == manual) {
          digitalWrite(ventilador,LOW);
        }
      }
 
      else if(mensajeRecibido == "V0"){
        if (modoControl == manual) {
          digitalWrite(ventilador,HIGH);
        }
      }
      else if (mensajeRecibido == "B1"){
        if (modoControl == manual) {
         attachInterrupt(digitalPinToInterrupt(zero_cross), funcionPara_disparar, RISING);
        }
      }
      else if (mensajeRecibido == "B0"){
        if (modoControl == manual) {
          detachInterrupt(digitalPinToInterrupt(zero_cross));
          digitalWrite(disparador,LOW);
        }
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

//Funcion para control del humidificador mediante PID
void controlHumidificador() {
    // Asegurarse de que el duty cycle esté entre 0 y 100
    if (duty < 0) duty = 0;
    if (duty > 100) duty = 100;
    analogWrite(PIN_Humidificador, (duty / 100.0) * 255); // Convertir el duty cycle a un valor entre 0 y 255
}

void calcularDutyCycle() {
    // Constantes del PID
    const float Kp = 1.0; // Ganancia proporcional
    const float Ki = 0.1; // Ganancia integral
    const float Kd = 0.05; // Ganancia derivativa

    static float errorAnterior = 0;
    static float integral = 0;

    // Calcular el error
    float error = setpoint - humedadPromedio;

    // Calcular la integral y la derivada
    integral += error;
    float derivada = error - errorAnterior;

    // Calcular el output del PID
    duty = Kp * error + Ki * integral + Kd * derivada;

    // Guardar el error actual para la próxima iteración
    errorAnterior = error;

    // Asegurarse de que el duty cycle esté entre 0 y 100
    if (duty < 0) duty = 0;
    if (duty > 100) duty = 100;
}


