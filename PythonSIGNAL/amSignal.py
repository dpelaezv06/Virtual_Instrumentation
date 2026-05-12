import numpy as np
import matplotlib.pyplot as plt
import serial as pyserial
import time


"""
En este script vamos a generar una señal modulada en amplitud (AM) utilizando Python.
La modulación en amplitud es una técnica de modulación en la que la amplitud de la portadora varía en función de la señal moduladora.
"""

#Primero solicitamos al usuario los parámetros de la señal modulada y la portadora
moduler_amplitude = 0.5 # Voltios
moduler_frecuency = 20 # Hz
carrier_amplitude = 1 # Voltios
carrier_frecuency = 80 # Hz

#Recordemos que m = Vm / Vc, donde Vm es la amplitud de la señal moduladora y Vc es la amplitud de la portadora
#modulation_index = float (input("Ingrese el índice de modulación: "))

#Generamos un vector de tiempo de 1 segundo con 1000 muestras
time = np.linspace(0, 2, 1000) 

moduler_signal = moduler_amplitude * np.cos(2 * np.pi * moduler_frecuency * time) # creacion de la seeñal moduladora

AM_signal = (carrier_amplitude + moduler_signal) * np.cos(2 * np.pi * carrier_frecuency * time) # creacion de la señal de amplitud modulada


# Enviamos la señal por el serial al ESP32

velocidad_puerto = 115200 #velocidad de transmision del puerto
puerto = '/dev/ttyACM0'
puerto_serial = pyserial.Serial(puerto, velocidad_puerto) #abrimos el puerto serial

  # --- PROCEDIMIENTO DE RECEPCION ---
    
try:
    # Se inicializa la conexion serial. 
    # Se establece un timeout de 1 segundo para evitar bloqueos en la lectura.
    conexion_serial = pyserial.Serial(puerto, velocidad_puerto, timeout=1)
  
    # Se incluye una pausa 
    time.sleep(2)
    
    
    # --- PROCEDIMIENTO DE ENVIO ---
    
    # Se define el mensaje a enviar, agregando un salto de linea al final.
    comando = "ENCENDER_LED\n"
    
    # Se convierte el texto a formato de bytes (UTF-8) y se envia por el puerto.
    conexion_serial.write(comando.encode('utf-8'))
    print("Comando enviado al microcontrolador.")
    
    
    
    # --- PROCEDIMIENTO DE RECEPCION ---
    
    time.sleep(0.1)
    
    # Se verifica si hay bytes esperando en el bufer de entrada de la computadora.
    if conexion_serial.in_waiting > 0:
        
        # Se lee la linea de respuesta proveniente del microcontrolador.
        respuesta_bytes = conexion_serial.readline()
        
        # Se convierte la respuesta de bytes a texto
        respuesta_texto = respuesta_bytes.decode('utf-8').strip()


except pyserial.SerialException as error:
    # Se captura y muestra cualquier error relacionado con la apertura del puerto.
    print(f"Error al abrir el puerto serial: {error}")

finally:
    # Se asegura que el puerto se cierre correctamente al finalizar o si ocurre un error.
    if 'conexion_serial' in locals() and conexion_serial.is_open:
        conexion_serial.close()
        print("Puerto serial cerrado.")