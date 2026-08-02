#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

/***********************************************************************
 *
 *                      WiFiManager
 *
 *  Proyecto:
 *      Invernadero Inteligente IoT
 *
 *  Descripción:
 *
 *      Gestiona completamente la conexión WiFi mediante una
 *      máquina de estados NO BLOQUEANTE.
 *
 *      Este módulo es responsable únicamente de:
 *
 *          • Inicializar el WiFi.
 *          • Mantener la conexión.
 *          • Reconectar automáticamente.
 *          • Informar el estado de la conexión.
 *
 *      No contiene ninguna lógica relacionada con MQTT.
 *
 ***********************************************************************/

#include <Arduino.h>
#include <WiFiS3.h>

#include "Config.h"

/***********************************************************************
 *                  Estados del módulo WiFi
 ***********************************************************************/

enum class WiFiState
{
    DISCONNECTED,      // Aún no conectado

    CONNECTING,        // Intentando conectar

    CONNECTED,         // Conectado correctamente

    CONNECTION_FAILED, // Timeout durante la conexión

    RECONNECTING       // Esperando nuevo intento
};

/***********************************************************************
 *                      Clase WiFiManager
 ***********************************************************************/

class WiFiManager
{

public:

    /*******************************************************************
     * Constructor
     ******************************************************************/
    WiFiManager();

    /*******************************************************************
     * Inicializa el módulo.
     *
     * Debe llamarse únicamente desde setup().
     ******************************************************************/
    void begin();

    /*******************************************************************
     * Actualiza la máquina de estados.
     *
     * Debe llamarse continuamente desde loop().
     ******************************************************************/
    void loop();

    /*******************************************************************
     * Indica si existe conexión WiFi.
     ******************************************************************/
    bool isConnected() const;

    /*******************************************************************
     * Devuelve el estado actual del módulo.
     ******************************************************************/
    WiFiState getState() const;

    /*******************************************************************
     * Devuelve la dirección IP asignada.
     ******************************************************************/
    IPAddress localIP() const;

    /*******************************************************************
     * Devuelve la intensidad de la señal WiFi.
     *
     * Unidad:
     *      dBm
     ******************************************************************/
    long RSSI() const;

private:

    /*******************************************************************
     * Inicia un nuevo intento de conexión.
     *
     * Esta función únicamente llama a WiFi.begin().
     * No espera a que finalice la conexión.
     ******************************************************************/
    void startConnection();

    /*******************************************************************
     * Supervisa el intento de conexión iniciado previamente.
     *
     * Comprueba:
     *      • Si la conexión fue exitosa.
     *      • Si ocurrió un timeout.
     ******************************************************************/
    void updateConnection();

    /*******************************************************************
     * Comprueba periódicamente si la conexión se perdió.
     ******************************************************************/
    void checkConnection();

    /*******************************************************************
     * Desconecta la interfaz WiFi.
     ******************************************************************/
    void disconnect();

    /*******************************************************************
     * Imprime información de la conexión.
     ******************************************************************/
    void printConnectionInfo() const;

    /*******************************************************************
     * Imprime mensajes de depuración.
     ******************************************************************/
    void printDebug(const String& message) const;

private:

    /*******************************************************************
     * Estado actual de la máquina.
     ******************************************************************/
    WiFiState currentState;

    /*******************************************************************
     * Instante en el que comenzó el intento actual.
     ******************************************************************/
    unsigned long connectionStartTime;

    /*******************************************************************
     * Instante del último intento de reconexión.
     ******************************************************************/
    unsigned long lastReconnectAttempt;

    /*******************************************************************
     * Número de intentos realizados.
     *
     * Se utiliza únicamente para depuración.
     ******************************************************************/
    uint32_t connectionAttempt;

};

#endif