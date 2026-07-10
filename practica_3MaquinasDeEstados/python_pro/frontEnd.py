import tkinter as tk
from tkinter import ttk, messagebox
import serial
import threading
import time

# Configuración del puerto serial
PUERTO = '/dev/ttyACM0'
BAUD_RATE = 115200

class ArduinoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Control - Arduino")
        self.root.geometry("450x550")
        self.root.resizable(False, False)
        
        self.serial_conn = None
        self.conectar_serial()

        self.crear_interfaz()
        
        # Iniciar lectura del puerto serial periódicamente
        self.root.after(100, self.leer_serial)

    def conectar_serial(self):
        try:
            self.serial_conn = serial.Serial(PUERTO, BAUD_RATE, timeout=0.1)
            print(f"Conectado a {PUERTO} a {BAUD_RATE} baudios.")
        except serial.SerialException as e:
            messagebox.showerror("Error de Conexión", f"No se pudo abrir {PUERTO}.\nVerifica que el Arduino esté conectado y tengas permisos.\n\n{e}")

    def enviar_comando(self, comando):
        if self.serial_conn and self.serial_conn.is_open:
            # Añadimos el '_' al final porque el firmware lo usa como terminador
            trama = f"{comando}_"
            self.serial_conn.write(trama.encode('utf-8'))
            print(f"Enviado: {trama}")
        else:
            print("Error: Puerto serial no está abierto.")

    def leer_serial(self):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                while self.serial_conn.in_waiting > 0:
                    linea = self.serial_conn.readline().decode('utf-8').strip()
                    # El firmware envía la temperatura como: "t_XX.XX"
                    if linea.startswith("t_"):
                        temperatura = linea.split('_')[1]
                        self.lbl_temperatura.config(text=f"{temperatura} °C")
            except Exception as e:
                print(f"Error leyendo serial: {e}")
        
        # Volver a llamar a esta función cada 100 ms sin bloquear la interfaz
        self.root.after(100, self.leer_serial)

    def crear_interfaz(self):
        # --- SECCIÓN: COMANDOS PRINCIPALES ---
        frame_comandos = ttk.LabelFrame(self.root, text="Comandos Principales", padding=10)
        frame_comandos.pack(fill="x", padx=10, pady=5)

        ttk.Button(frame_comandos, text="RGB Resistencia (R)", command=lambda: self.enviar_comando("R")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(frame_comandos, text="RGB Toque (T)", command=lambda: self.enviar_comando("T")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame_comandos, text="Pedir Temperatura (ON)", command=lambda: self.enviar_comando("ON")).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(frame_comandos, text="Apagar Resistencia (OFF)", command=lambda: self.enviar_comando("OFF")).grid(row=1, column=1, padx=5, pady=5)

        # --- SECCIÓN: COLOR RESISTENCIA ---
        frame_resistencia = ttk.LabelFrame(self.root, text="Color de Resistencia", padding=10)
        frame_resistencia.pack(fill="x", padx=10, pady=5)

        colores_res = [
            ("Azul", "escalaAzul"),
            ("Rojo", "escalaRojo"),
            ("Verde", "escalaVerde"),
            ("Policromático", "escalaPolicromatico")
        ]
        
        for i, (texto, comando) in enumerate(colores_res):
            ttk.Button(frame_resistencia, text=texto, command=lambda c=comando: self.enviar_comando(c)).grid(row=i//2, column=i%2, sticky="ew", padx=5, pady=5)

        # --- SECCIÓN: COLOR TOQUE ---
        frame_toque = ttk.LabelFrame(self.root, text="Color de Toque", padding=10)
        frame_toque.pack(fill="x", padx=10, pady=5)

        colores_toque = [
            ("Azul", "colorAzul"),
            ("Rojo", "colorRojo"),
            ("Verde", "colorVerde"),
            ("Blanco", "colorBlanco"),
            ("Violeta", "colorVioleta"),
            ("Amarillo", "colorAmarillo")
        ]
        
        for i, (texto, comando) in enumerate(colores_toque):
            ttk.Button(frame_toque, text=texto, command=lambda c=comando: self.enviar_comando(c)).grid(row=i//2, column=i%2, sticky="ew", padx=5, pady=5)

        # --- SECCIÓN: LECTURA DE TEMPERATURA ---
        frame_temp = ttk.LabelFrame(self.root, text="Monitor de Temperatura", padding=10)
        frame_temp.pack(fill="x", padx=10, pady=10)

        self.lbl_temperatura = ttk.Label(frame_temp, text="-- °C", font=("Arial", 24, "bold"), foreground="blue")
        self.lbl_temperatura.pack(pady=10)

    def on_closing(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ArduinoApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()