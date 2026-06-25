import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import threading
from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial

# =====================================================================
# BACK-END: CONTROLADOR SERIAL (Lógica de Hardware y Datos)
# =====================================================================
class ControladorSerial:
    """Maneja la conexión, lectura de sensores y escritura de PWM por puerto serial."""
    def __init__(self):
        self.conexion = None
        self.hilo_activo = False
        self.ultimo_dato = None
        self.lock = threading.Lock()

    def conectar(self, puerto, baudrate):
        try:
            self.conexion = serial.Serial(puerto, baudrate, timeout=1)
            time.sleep(2) # Tiempo para estabilizar el puerto
            self.hilo_activo = True
            threading.Thread(target=self._bucle_lectura, daemon=True).start()
            return True
        except Exception as e:
            raise Exception(f"No se pudo abrir el puerto: {e}")

    def desconectar(self):
        self.hilo_activo = False
        if self.conexion and self.conexion.is_open:
            self.conexion.close()

    def _bucle_lectura(self):
        """Lectura sincronizada esperando el espacio ' '."""
        while self.hilo_activo:
            if self.conexion and self.conexion.is_open:
                try:
                    # 1. Buscamos tu nuevo byte de cabecera ' ' (espacio)
                    if self.conexion.read(1) == b' ':
                        # 2. Leemos los 2 bytes del ADC
                        data = self.conexion.read(2) 
                        if len(data) == 2:
                            valor_adc = (int.from_bytes(data, byteorder='little') * ( 5.0 / 1023.0) * 100.0) - 5
                            
                            with self.lock:
                                # FACTOR DE CONVERSIÓN (Ajusta según tu LM35 y VCC)
                                # Ejemplo: self.ultimo_dato = (valor_adc * 5.0 / 1024.0) * 100.0
                                self.ultimo_dato = float(valor_adc) 
                except Exception:
                    pass
            time.sleep(0.01)

    def enviar_pwm(self, pwm_valor):
        """Toma un valor entre 0 y 255 y lo envía por serial."""
        if self.conexion and self.conexion.is_open:
            try:
                # Nos aseguramos de que sea un entero y no pase de 255
                pwm_seguro = max(0, min(255, int(pwm_valor)))
                # bytes([valor]) convierte el número en un byte, equivalente a np.uint8().tobytes()
                self.conexion.write(bytes([pwm_seguro]))
            except Exception as e:
                print(f"Error al enviar PWM: {e}")

    def obtener_ultimo_dato(self):
        with self.lock:
            return self.ultimo_dato

    def limpiar_datos(self):
        with self.lock:
            self.ultimo_dato = None


