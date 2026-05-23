import numpy as np
import matplotlib.pyplot as plt
import serial as pyserial
import time as t


"""
En este script vamos a generar una señal modulada en amplitud (AM) utilizando Python.
La modulación en amplitud es una técnica de modulación en la que la amplitud de la portadora varía en función de la señal moduladora.
"""

#Primero solicitamos al usuario los parámetros de la señal modulada y la portadora
moduler_amplitude = 2.5 / 2 # Voltios
moduler_frecuency = 10 # Hz
carrier_amplitude = 1  # Voltios
carrier_frecuency = 80 # Hz

#Recordemos que m = Vm / Vc, donde Vm es la amplitud de la señal moduladora y Vc es la amplitud de la portadora
#modulation_index = float (input("Ingrese el índice de modulación: "))

#Generamos un vector de tiempo de 1 segundo con 1000 muestras
time = np.linspace(0, 1/moduler_frecuency, 1152)

moduler_signal = moduler_amplitude * np.cos(2 * np.pi * moduler_frecuency * time) # creacion de la seeñal moduladora

AM_signal = (carrier_amplitude + moduler_signal) * np.cos(2 * np.pi * carrier_frecuency * time) # creacion de la señal de amplitud modulada

''' sumar un offset para que la senal varie entre 0 y 5 voltios'''

AM_signal = AM_signal + 2.5 # sumamos un offset de 2.5 voltios para que la señal varie entre 0 y 5 voltios

''' metemos la senal en una escala de 0 a 255 para que el microcontrolador pueda leerla'''
AM_signal = (AM_signal / np.max(AM_signal)) * 255

"""
''' graficamos la señal modulada en amplitud para verificar que se ha generado correctamente'''
plt.plot(time, AM_signal)
plt.title("Señal modulada en amplitud (AM)")
plt.xlabel("Tiempo (s)")
plt.grid()
plt.show()
"""

# Enviamos la señal por el serial al ESP32

velocidad_puerto = 115200 #velocidad de transmision del puerto
puerto = '/dev/ttyS0'
puerto_serial = pyserial.Serial(puerto, velocidad_puerto) #abrimos el puerto serial



''' enviar los datos de la senal al UMC'''
try:
    # Se inicializa la conexion serial. 
    # Se establece un timeout de 1 segundo para evitar bloqueos en la lectura.
    conexion_serial = pyserial.Serial(puerto, velocidad_puerto, timeout=1)
  
    # Se incluye una pausa 
    t.sleep(2)

    ''' Enviar la señal AM al microcontrolador.'''
    while True:
        for valor in AM_signal:
            # Se convierte el valor de la señal a bytes y se envía por el puerto serial.
            conexion_serial.write(valor.astype(np.uint8).tobytes())
    



except pyserial.SerialException as error:
    # Se captura y muestra cualquier error relacionado con la apertura del puerto.
    print(f"Error al abrir el puerto serial: {error}")

finally:
    # Se asegura que el puerto se cierre correctamente al finalizar o si ocurre un error.
    if 'conexion_serial' in locals() and conexion_serial.is_open:
        conexion_serial.close()
        print("Puerto serial cerrado.")
