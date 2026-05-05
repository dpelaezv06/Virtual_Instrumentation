import numpy as np
import matplotlib.pyplot as plt

"""
En este script vamos a generar una señal modulada en amplitud (AM) utilizando Python.
La modulación en amplitud es una técnica de modulación en la que la amplitud de la portadora varía en función de la señal moduladora.
"""

#Primero solicitamos al usuario los parámetros de la señal modulada y la portadora
moduler_amplitude = float (input("Ingrese la amplitud de la señal: "))
moduler_frecuency = float (input("Ingrese la frecuencia de la señal: "))
carrier_amplitude = float (input("Ingrese la amplitud de la portadora: "))
carrier_frecuency = float (input("Ingrese la frecuencia de la portadora: "))

#Recordemos que m = Vm / Vc, donde Vm es la amplitud de la señal moduladora y Vc es la amplitud de la portadora
modulation_index = float (input("Ingrese el índice de modulación: "))

#Generamos un vector de tiempo de 1 segundo con 1000 muestras
t = np.linspace(0, 1, 1000) 