# =====================================================================
# FRONT-END: INTERFAZ GRÁFICA Y CONTROL PID
# =====================================================================
class InterfazControl:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Control Integrado - Temperatura y Motor")
        self.root.geometry("1250x700")
        self.root.configure(bg="#f0f0f0")

        self.backend = ControladorSerial()

        self.sistema_activo = tk.StringVar(value="Temperatura")
        self.ejecutando = False
        self.emergencia = False
        self.puerto_com = tk.StringVar(value="/dev/ttyACM0")
        self.baudrate = 115200
        
        # Referencias
        self.ref_temp = tk.DoubleVar(value=32.5)
        self.ref_speed = tk.DoubleVar(value=350.0)
        self.med_temp = None 
        self.med_speed = 0.0
        
        self.pwm_temp_grafica = 0.0 # Guardará el % (0-100) para mostrar en la gráfica
        self.pwm_motor = 0.0
        
        # Ganancias PID
        self.kp = tk.StringVar(value="5.0")
        self.ki = tk.StringVar(value="0.1")
        self.kd = tk.StringVar(value="1.0")

        # Variables internas para el cálculo matemático del PID
        self.integral_error = 0.0
        self.error_previo = 0.0
        self.tiempo_previo = time.time()

        # Historial para gráficas
        self.max_puntos = 40
        self.tiempo_x = deque(maxlen=self.max_puntos)
        self.historial_pwm_temp = deque(maxlen=self.max_puntos)
        self.historial_pwm_motor = deque(maxlen=self.max_puntos)
        self.historial_temp_med = deque(maxlen=self.max_puntos)
        self.historial_temp_ref = deque(maxlen=self.max_puntos)
        self.historial_speed_med = deque(maxlen=self.max_puntos)
        self.historial_speed_ref = deque(maxlen=self.max_puntos)
        self.contador_tiempo = 0

        self.crear_widgets()
        self.inicializar_graficas()
        self.actualizar_interfaz()

    def crear_widgets(self):
        # [Se mantiene igual que la versión anterior]
        frame_superior = ttk.LabelFrame(self.root, text=" Configuración General y Control ")
        frame_superior.pack(fill="x", padx=15, pady=10)

        ttk.Label(frame_superior, text="Sistema a Controlar:").grid(row=0, column=0, padx=5, pady=10)
        selector = ttk.Combobox(frame_superior, textvariable=self.sistema_activo, 
                                values=["Temperatura", "Motor"], state="readonly", width=12)
        selector.grid(row=0, column=1, padx=5, pady=10)
        selector.bind("<<ComboboxSelected>>", self.cambio_sistema)
        ttk.Separator(frame_superior, orient="vertical").grid(row=0, column=2, sticky="ns", padx=10, pady=5)

        ttk.Label(frame_superior, text="Puerto Serial:").grid(row=0, column=3, padx=5, pady=10)
        ttk.Entry(frame_superior, textvariable=self.puerto_com, width=15).grid(row=0, column=4, padx=5, pady=10)
        ttk.Separator(frame_superior, orient="vertical").grid(row=0, column=5, sticky="ns", padx=10, pady=5)

        self.btn_inicio = ttk.Button(frame_superior, text="▶ Iniciar", command=self.iniciar)
        self.btn_inicio.grid(row=0, column=6, padx=10, pady=10)
        self.btn_parada = ttk.Button(frame_superior, text="⏹ Parar", command=self.parar, state="disabled")
        self.btn_parada.grid(row=0, column=7, padx=10, pady=10)

        estilo_emergencia = ttk.Style()
        estilo_emergencia.configure("Emergencia.TButton", foreground="red", font=('Helvetica', 10, 'bold'))
        self.btn_emergencia = ttk.Button(frame_superior, text="🚨 EMERGENCIA", 
                                         style="Emergencia.TButton", command=self.parada_emergencia)
        self.btn_emergencia.grid(row=0, column=8, padx=20, pady=10)

        frame_izquierdo = tk.Frame(self.root, bg="#f0f0f0", width=350)
        frame_izquierdo.pack(side="left", fill="y", padx=15, pady=5)

        frame_pid = ttk.LabelFrame(frame_izquierdo, text=" Parámetros PID ")
        frame_pid.pack(fill="x", pady=5)
        ttk.Label(frame_pid, text="Kp:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame_pid, textvariable=self.kp, width=7).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frame_pid, text="Ki:").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(frame_pid, textvariable=self.ki, width=7).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(frame_pid, text="Kd:").grid(row=0, column=4, padx=5, pady=5)
        ttk.Entry(frame_pid, textvariable=self.kd, width=7).grid(row=0, column=5, padx=5, pady=5)

        self.frame_ref = ttk.LabelFrame(frame_izquierdo, text=" Referencia Activa del Sistema ")
        self.frame_ref.pack(fill="x", pady=10)

        self.contenedor_temp = tk.Frame(self.frame_ref, bg="#f0f0f0")
        ttk.Label(self.contenedor_temp, text="Setpoint (°C):", font=("Helvetica", 10, "bold")).pack(side="left", padx=10)
        ttk.Entry(self.contenedor_temp, textvariable=self.ref_temp, width=8).pack(side="left", padx=5)
        
        self.contenedor_motor = tk.Frame(self.frame_ref, bg="#f0f0f0")
        ttk.Label(self.contenedor_motor, text="Setpoint (RPM):", font=("Helvetica", 10, "bold")).pack(side="left", padx=10)
        ttk.Entry(self.contenedor_motor, textvariable=self.ref_speed, width=8).pack(side="left", padx=5)
        self.contenedor_temp.pack(fill="x", padx=5, pady=15)

        frame_display = ttk.LabelFrame(frame_izquierdo, text=" Monitoreo en Tiempo Real ")
        frame_display.pack(fill="both", expand=True, pady=5)

        self.lbl_temp_obj = ttk.Label(frame_display, text="Temp. Objetivo: --", font=("Helvetica", 11))
        self.lbl_temp_obj.pack(anchor="w", padx=15, pady=5)
        self.lbl_temp_med = ttk.Label(frame_display, text="Temp. Medida: Esperando datos...", font=("Helvetica", 12, "bold"), foreground="orange")
        self.lbl_temp_med.pack(anchor="w", padx=15, pady=5)
        
        ttk.Separator(frame_display, orient="horizontal").pack(fill="x", padx=10, pady=10)

        self.lbl_speed_obj = ttk.Label(frame_display, text="Vel. Objetivo: --", font=("Helvetica", 11))
        self.lbl_speed_obj.pack(anchor="w", padx=15, pady=5)
        self.lbl_speed_med = ttk.Label(frame_display, text="Vel. Medida: 0.0 RPM", font=("Helvetica", 12, "bold"), foreground="green")
        self.lbl_speed_med.pack(anchor="w", padx=15, pady=5)

        self.frame_derecho = ttk.LabelFrame(self.root, text=" Gráficas Dinámicas del Sistema ")
        self.frame_derecho.pack(side="right", fill="both", expand=True, padx=15, pady=10)

    def inicializar_graficas(self):
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax_t_val = self.fig.add_subplot(221) 
        self.ax_s_val = self.fig.add_subplot(222) 
        self.ax_t_pwm = self.fig.add_subplot(223) 
        self.ax_t_pwm.sharex(self.ax_t_val)
        self.ax_s_pwm = self.fig.add_subplot(224)
        self.ax_s_pwm.sharex(self.ax_s_val)

        self.fig.tight_layout(pad=3.0)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_derecho)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def cambio_sistema(self, event=None):
        if self.sistema_activo.get() == "Temperatura":
            self.contenedor_motor.pack_forget()
            self.contenedor_temp.pack(fill="x", padx=5, pady=15)
        else:
            self.contenedor_temp.pack_forget()
            self.contenedor_motor.pack(fill="x", padx=5, pady=15)

    def iniciar(self):
        if self.emergencia:
            messagebox.showwarning("Alerta", "Desactive el estado de Emergencia.")
            return
        try:
            self.backend.conectar(self.puerto_com.get(), self.baudrate)
            self.backend.limpiar_datos()
            self.med_temp = None
            
            # Reiniciar memoria del PID
            self.integral_error = 0.0
            self.error_previo = 0.0
            self.tiempo_previo = time.time()
            
            self.ejecutando = True
            self.btn_inicio.config(state="disabled")
            self.btn_parada.config(state="normal")
            self.lbl_temp_med.config(text="Temp. Medida: Esperando datos...", foreground="orange")
        except Exception as e:
            messagebox.showerror("Error Serial", str(e))
        
    def parar(self):
        self.ejecutando = False
        self.btn_inicio.config(state="normal")
        self.btn_parada.config(state="disabled")
        self.pwm_temp_grafica = 0.0
        self.pwm_motor = 0.0
        # Apagamos la resistencia por seguridad enviando un 0
        self.backend.enviar_pwm(0)
        self.backend.desconectar()

    def parada_emergencia(self):
        self.emergencia = True
        self.parar()
        self.lbl_temp_med.config(text="Temp. Medida: ALERTA CRÍTICA", foreground="red")
        self.lbl_speed_med.config(text="Vel. Medida: 0.0 RPM (BLOQUEADO)", foreground="red")
        messagebox.showerror("🚨 PARADA DE EMERGENCIA", "¡Sistema detenido inmediatamente!")
        self.emergencia = False 

    # ---------------------------------------------------------
    # EL NUEVO MÉTODO PID
    # ---------------------------------------------------------
    def calcular_pid(self, setpoint, valor_medido):
        """Aplica la matemática del PID y devuelve un PWM entre 0 y 255"""
        tiempo_actual = time.time()
        dt = tiempo_actual - self.tiempo_previo
        if dt <= 0: dt = 0.01 # Evita errores de división por cero

        error = setpoint - valor_medido
        
        try:
            kp = float(self.kp.get())
            ki = float(self.ki.get())
            kd = float(self.kd.get())
        except ValueError:
            kp, ki, kd = 0.0, 0.0, 0.0

        # Acción Proporcional
        P = kp * error
        
        # Acción Integral (Sumatoria del error)
        self.integral_error += error * dt
        # Limitar la integral (Anti-Windup) para evitar que crezca infinitamente
        self.integral_error = max(-255, min(255, self.integral_error))
        I = ki * self.integral_error
        
        # Acción Derivativa (Tasa de cambio del error)
        D = kd * ((error - self.error_previo) / dt)

        # Ecuación completa
        salida = P + I + D

        # Guardar historial para el siguiente cálculo
        self.error_previo = error
        self.tiempo_previo = tiempo_actual

        # Restringir matemáticamente entre 0 y 255
        salida_pwm = max(0, min(255, int(salida)))
        
        return salida_pwm
    # ---------------------------------------------------------

    def actualizar_interfaz(self):
        if self.ejecutando:
            self.contador_tiempo += 1
            nuevo_dato = self.backend.obtener_ultimo_dato()
            
            if nuevo_dato is not None:
                self.med_temp = nuevo_dato
            
            try: target_t = max(30.0, min(35.0, self.ref_temp.get()))
            except tk.TclError: target_t = 32.5
            try: target_s = max(0.0, min(750.0, self.ref_speed.get()))
            except tk.TclError: target_s = 350.0

            self.lbl_temp_obj.config(text=f"Temp. Objetivo: {target_t:.2f} °C")
            self.lbl_speed_obj.config(text=f"Vel. Objetivo: {target_s:.1f} RPM")

            # --- CONTROL Y ENVÍO ---
            if self.sistema_activo.get() == "Temperatura":
                self.pwm_motor = 0.0
                self.med_speed = max(0.0, self.med_speed - 10)
                
                if self.med_temp is not None:
                    # 1. Calculamos el PID
                    pwm_salida_cruda = self.calcular_pid(target_t, self.med_temp)
                    
                    # 2. Enviamos el valor (0-255) al Arduino
                    self.backend.enviar_pwm(pwm_salida_cruda)
                    
                    # 3. Mapeamos a porcentaje (0-100%) solo para que la gráfica se vea bonita
                    self.pwm_temp_grafica = (pwm_salida_cruda / 255.0) * 100.0
            else:
                error_s = target_s - self.med_speed
                self.pwm_motor = max(0.0, min(100.0, (target_s / 7.5) + error_s * 0.1))
                self.med_speed += (error_s * 0.3) + random.uniform(-2, 2)
                if self.med_speed < 0: self.med_speed = 0.0
                
                self.pwm_temp_grafica = 0.0
                self.backend.enviar_pwm(0) # Apaga la resistencia si estamos en modo motor

            # --- ACTUALIZAR ETIQUETAS Y GRÁFICAS ---
            if self.med_temp is not None:
                self.lbl_temp_med.config(text=f"Temp. Medida: {self.med_temp:.2f} °C", foreground="blue")
            
            self.lbl_speed_med.config(text=f"Vel. Medida: {self.med_speed:.1f} RPM", foreground="green")

            valor_temp_grafica = self.med_temp if self.med_temp is not None else 0.0
            
            self.tiempo_x.append(self.contador_tiempo)
            self.historial_temp_ref.append(target_t)
            self.historial_temp_med.append(valor_temp_grafica)
            self.historial_pwm_temp.append(self.pwm_temp_grafica)
            self.historial_speed_ref.append(target_s)
            self.historial_speed_med.append(self.med_speed)
            self.historial_pwm_motor.append(self.pwm_motor)

            t_list = list(self.tiempo_x)

            self.ax_t_val.clear()
            self.ax_t_val.set_title("Temperatura (Datos Reales)")
            self.ax_t_val.set_ylabel("°C")
            self.ax_t_val.set_ylim(25, 40)
            self.ax_t_val.grid(True)
            self.ax_t_val.plot(t_list, list(self.historial_temp_ref), 'k--', label="Setpoint")
            self.ax_t_val.plot(t_list, list(self.historial_temp_med), 'b-', linewidth=2, label="Medida")
            self.ax_t_val.legend(loc="upper left")

            self.ax_s_val.clear()
            self.ax_s_val.set_title("Evolución de Velocidad")
            self.ax_s_val.set_ylabel("RPM")
            self.ax_s_val.set_ylim(-20, 800)
            self.ax_s_val.grid(True)
            self.ax_s_val.plot(t_list, list(self.historial_speed_ref), 'k--', label="Setpoint")
            self.ax_s_val.plot(t_list, list(self.historial_speed_med), 'g-', linewidth=2, label="Medida")

            self.ax_t_pwm.clear()
            self.ax_t_pwm.set_title("PWM Resistencia (%)")
            self.ax_t_pwm.set_ylim(-5, 105)
            self.ax_t_pwm.grid(True)
            self.ax_t_pwm.plot(t_list, list(self.historial_pwm_temp), 'r-', linewidth=2)

            self.ax_s_pwm.clear()
            self.ax_s_pwm.set_title("PWM Motor (%)")
            self.ax_s_pwm.set_ylim(-5, 105)
            self.ax_s_pwm.grid(True)
            self.ax_s_pwm.plot(t_list, list(self.historial_pwm_motor), color="orange", linewidth=2)

            self.canvas.draw()

        self.root.after(300, self.actualizar_interfaz)

    def on_closing(self):
        # Se envía un 0 para apagar la resistencia por precaución al cerrar el programa
        self.backend.enviar_pwm(0)
        self.backend.desconectar()
        self.root.destroy()

if __name__ == "__main__":
    ventana = tk.Tk()
    app = InterfazControl(ventana)
    ventana.protocol("WM_DELETE_WINDOW", app.on_closing)
    ventana.mainloop()