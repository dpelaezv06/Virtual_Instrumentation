import tkinter as tk
import serial
import threading
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def alternar_modo():
    global modo_actual
    
    if modo_actual == "F":
        puerto_serial.write(b'T_')
        modo_actual = "T"
        boton.config(text="Modo Actual: Temperatura")
        puerto_serial.reset_input_buffer()
    else:
        puerto_serial.write(b'F_')
        modo_actual = "F"
        boton.config(text="Modo Actual: Fotorresistencia")
        datos_voltaje.clear()
        ax.clear()
        ax.set_title("Temperatura (°C)")
        canvas.draw()

def leer_serial():
    while True:
        if modo_actual == "T" and puerto_serial.in_waiting >= 2:
            try:
                datos_raw = puerto_serial.read(2)
                valor_adc = int.from_bytes(datos_raw, byteorder='little')
                
                voltaje = valor_adc * (5.0 / 4095.0)
                datos_voltaje.append(voltaje)
                if len(datos_voltaje) > max_puntos:
                    datos_voltaje.pop(0)
            except Exception:
                pass
        time.sleep(0.01)

def actualizar_grafica():
    if modo_actual == "T" and len(datos_voltaje) > 0:
        ax.clear()
        ax.plot(datos_voltaje, color='red', marker='o', markersize=3)
        ax.set_title("Temperatura (°C)")
        ax.grid(True)
        canvas.draw()
        
    ventana.after(200, actualizar_grafica)



puerto_serial = serial.Serial('/dev/ttyUSB0', 115200)

modo_actual = "F"
datos_voltaje = []
max_puntos = 50
ventana = tk.Tk()
ventana.title("Panel de Control y Monitoreo")
ventana.geometry("600x450")

fig = Figure(figsize=(6, 4), dpi=100)
ax = fig.add_subplot(111)
ax.set_title("Voltaje (V)")
ax.grid(True)

canvas = FigureCanvasTkAgg(fig, master=ventana)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

boton = tk.Button(ventana, text="Modo Actual: Fotorresistencia", command=alternar_modo, height=2, width=30)
boton.pack(pady=10)

hilo_serial = threading.Thread(target=leer_serial, daemon=True)
hilo_serial.start()

actualizar_grafica()

ventana.mainloop()