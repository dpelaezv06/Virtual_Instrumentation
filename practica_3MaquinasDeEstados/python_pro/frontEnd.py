import tkinter as tk
from tkinter import ttk, messagebox

class ArduinoApp:
    def __init__(self, root, backend):
        self.root = root
        self.backend = backend
        
        self.root.title("Práctica 3 - Panel de Control Instrumentación Virtual")
        self.root.geometry("500x550")
        self.root.resizable(False, False)

        # Conectar al backend
        exito, mensaje = self.backend.conectar()
        if not exito:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar al Arduino.\n\nDetalle: {mensaje}")

        self.crear_interfaz()
        self.actualizar_pantalla()

    def crear_interfaz(self):
        # --- SECCIÓN SUPERIOR: MONITOR DE TEMPERATURA Y LED VIRTUAL ---
        frame_superior = ttk.LabelFrame(self.root, text="Monitor de Estado (Panel Frontal)", padding=15)
        frame_superior.pack(fill="x", padx=10, pady=10)

        # Sub-cuadro para la temperatura
        frame_temp = ttk.Frame(frame_superior)
        frame_temp.pack(side="left", expand=True)
        ttk.Label(frame_temp, text="Temperatura LM35:", font=("Arial", 10, "bold")).pack()
        
        # Etiqueta adaptada para contener el formato ± u(x)
        self.lbl_temperatura = ttk.Label(frame_temp, text="-- ± 0.35 °C", font=("Arial", 20, "bold"), foreground="#d9534f")
        self.lbl_temperatura.pack(pady=5)

        # Sub-cuadro para el cuadrado LED virtual
        frame_led = ttk.Frame(frame_superior)
        frame_led.pack(side="right", expand=True)
        ttk.Label(frame_led, text="Estado LED RGB:", font=("Arial", 10, "bold")).pack()
        
        # El cuadrado del LED usando Canvas
        self.canvas_led = tk.Canvas(frame_led, width=60, height=60, bg="white", highlightthickness=1, highlightbackground="black")
        self.cuadrado_led = self.canvas_led.create_rectangle(10, 10, 50, 50, fill="gray", outline="black", width=2)
        self.canvas_led.pack(pady=5)

        # --- SECCIÓN INFERIOR: SELECTOR DE MODOS (PESTAÑAS) ---
        ttk.Label(self.root, text="Seleccione el modo de operación:", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(10, 0))
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Enlazar evento cuando se cambia de pestaña para mandar el comando 'T' o 'R'
        self.notebook.bind("<<NotebookTabChanged>>", self.al_cambiar_pestaña)

        # Crear las dos pestañas
        self.tab_toque = ttk.Frame(self.notebook, padding=15)
        self.tab_temperatura = ttk.Frame(self.notebook, padding=15)

        self.notebook.add(self.tab_toque, text=" 👆 Modo Toque / Hall ")
        self.notebook.add(self.tab_temperatura, text=" 🌡️ Modo Temperatura LM35 ")

        self._construir_tab_toque()
        self._construir_tab_temperatura()

    def _construir_tab_toque(self):
        ttk.Label(self.tab_toque, text="Selecciona el color al detectar el toque:", font=("Arial", 10)).pack(pady=10)
        
        frame_grid = ttk.Frame(self.tab_toque)
        frame_grid.pack()

        # Botones actualizados para modo toque (6 botones en cuadrícula 3x2)
        colores = [
            ("Azul", "colorAzul"),
            ("Rojo", "colorRojo"),
            ("Verde", "colorVerde"),
            ("Violeta", "colorVioleta"),
            ("Blanco", "colorBlanco"),
            ("Amarillo", "colorAmarillo")
        ]
        
        for i, (texto, comando) in enumerate(colores):
            btn = tk.Button(frame_grid, text=texto, width=15, pady=5, command=lambda c=comando: self.backend.enviar_comando(c))
            btn.grid(row=i//2, column=i%2, padx=10, pady=10)

    def _construir_tab_temperatura(self):
        # 1. Selector de colores de temperatura
        ttk.Label(self.tab_temperatura, text="Escala de color por temperatura:", font=("Arial", 10)).pack(pady=5)
        frame_grid = ttk.Frame(self.tab_temperatura)
        frame_grid.pack(pady=5)

        colores = [
            ("Azul", "escalaAzul"),
            ("Verde", "escalaVerde"),
            ("Rojo", "escalaRojo"),
            ("Policromático", "escalaPolicromatico")
        ]
        for i, (texto, comando) in enumerate(colores):
            btn = tk.Button(frame_grid, text=texto, width=15, pady=5, command=lambda c=comando: self.backend.enviar_comando(c))
            btn.grid(row=i//2, column=i%2, padx=10, pady=5)

        # 2. Suiche (Interruptor) para encender/apagar la resistencia y solicitar temperatura
        ttk.Separator(self.tab_temperatura, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(self.tab_temperatura, text="Control de Resistencia Calefactora:", font=("Arial", 10, "bold")).pack()

        frame_suiche = ttk.Frame(self.tab_temperatura)
        frame_suiche.pack(pady=10)

        # Botón para Encender Resistencia + Pedir Temp (ON)
        btn_on = tk.Button(frame_suiche, text="🔥 ENCENDER (ON)", bg="#d9534f", fg="white", font=("Arial", 9, "bold"), width=16, pady=5,
                           command=lambda: self.backend.enviar_comando("ON"))
        btn_on.grid(row=0, column=0, padx=10)

        # Botón para Apagar Resistencia (OFF)
        btn_off = tk.Button(frame_suiche, text="❄️ APAGAR (OFF)", bg="#5cb85c", fg="white", font=("Arial", 9, "bold"), width=16, pady=5,
                            command=lambda: self.backend.enviar_comando("OFF"))
        btn_off.grid(row=0, column=1, padx=10)

    def al_cambiar_pestaña(self, event):
        """Envía automáticamente el comando del modo al cambiar de pestaña."""
        pestaña_actual = self.notebook.index("current")
        if pestaña_actual == 0:
            self.backend.enviar_comando("T") # Activar modo Toque en Arduino
        elif pestaña_actual == 1:
            self.backend.enviar_comando("R") # Activar modo Resistencia/Temp en Arduino

    def actualizar_pantalla(self):
        """Consulta los datos al backend y refresca la pantalla cada 50ms exactos."""
        temp, desv, color = self.backend.obtener_datos()
        
        # Actualizar texto de temperatura con su respectiva incertidumbre
        if temp != "--":
            self.lbl_temperatura.config(text=f"{temp} ± {desv} °C")
        else:
            self.lbl_temperatura.config(text="-- ± 0.00 °C")
            
        # Actualizar el color del cuadrado del LED
        self.canvas_led.itemconfig(self.cuadrado_led, fill=color)
        
        # PROGRAMADO A 50MS
        self.root.after(100, self.actualizar_pantalla)

    def on_closing(self):
        self.backend.desconectar()
        self.root.destroy()