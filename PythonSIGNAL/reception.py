import numpy as np
import serial as pyserial
import time 
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

def update_plot():
    line.set_xdata(tiempos)
    line.set_ydata(valores_ADC)
    ax.relim()
    ax.autoscale_view()
    plt.draw()

def update_pollingTime(val):
    global polling_time
    polling_time = slider_polling.val




""" En este script se recibira la senal AM enviada por el ESP32 por el serial /dev/ttyACM0, se graficara, se demodulara,
se le calculara y mostrara su FFT """

velocidad_puerto = 115200 #velocidad de transmision del puerto
puerto = '/dev/ttyACM0'
puerto_serial = pyserial.Serial(puerto, velocidad_puerto) #abrimos el puerto serial
time.sleep(2) # esperamos 2 segundos para que el puerto serial se estabilice


valores_ADC = np.array([]) #creamos un array vacio para almacenar los valores del ADC
tiempos = np.array([]) #creamos un array vacio para almacenar los tiempos en los cuales se recibio cada valor del ADC
polling_time = 2 # es el tiempo en el cual el programa va a almacenar los datos del ADC recibidos por el serial cada que ocurra un polling, se actualizara la grafica 

''' se genera la grafica vacia donde se mostrara la senal del ADC en tiempo real, se actualizara cada que ocurra un polling'''

plt.ion() # habilitamos el modo interactivo de matplotlib para actualizar la grafica en tiempo real
fig, ax = plt.subplots() # creamos la figura y los ejes de la grafica
line, = ax.plot(tiempos, valores_ADC) # creamos una linea vacia para mostrar los valores del ADC en la grafica
ax.set_xlabel('Tiempo (ms)') # etiquetamos el eje x
ax.set_ylabel('Valor del ADC') # etiquetamos el eje y
ax.set_title('Señal recibida') # ponemos un titulo a la grafica
ax.grid() # mostramos una cuadricula en la grafica
plt.show() # mostramos la grafica vacia

''' generamos un slider para ajustar el tiempo de polling y asi controlar la tasa de actualizacion de la grafica y la cantidad de datos almacenados en los arrays de tiempos y valores_ADC'''
ax_polling = plt.axes([0.25, 0.01, 0.50, 0.03]) # creamos un eje para el slider
slider_polling = Slider(ax_polling, 'Polling Time (s)', 0.1, 5.0, valinit=polling_time) # creamos el slider con un rango de 0.1 a 5 segundos y un valor inicial de 2 segundos

''' conectamos el slider a la funcion que actualiza el tiempo de polling '''
slider_polling.on_changed(update_pollingTime)


try:
    while True:
        if puerto_serial.in_waiting > 0: # verificamos si hay datos disponibles en el puerto serial
            valor_ADC = puerto_serial.readline().decode('utf-8').strip() # leemos el valor del ADC
            if valor_ADC != '':
                valor_ADC = int(valor_ADC) # convertimos el valor del ADC a entero

                
            print(f"Valor del ADC recibido: {valor_ADC}") # imprimimos el valor del ADC recibido por el serial
            tiempo_actual = time.time() * 1000 # obtenemos el tiempo actual en milisegundos
            valores_ADC = np.append(valores_ADC, valor_ADC) # agregamos el valor del ADC al array de valores_ADC
            tiempos = np.append(tiempos, tiempo_actual) # agregamos el tiempo actual al array de tiempos

            ''' antes de graficar verificamos que haya transcurrido el tiempo de polling desde la ultima actualizacion'''

            if tiempos[-1] - tiempos[0] >= polling_time * 1000: # verificamos si ha transcurrido el tiempo de polling en milisegundos
               update_plot() # actualizamos la grafica con los nuevos datos
               tiempos = np.array([]) # reiniciamos el array de tiempos para almacenar los nuevos tiempos a partir de la siguiente actualizacion
               valores_ADC = np.array([]) # reiniciamos el array de valores_ADC para almacenar los nuevos valores del ADC a partir de la siguiente actualizacion



except KeyboardInterrupt:
    print("Programa terminado por el usuario.")
finally:
    puerto_serial.close() # cerramos el puerto serial al finalizar el programa








