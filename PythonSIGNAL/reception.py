import numpy as np
import serial as pyserial
import time 
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from scipy.signal import hilbert


def update_plot():
    global line, line2, line3, valores_ADC, senal_demodulada, fft_senal, tiempos
    line.set_data(tiempos, valores_ADC) # actualizamos los datos de la grafica de la senal del ADC
    line2.set_data(tiempos, senal_demodulada) # actualizamos los datos de la grafica de la senal demodulada
    line3.set_data(fft_frecuencias, fft_senal) # actualizamos los datos de la grafica de la FFT de la senal demodulada
    ax1.relim() # recalculamos los limites de la grafica de la senal del ADC
    ax1.autoscale_view() # ajustamos la vista de la grafica de la senal del ADC
    ax2.relim() # recalculamos los limites de la grafica de la senal demodulada
    ax2.autoscale_view() # ajustamos la vista de la grafica de la senal demodulada
    ax3.relim() # recalculamos los limites de la grafica de la FFT de la senal demodulada
    ax3.autoscale_view() # ajustamos la vista de la grafica de la FFT de la senal demodulada
    plt.draw()
    plt.pause(0.01)

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
senal_demodulada = np.array([]) #creamos un array vacio para almacenar los valores de la señal demodulada
fft_senal = np.array([]) #creamos un array vacio para almacenar los valores de la FFT de la señal demodulada
fft_frecuencias = np.array([])
tiempos = np.array([]) #creamos un array vacio para almacenar los tiempos en los cuales se recibio cada valor del ADC
polling_time = 5 # es el tiempo en el cual el programa va a almacenar los datos del ADC recibidos por el serial cada que ocurra un polling, se actualizara la grafica 

''' se generaran 3 graficas:
1. la senal del ADC recibida por el serial
2. la senal demodulada en amplitud (AM)
3. la FFT de la senal AM sin demodular '''



#########Codigo de generacion de las graficas con los 3 subplots y el slider para ajustar el tiempo de polling#########
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8)) # creamos una figura con 3 subplots
line, = ax1.plot([], [], 'b-') # creamos una linea vacia para la grafica de la senal del ADC
ax1.set_title("Valor del ADC recibido por el serial")
ax1.set_xlabel("Tiempo (s)")
ax1.set_ylabel("Valor del ADC")
ax1.grid()
line2, = ax2.plot([], [], 'r-') # creamos una linea vacia para la grafica de la senal demodulada
ax2.set_title("Señal demodulada en amplitud (AM)")
ax2.set_xlabel("Tiempo (s)")
ax2.set_ylabel("Amplitud")
ax2.grid()
line3, = ax3.plot([], [], 'g-') # creamos una linea vacia para la grafica de la FFT de la senal demodulada
ax3.set_title("FFT de la señal demodulada")
ax3.set_xlabel("Frecuencia (Hz)")
ax3.set_ylabel("Magnitud")
ax3.grid()

plt.tight_layout() # ajustamos el layout de las graficas para que no se solapen
plt.pause(0.01) # hacemos una pausa para que se muestren las graficas antes de empezar a actualizar los datos
plt.show()



''' generamos un slider para ajustar el tiempo de polling y asi controlar la tasa de actualizacion de la grafica y la cantidad de datos almacenados en los arrays de tiempos y valores_ADC'''
ax_polling = plt.axes([0.25, 0.01, 0.50, 0.03]) # creamos un eje para el slider
slider_polling = Slider(ax_polling, 'Polling Time (s)', 0.1, 5.0, valinit=polling_time) # creamos el slider con un rango de 0.1 a 5 segundos y un valor inicial de 2 segundos

''' conectamos el slider a la funcion que actualiza el tiempo de polling '''
slider_polling.on_changed(update_pollingTime)


try:
    tiempo_inicio = time.time()
    while True:
        if puerto_serial.in_waiting > 0: # verificamos si hay datos disponibles en el puerto serial
            data = puerto_serial.read(2)
            valor_ADC = int.from_bytes(data, byteorder='little')
            try:
                valor_ADC = int(valor_ADC) # convertimos el valor del ADC a un entero
            except ValueError:
                continue


            #print(f"Valor del ADC recibido: {valor_ADC}") # imprimimos el valor del ADC recibido por el serial
            tiempo_actual = time.time()  # obtenemos el tiempo actual en milisegundos
            valores_ADC = np.append(valores_ADC, valor_ADC) # agregamos el valor del ADC al array de valores_ADC
            tiempos = np.append(tiempos, (tiempo_actual - tiempo_inicio)) # agregamos el tiempo actual al array de tiempos

            ''' antes de graficar verificamos que haya transcurrido el tiempo de polling desde la ultima actualizacion'''

            if tiempos[-1] - tiempos[0] >= polling_time: # verificamos si ha transcurrido el tiempo de polling en milisegundos
               senal_demodulada = valores_ADC - np.mean(valores_ADC) #quitamos el offset
               senal_demodulada = np.abs(hilbert(senal_demodulada))
               senal_demodulada = senal_demodulada - np.mean(senal_demodulada) #quitamos el offset de la demodulada

               fft_senal = np.fft.fft(valores_ADC)
               fft_senal = fft_senal / (np.max(fft_senal))
               fft_senal = fft_senal[:len(fft_senal)//2] # nos quedamos solo con la mitad de los valores de la FFT (los correspondientes a las frecuencias positivas)
               fft_frecuencias = np.fft.fftfreq(len(valores_ADC), d=(tiempos[-1] - tiempos[0])) # calculamos las frecuencias correspondientes a cada valor de la FFT
               fft_frecuencias = fft_frecuencias[:len(fft_frecuencias)//2] # nos quedamos solo con la mitad de las frecuencias (las positivas)



               
               update_plot() # actualizamos la grafica con los nuevos datos
               tiempos = np.array([]) # reiniciamos el array de tiempos para almacenar los nuevos tiempos a partir de la siguiente actualizacion
               valores_ADC = np.array([]) # reiniciamos el array de valores_ADC para almacenar los nuevos valores del ADC a partir de la siguiente actualizacion
               tiempo_inicio = time.time()



except KeyboardInterrupt:
    print("Programa terminado por el usuario.")
finally:
    puerto_serial.close() # cerramos el puerto serial al finalizar el programa








