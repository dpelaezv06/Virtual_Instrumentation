import numpy as np
import serial as pyserial
import time
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import scipy.signal as signal


def update_plot():
    global fig, line, line2, line3, valores_ADC, senal_demodulada, fft_senal, tiempos
    line.set_data(tiempos, valores_ADC) # actualizamos los datos de la grafica de la senal del ADC
    line2.set_data(tiempos, senal_demodulada) # actualizamos los datos de la grafica de la senal demodulada
    line3.set_data(fft_frecuencias, np.abs(fft_senal)) # actualizamos los datos de la grafica de la FFT de la senal demodulada
    ax1.relim() # recalculamos los limites de la grafica de la senal del ADC
    ax1.autoscale_view() # ajustamos la vista de la grafica de la senal del ADC
    ax2.relim() # recalculamos los limites de la grafica de la senal demodulada
    ax2.autoscale_view() # ajustamos la vista de la grafica de la senal demodulada
    ax3.relim() # recalculamos los limites de la grafica de la FFT de la senal demodulada
    #ax3.autoscale_view() # ajustamos la vista de la grafica de la FFT de la senal demodulada
    #la grafica de laa fft debe tener una escala de 0 a 200000 en el eje y para poder visualizar la frecuencia dominante
    ax3.set_ylim(0, 200000)
    ax3.set_xlim(0, 500) # ajustamos el limite del eje x de la grafica de la FFT para visualizar mejor las frecuencias bajas



    plt.draw() # redibujamos la grafica con los nuevos datos
    plt.pause(0.01) # pausamos brevemente para permitir que la grafica

def update_pollingTime(val):
    global polling_time
    polling_time = slider_polling.val


""" En este script se recibira la senal AM enviada por el ESP32 por el serial /dev/ttyACM1, se graficara, se demodulara,
se le calculara y mostrara su FFT """

velocidad_puerto = 115200 # velocidad de transmision del puerto
puerto = '/dev/ttyACM1'
puerto_serial = pyserial.Serial(puerto, velocidad_puerto, timeout=1)
time.sleep(2) # esperamos 2 segundos para que el puerto serial se estabilice

valores_ADC =np.array([]) # lista para almacenar los valores del ADC
senal_demodulada = np.array([]) # array para la señal demodulada
fft_senal = np.array([]) # array para la FFT de la señal demodulada
fft_frecuencias = np.array([])
tiempos = np.array([]) # lista para almacenar los tiempos de los valores ADC
lista_frecuecias = []
polling_time = 0.5 # tiempo de polling en segundos para actualizar la grafica

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
ax3.set_title("FFT de la señal ADC")
ax3.set_xlabel("Frecuencia (Hz)")
ax3.set_ylabel("Magnitud")
ax3.grid()

plt.tight_layout() # ajustamos el layout de las graficas para que no se solapen
plt.ion()
plt.show(block=False)
plt.pause(0.1)

''' parametros del filtro butterworth para la senal demodulada '''
cutoff_freq = 15 # frecuencia de corte del filtro en Hz
filter_order = 5 # orden del filtro




''' generamos un slider para ajustar el tiempo de polling y asi controlar la tasa de actualizacion de la grafica y la cantidad de datos almacenados en los arrays de tiempos y valores_ADC'''
ax_polling = plt.axes([0.25, 0.01, 0.50, 0.03]) # creamos un eje para el slider
slider_polling = Slider(ax_polling, 'Polling Time (s)', polling_time * 0.05, polling_time * 1.95, valinit=polling_time) # rango de 0.5 a 2 segundos, valor inicial 2

''' conectamos el slider a la funcion que actualiza el tiempo de polling '''
slider_polling.on_changed(update_pollingTime)


try:
    tiempo_inicio = time.time()
    while True:
        data = puerto_serial.read(2) #
        valor_ADC = int.from_bytes(data, byteorder='little')
        tiempo_actual = time.time()
        valores_ADC= np.append(valores_ADC, valor_ADC)
        tiempos= np.append(tiempos, tiempo_actual - tiempo_inicio)

        if tiempos[-1] - tiempos[0]>= polling_time:
            valores_ADC = valores_ADC - np.mean(valores_ADC) # eliminamos el offset de la señal
            valores_ADC = valores_ADC[100:]
            tiempos = tiempos[100:]

            array_adc = np.asarray(valores_ADC, dtype=float)
            tiempos_arr = np.asarray(tiempos, dtype=float)

            
            senal_demodulada = array_adc - np.mean(array_adc) # eliminamos el offset de la señal
            senal_demodulada = np.abs(senal_demodulada) # rectificamos
            frecuencia_muestreo = len(tiempos_arr) / (tiempos_arr[-1] - tiempos_arr[0])
            nyquist_freq = 0.5 * frecuencia_muestreo # calculamos la frecuencia de Nyquist
            
            normalized_cutoff = cutoff_freq / nyquist_freq # normalizamos la frecuencia de corte

            b, a = signal.butter(filter_order, normalized_cutoff, btype='low', analog = False) # calculamos los coeficientes del filtro Butterworth
            

            senal_demodulada = signal.filtfilt(b, a, senal_demodulada) # aplicamos el filtro a la señal demodulada
            senal_demodulada = senal_demodulada - np.mean(senal_demodulada) # eliminamos el offset de la señal demodulada filtrada


            fft_senal = np.abs(np.fft.rfft(array_adc))
            #if fft_senal.max() != 0:
                #fft_senal /= fft_senal.max()
            fft_frecuencias = np.fft.rfftfreq(
                len(array_adc),
                d=np.mean(np.diff(tiempos_arr)) if len(tiempos_arr) > 1 else 1.0,
            )
            fft_modulada = np.abs(np.fft.rfft(senal_demodulada))
            #if fft_modulada.max() != 0:
                #fft_modulada /= fft_modulada.max()
            fft_frecuencias_modulada = np.fft.rfftfreq(
                len(senal_demodulada),
                d=np.mean(np.diff(tiempos_arr)) if len(tiempos_arr) > 1 else 1.0,
            )
            fft_maxIndex = np.argmax(fft_modulada)
            frecuencia_dominante = fft_frecuencias_modulada[fft_maxIndex]
            lista_frecuecias.append(frecuencia_dominante)


            

            update_plot()
            tiempos = np.array([])
            valores_ADC = np.array([])
            tiempo_inicio = time.time()
            fft_frecuencias = np.array([])
            fft_senal = np.array([])
            senal_demodulada = np.array([])
            print(str(2 * len(lista_frecuecias)) + " %")

            if len(lista_frecuecias) > 50:
                lista_frecuencias = np.array(lista_frecuecias)
                promedio_frecuencia = np.mean(lista_frecuecias)
                desviacion_estandar = np.std(lista_frecuecias)
                incertidumbre_relativa = (desviacion_estandar / promedio_frecuencia) * 100
                print(f"Dominante promedio: " + str(promedio_frecuencia) + " Hz")
                print(f"Desviacion estandar: " + str(desviacion_estandar) + " Hz\n")
                print(f"Error porcentual: " + str(np.abs(((10-promedio_frecuencia)))*10) + " %")
                print(f"Incertidumbre relativa: " + str(incertidumbre_relativa) + " %")
                lista_frecuecias = []
except KeyboardInterrupt:
    print("Programa terminado por el usuario.")
finally:
    puerto_serial.close() # cerramos el puerto serial al finalizar el programa








