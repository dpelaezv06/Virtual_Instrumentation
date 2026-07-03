#include <Arduino.h>

/* configuraciones del serial */
int const baudrate = 115200;
int const PWM_Frequency = 15; // Frecuencia de PWM (no usada en UNO clásico)
int const PWM_Resolution = 8; // Resolución de PWM en bits (0-255 para 8 bits)
int const PWM_ResistenciaChannel = 0; // Valor no usado en Arduino UNO

/* pines necesarios para la temperatura */
//hardware
// Use a PWM-capable pin for la resistencia (ej. 3,5,6,9,10,11 en UNO)
int const pinPWM_Resistencia = 5;
// Use an analog pin for LM35 (A0..A5). A0 equivale a 14 en Arduino UNO
int const pinLM35 = A0;

float temperaturaRawData = 0; // Variable para almacenar el valor de temperatura leido del LM35
volatile float temperatura = 0.0;

//Pines necesarios para el Driver del motor
int const in1 = 2;
int const in2 = 3;

//Pin necesario para el encoder
int const pinEncoder = 4; 

//Contador para el calculo de la velocidad del motor
long contador = 0;

//Para hacer el muestreo cada 10 ms
unsigned long tiempoAnterior = 0;
const unsigned long Ts = 10000;   // 10 ms


//variables de control
int duttycycle_PWM_Resistencia = 0;
int duttycycle_PWM_in1 = 254;
int duttycycle_PWM_in2 = 0;

//funciones en temperatura
float leerTemperaturaRawData() {
  int valor_analogico = analogRead(pinLM35);
  temperatura = ((valor_analogico * 5.0 / 1023.0) * 100.0)-6; // Convertir a grados Celsius
  return temperatura;
}

void procesarComandoSerial(const String &comando) {
  if (comando.startsWith("t_")) {
    int valor = comando.substring(2).toInt();
    if (valor >= 0 && valor <= 255) {
      duttycycle_PWM_Resistencia = valor;
      Serial.println("ack_t");
    }
  } else if (comando.startsWith("v_")) {
    int valor = comando.substring(2).toInt();
    if (valor >= 0 && valor <= 255) {
      duttycycle_PWM_in1 = valor;
      Serial.println("ack_v");
    }
  }
}

void leerComandoSerial() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      serialBuffer.trim();
      if (serialBuffer.length() > 0) {
        procesarComandoSerial(serialBuffer);
      }
      serialBuffer = "";
    } else if (c != '\r') {
      serialBuffer += c;
      if (serialBuffer.length() > 64) {
        serialBuffer = ""; // evitar saturación con datos no válidos
      }
    }
  }
}

// Inicializa un pin para PWM en Arduino UNO R4 WiFi
void initPWM(uint8_t pin) {
  pinMode(pin, OUTPUT);
}

// Establece el duty cycle en rango 0..255 (8 bits). Para porcentaje, mapear externamente.
void setPWMDuty(uint8_t pin, uint8_t duty) {
  analogWrite(pin, duty);
}

//Cada vez que se llama a esta funcion se incrementa el contador del encoder
void encoderISR()
{
    contador++;
}



void setup() {
  /* configuracion del serial para enviar datos al pc (el pc se encargara de realizar el control PID), el esp se encargara
  unicamente de responder a los comandos que el pc le envia */
  Serial.begin(baudrate);
  pinMode(pinLM35, INPUT);
  // Inicializar PWM usando función wrapper para Arduino
  initPWM(pinPWM_Resistencia);
  initPWM(in1);
  initPWM(in2);
  pinMode(pinEncoder, INPUT_PULLUP); // Configurar el pin del encoder con resistencia pull-up interna

  // Configurar interrupción para el pin del encoder
  attachInterrupt(digitalPinToInterrupt(pinEncoder), encoderISR, RISING);

}

  // Si desea cambiar resolución global (según core), podría usarse analogWriteResolution(),
  // pero en la mayoría de cores AVR la resolución es 8 bits (0-255).
  



void loop() {
  /* Leemos la temperatura en cada ciclo, pero NO la enviamos todavía
     (se envía más abajo, sincronizada con la ventana Ts) */
  temperaturaRawData = leerTemperaturaRawData();

  /* Leer comandos PWM entrantes separados por línea. Se llama en cada
     vuelta del loop (sin delay bloqueante) para vaciar el buffer RX
     tan rápido como llegan los datos y evitar que se acumulen */
  leerComandoSerial();

  /* Aplicar PWM de la resistencia y del motor */
  setPWMDuty(pinPWM_Resistencia, duttycycle_PWM_Resistencia);
  setPWMDuty(in1, duttycycle_PWM_in1);

  if (micros() - tiempoAnterior >= Ts) {
    tiempoAnterior += Ts;

    Serial.print("t_");
    Serial.println(temperaturaRawData);

        // Leer encoder
        long velocidad = (contador * 60)/(700*0.01); // Velocidad en pulsos por segundo (pulsos/s)
        Serial.println("velocidad: " + String(velocidad)); // Enviar velocidad al PC
        contador = 0; // Reiniciar contador para la siguiente medición
        
    }
}
