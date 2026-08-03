#ifndef CONFIG_H
#define CONFIG_H

/**********************************************************************
 *                      CONFIGURACIÓN GENERAL
 *
 *      Proyecto:
 *      Invernadero Inteligente IoT
 *
 *      Microcontrolador:
 *      Arduino UNO R4 WiFi
 *
 *      Autor:
 *      Paula Fernández
 *
 *********************************************************************/

#include <Arduino.h>

/**********************************************************************
 *                      CONFIGURACIÓN WIFI
 *********************************************************************/

// Nombre de la red WiFi
constexpr char WIFI_SSID[] = "COMUNIDAD_UNMED";

// Contraseña de la red
constexpr char WIFI_PASSWORD[] = "wifi_med_123";

/**********************************************************************
 *                      CONFIGURACIÓN MQTT
 *********************************************************************/

// Dirección del Broker MQTT
constexpr char MQTT_SERVER[] = "broker.emqx.io";

// Usuario MQTT
// (dejar vacío si el broker no requiere autenticación)
constexpr char MQTT_USER[] = "";

// Puerto MQTT
constexpr uint16_t MQTT_PORT = 1883;

// Contraseña MQTT
constexpr char MQTT_PASSWORD[] = "";

// Identificador único del cliente
constexpr char MQTT_CLIENT_ID[] = "Invernadero_UNO_R4";

/**********************************************************************
 *              TIEMPOS DE RECONEXIÓN
 *********************************************************************/

// Tiempo entre intentos de reconexión WiFi (ms)
constexpr uint32_t WIFI_RECONNECT_TIME = 5000;

// Tiempo entre intentos de reconexión MQTT (ms)
constexpr uint32_t MQTT_RECONNECT_TIME = 5000;

/**********************************************************************
 *          PUBLICACIÓN DE DATOS
 *********************************************************************/

// Tiempo de publicación de sensores (ms)
//
// NOTA:
//
// En tu proyecto ya existe un Timer que genera el evento
// cada 2 segundos.
//
// Este parámetro únicamente se deja como referencia para
// futuras modificaciones.
//
constexpr uint32_t SENSOR_PUBLISH_PERIOD = 2000;

/**********************************************************************
 *              TIMEOUTS
 *********************************************************************/

// Tiempo máximo de espera para conectar al WiFi
constexpr uint32_t WIFI_TIMEOUT = 15000;

// Tiempo máximo de espera para conectar al Broker
constexpr uint32_t MQTT_TIMEOUT = 5000;

/**********************************************************************
 *          INFORMACIÓN DEL DISPOSITIVO
 *********************************************************************/

constexpr char DEVICE_NAME[] = "Invernadero";

constexpr char DEVICE_VERSION[] = "1.0.0";

/**********************************************************************
 *          DEPURACIÓN
 *********************************************************************/

// Activar mensajes Serial
constexpr bool DEBUG_SERIAL = true;

#endif