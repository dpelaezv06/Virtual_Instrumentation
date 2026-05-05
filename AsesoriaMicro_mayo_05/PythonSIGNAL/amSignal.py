import numpy as np
import matplotlib.pyplot as plt

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

