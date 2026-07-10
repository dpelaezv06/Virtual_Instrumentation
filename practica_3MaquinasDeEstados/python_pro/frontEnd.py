import tkinter as tk
from tkinter import ttk, messagebox

class ArduinoApp:
    def __init__(self, root, backend):
        self.root = root
        self.backend = backend
        
        self.root.title("Panel de Control - Arduino")
        self.root.geometry("450x550")
        self.root.resizable(False, False)

        # 1. Intentar conectar el backend
        exito, mensaje = self.backend.conectar()
        if not exito:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar al Arduino.\n\nDetalle: {mensaje}")

        # 2. Dibujar interfaz
        self.crear_interfaz()
        
        # 3. Iniciar el bucle de actualización de pantalla
        self.actualizar_pantalla()

    def crear_interfaz(self):
        # --- COMANDOS PRINCIPALES ---
        frame_comandos = ttk.LabelFrame(self.root, text="Comandos Principales", padding=10)
        frame_comandos.pack(fill="x", padx=10, pady=5)

        ttk.Button(frame_comandos, text="RGB Resistencia (R)", command=lambda: self.backend.enviar_comando("R")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(frame_comandos, text="RGB Toque (T)", command=lambda: self.backend.enviar_comando("T")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame_comandos, text="Pedir Temperatura (ON)", command=lambda: self.backend.enviar_comando("ON")).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(frame_comandos, text="Apagar Resistencia (OFF)", command=lambda: self.backend.enviar_comando("OFF")).grid(row=1, column=1, padx=5, pady=5)

        # --- COLOR RESISTENCIA ---
        frame_resistencia = ttk.LabelFrame(self.root, text="Color de Resistencia", padding=10)
        frame_resistencia.pack(fill="x", padx=10, pady=5)

        colores_res = [("Azul", "escalaAzul"), ("Rojo", "escalaRojo"), 
                       ("Verde", "escalaVerde"), ("Policromático", "escalaPolicromatico")]
        
        for i, (texto, comando) in enumerate(colores_res):
            ttk.Button(frame_resistencia, text=texto, command=lambda c=comando: self.backend.enviar_comando(c)).grid(row=i//2, column=i%2, sticky="ew", padx=5, pady=5)

        # --- COLOR TOQUE ---
        frame_toque = ttk.LabelFrame(self.root, text="Color de Toque", padding=10)
        frame_toque.pack(fill="x", padx=10, pady=5)

        colores_toque = [("Azul", "colorAzul"), ("Rojo", "colorRojo"), ("Verde", "colorVerde"),
                         ("Blanco", "colorBlanco"), ("Violeta", "colorVioleta"), ("Amarillo", "colorAmarillo")]
        
        for i, (texto, comando) in enumerate(colores_toque):
            ttk.Button(frame_toque, text=texto, command=lambda c=comando: self.backend.enviar_comando(c)).grid(row=i//2, column=i%2, sticky="ew", padx=5, pady=5)

        # --- MONITOR TEMPERATURA ---
        frame_temp = ttk.LabelFrame(self.root, text="Monitor de Temperatura", padding=10)
        frame_temp.pack(fill="x", padx=10, pady=10)

        self.lbl_temperatura = ttk.Label(frame_temp, text="-- °C", font=("Arial", 24, "bold"), foreground="blue")
        self.lbl_temperatura.pack(pady=10)

    def actualizar_pantalla(self):
        temp = self.backend.obtener_temperatura()
        if temp != "--":
            self.lbl_temperatura.config(text=f"{temp} °C")
        
        self.root.after(100, self.actualizar_pantalla)

    def on_closing(self):
        self.backend.desconectar()
        self.root.destroy()