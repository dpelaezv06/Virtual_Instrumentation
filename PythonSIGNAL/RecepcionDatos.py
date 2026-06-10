import tkinter as tk
from tkinter import ttk, messagebox
import random
import csv
import time
from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial # <-- Importamos PySerial
import threading # <-- Importamos Threading para lectura en segundo plano

class InterfazControl:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Control Integrado - Temperatura y Motor N20")
        self.root.geometry("1250x700")
        self.root.configure(bg="#f0f0f0")

        # --- Variables de control y estado ---
        self.sistema_activo = tk.StringVar(value="Temperatura")
        self.ejecutando = False
        self.emergencia = False
        
        # --- Configuración Serial ---
        self.puerto_com = tk.StringVar(value="/dev/ttyACM0") # Puerto por defecto de tu código
        self.baudrate = 115200 # Velocidad de tu código
        self.serial_conn = None
        self.hilo_activo = True # Bandera para mantener vivo el hilo
        
        # Referencias y Valores Medidos
        self.ref_temp = tk.DoubleVar(value=32.5)
        self.ref_speed = tk.DoubleVar(value=350.0)
        self.med_temp = 25.0 # ESTE VALOR AHORA SE ACTUALIZARÁ POR SERIAL
        self.med_speed = 0.0
        
        # Variables de los lazos PWM (%)
        self.pwm_temp = 0.0
        self.pwm_motor = 0.0
        
        # Ganancias PID (Modificables)
        self.kp = tk.StringVar(value="1.5")
        self.ki = tk.StringVar(value="0.05")
        self.kd = tk.StringVar(value="0.2")

        # Historial de datos para las gráficas
        self.max_puntos = 40
        self.tiempo_x = deque(maxlen=self.max_puntos)
        self.historial_pwm_temp = deque(maxlen=self.max_puntos)
        self.historial_pwm_motor = deque(maxlen=self.max_puntos)
        self.historial_temp_med = deque(maxlen=self.max_puntos)
        self.historial_temp_ref = deque(maxlen=self.max_puntos)
        self.historial_speed_med = deque(maxlen=self.max_puntos)
        self.historial_speed_ref = deque(maxlen=self.max_puntos)
        self.contador_tiempo = 0

        # Crear estructura de la GUI
        self.crear_widgets()
        self.inicializar_graficas()
        
        # Iniciar el Hilo de lectura Serial en segundo plano (Filosofía de Polling continuo)
        self.hilo_serial = threading.Thread(target=self.lectura_serial_continua, daemon=True)
        self.hilo_serial.start()
        
        # Iniciar el bucle de actualización visual en tiempo real
        self.actualizar_sistema()

    def crear_widgets(self):
        # -----------------------------------------------------------------
        # PANEL SUPERIOR: SELECCIÓN DE SISTEMA, SERIAL Y BOTONES
        # -----------------------------------------------------------------
        frame_superior = ttk.LabelFrame(self.root, text=" Configuración General y Control ")
        frame_superior.pack(fill="x", padx=15, pady=10)

        # Selección de sistema
        ttk.Label(frame_superior, text="Sistema a Controlar:").grid(row=0, column=0, padx=5, pady=10)
        selector = ttk.Combobox(frame_superior, textvariable=self.sistema_activo, 
                                values=["Temperatura", "Motor"], state="readonly", width=12)
        selector.grid(row=0, column=1, padx=5, pady=10)
        selector.bind("<<ComboboxSelected>>", self.cambio_sistema)
        
        ttk.Separator(frame_superior, orient="vertical").grid(row=0, column=2, sticky="ns", padx=10, pady=5)

        # Configuración Serial
        ttk.Label(frame_superior, text="Puerto Serial:").grid(row=0, column=3, padx=5, pady=10)
        ttk.Entry(frame_superior, textvariable=self.puerto_com, width=15).grid(row=0, column=4, padx=5, pady=10)

        ttk.Separator(frame_superior, orient="vertical").grid(row=0, column=5, sticky="ns", padx=10, pady=5)

        # Botones de Control
        self.btn_inicio = ttk.Button(frame_superior, text="▶ Iniciar", command=self.iniciar)
        self.btn_inicio.grid(row=0, column=6, padx=10, pady=10)

        self.btn_parada = ttk.Button(frame_superior, text="⏹ Parar", command=self.parar, state="disabled")
        self.btn_parada.grid(row=0, column=7, padx=10, pady=10)

        # Botón de Emergencia
        estilo_emergencia = ttk.Style()
        estilo_emergencia.configure("Emergencia.TButton", foreground="red", font=('Helvetica', 10, 'bold'))
        self.btn_emergencia = ttk.Button(frame_superior, text="🚨 EMERGENCIA", 
                                         style="Emergencia.TButton", command=self.parada_emergencia)
        self.btn_emergencia.grid(row=0, column=8, padx=20, pady=10)

        # -----------------------------------------------------------------
        # PANEL IZQUIERDO Y DERECHO (Igual a la versión anterior)
        # -----------------------------------------------------------------
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
        ttk.Label(self.contenedor_temp, text="(30 - 35)").pack(side="left", padx=5)

        self.contenedor_motor = tk.Frame(self.frame_ref, bg="#f0f0f0")
        ttk.Label(self.contenedor_motor, text="Setpoint (RPM):", font=("Helvetica", 10, "bold")).pack(side="left", padx=10)
        ttk.Entry(self.contenedor_motor, textvariable=self.ref_speed, width=8).pack(side="left", padx=5)
        ttk.Label(self.contenedor_motor, text="(0 - 750)").pack(side="left", padx=5)

        self.contenedor_temp.pack(fill="x", padx=5, pady=15)

        frame_display = ttk.LabelFrame(frame_izquierdo, text=" Monitoreo en Tiempo Real ")
        frame_display.pack(fill="both", expand=True, pady=5)

        self.lbl_temp_obj = ttk.Label(frame_display, text="Temp. Objetivo: 32.50 °C", font=("Helvetica", 11))
        self.lbl_temp_obj.pack(anchor="w", padx=15, pady=5)
        self.lbl_temp_med = ttk.Label(frame_display, text="Temp. Medida: 25.00 °C", font=("Helvetica", 12, "bold"), foreground="blue")
        self.lbl_temp_med.pack(anchor="w", padx=15, pady=5)
        
        ttk.Separator(frame_display, orient="horizontal").pack(fill="x", padx=10, pady=10)

        self.lbl_speed_obj = ttk.Label(frame_display, text="Vel. Objetivo: 350.0 RPM", font=("Helvetica", 11))
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
        self.ax_t_pwm.sharex(self.ax_t_val) # Sincroniza el eje X de Temp
        self.ax_s_pwm = self.fig.add_subplot(224)
        self.ax_s_pwm.sharex(self.ax_s_val) # Sincroniza el eje X de Vel

        self.fig.tight_layout(pad=3.0)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_derecho)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # -----------------------------------------------------------------
    # LÓGICA DEL PUERTO SERIAL (HILO EN SEGUNDO PLANO)
    # -----------------------------------------------------------------
    def lectura_serial_continua(self):
        """ Este es el equivalente a tu While True de referencia.
        Corre en segundo plano sin congelar la interfaz visual """
        while self.hilo_activo:
            if self.ejecutando and self.serial_conn and self.serial_conn.is_open:
                try:
                    # Leemos los datos que lleguen. 
                    # NOTA: Asumo que el micro envía la temp en texto terminada en salto de linea (ej: "25.4\n")
                    # Si envias bytes crudos como en tu script (read(2)), debes cambiar esta linea a:
                    # data = self.serial_conn.read(2)
                    # valor_ADC = int.from_bytes(data, byteorder='little')
                    # self.med_temp = valor_ADC * factor_de_conversion_a_grados
                    
                    if self.serial_conn.in_waiting > 0:
                        # el miro envia la temperatura en un byte
                        linea = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        if linea:
                            try:
                                self.med_temp = float(linea) # Actualiza la variable con el dato REAL
                            except ValueError:
                                pass # Si llega basura por el serial, la ignoramos
                except Exception as e:
                    print(f"Error leyendo serial: {e}")
                    time.sleep(0.1)
            else:
                time.sleep(0.1) # Pausa para no saturar el procesador si no estamos ejecutando

    # -----------------------------------------------------------------
    # LÓGICA DE CONTROL DE INTERFAZ
    # -----------------------------------------------------------------
    def cambio_sistema(self, event=None):
        if self.sistema_activo.get() == "Temperatura":
            self.contenedor_motor.pack_forget()
            self.contenedor_temp.pack(fill="x", padx=5, pady=15)
        else:
            self.contenedor_temp.pack_forget()
            self.contenedor_motor.pack(fill="x", padx=5, pady=15)

    def iniciar(self):
        if self.emergencia:
            messagebox.showwarning("Alerta", "Desactive el estado de Emergencia antes de iniciar.")
            return
        
        # Intentar conectar el puerto serial
        try:
            if not self.serial_conn or not self.serial_conn.is_open:
                self.serial_conn = serial.Serial(self.puerto_com.get(), self.baudrate, timeout=1)
                time.sleep(1) # Tiempo de estabilización como en tu script
        except Exception as e:
            messagebox.showerror("Error de Puerto Serial", f"No se pudo abrir el puerto {self.puerto_com.get()}.\nVerifique la conexión.\n\nDetalle: {e}")
            return

        self.ejecutando = True
        self.btn_inicio.config(state="disabled")
        self.btn_parada.config(state="normal")
        
        with open("datos_experimentales.csv", mode="w", newline="") as f:
            escritor = csv.writer(f)
            escritor.writerow(["Timestamp", "Sistema_Activo", "Ref_Temp", "Med_Temp", "PWM_Temp", "Ref_Vel", "Med_Vel", "PWM_Motor"])

    def parar(self):
        self.ejecutando = False
        self.btn_inicio.config(state="normal")
        self.btn_parada.config(state="disabled")
        self.pwm_temp = 0.0
        self.pwm_motor = 0.0
        
        # Cerrar el puerto serial de forma segura
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def parada_emergencia(self):
        self.emergencia = True
        self.parar() # Usa la lógica de parar para detener variables y el serial
        self.lbl_temp_med.config(text="Temp. Medida: ALERTA CRÍTICA", foreground="red")
        self.lbl_speed_med.config(text="Vel. Medida: 0.0 RPM (BLOQUEADO)", foreground="red")
        messagebox.showerror("🚨 PARADA DE EMERGENCIA", "¡Sistema detenido inmediatamente!")
        self.emergencia = False 

    def actualizar_sistema(self):
        # Esta función corre en el Hilo Principal. Actualiza gráficos basándose en lo que lee el Hilo Serial.
        if self.ejecutando:
            self.contador_tiempo += 1
            
            try:
                target_t = max(30.0, min(35.0, self.ref_temp.get()))
            except tk.TclError:
                target_t = 32.5

            try:
                target_s = max(0.0, min(750.0, self.ref_speed.get()))
            except tk.TclError:
                target_s = 350.0

            self.lbl_temp_obj.config(text=f"Temp. Objetivo: {target_t:.2f} °C")
            self.lbl_speed_obj.config(text=f"Vel. Objetivo: {target_s:.1f} RPM")

            # --- SIMULACIÓN Y CONTROL PID (Software) ---
            if self.sistema_activo.get() == "Temperatura":
                error_t = target_t - self.med_temp # Calcula el error usando la temp REAL del serial
                
                # --- AQUI IRIA TU CÓDIGO PID QUE ENVIA EL PWM POR SERIAL ---
                # Ejemplo (Aun no envia, solo calcula para la grafica):
                self.pwm_temp = max(0.0, min(100.0, error_t * float(self.kp.get()) * 20))
                
                # Motor inactivo
                self.pwm_motor = 0.0
                self.med_speed = max(0.0, self.med_speed - 10)
            else:
                # El motor sigue simulado por el momento
                error_s = target_s - self.med_speed
                self.pwm_motor = max(0.0, min(100.0, (target_s / 7.5) + error_s * 0.1))
                self.med_speed += (error_s * 0.3) + random.uniform(-2, 2)
                if self.med_speed < 0: self.med_speed = 0.0
                
                self.pwm_temp = 0.0
                # La temperatura med_temp se sigue actualizando en segundo plano por el serial
                # así que la gráfica seguirá mostrando la temperatura ambiente

            self.lbl_temp_med.config(text=f"Temp. Medida: {self.med_temp:.2f} °C", foreground="blue")
            self.lbl_speed_med.config(text=f"Vel. Medida: {self.med_speed:.1f} RPM", foreground="green")

            # Guardar en historiales
            self.tiempo_x.append(self.contador_tiempo)
            
            self.historial_temp_ref.append(target_t)
            self.historial_temp_med.append(self.med_temp)
            self.historial_pwm_temp.append(self.pwm_temp)

            self.historial_speed_ref.append(target_s)
            self.historial_speed_med.append(self.med_speed)
            self.historial_pwm_motor.append(self.pwm_motor)

            # CSV
            with open("datos_experimentales.csv", mode="a", newline="") as f:
                escritor = csv.writer(f)
                escritor.writerow([time.strftime("%H:%M:%S"), self.sistema_activo.get(), 
                                  target_t, f"{self.med_temp:.2f}", f"{self.pwm_temp:.1f}",
                                  target_s, f"{self.med_speed:.1f}", f"{self.pwm_motor:.1f}"])

            # ---- RE-DIBUJAR GRÁFICAS ----
            t_list = list(self.tiempo_x)

            # 1. Temperatura
            self.ax_t_val.clear()
            self.ax_t_val.set_title("Evolución de Temperatura (Datos Reales Serial)")
            self.ax_t_val.set_ylabel("°C")
            self.ax_t_val.grid(True)
            self.ax_t_val.plot(t_list, list(self.historial_temp_ref), 'k--', label="Setpoint")
            self.ax_t_val.plot(t_list, list(self.historial_temp_med), 'b-', linewidth=2, label="Medida")
            self.ax_t_val.legend(loc="upper left")

            # 2. Velocidad (Aún simulado)
            self.ax_s_val.clear()
            self.ax_s_val.set_title("Evolución de Velocidad")
            self.ax_s_val.set_ylabel("RPM")
            self.ax_s_val.set_ylim(-20, 800)
            self.ax_s_val.grid(True)
            self.ax_s_val.plot(t_list, list(self.historial_speed_ref), 'k--', label="Setpoint")
            self.ax_s_val.plot(t_list, list(self.historial_speed_med), 'g-', linewidth=2, label="Medida")
            self.ax_s_val.legend(loc="upper left")

            # 3. PWM Temp
            self.ax_t_pwm.clear()
            self.ax_t_pwm.set_title("Esfuerzo de Control (Resistencia)")
            self.ax_t_pwm.set_ylabel("PWM (%)")
            self.ax_t_pwm.set_ylim(-5, 105)
            self.ax_t_pwm.grid(True)
            self.ax_t_pwm.plot(t_list, list(self.historial_pwm_temp), 'r-', linewidth=2)

            # 4. PWM Motor
            self.ax_s_pwm.clear()
            self.ax_s_pwm.set_title("Esfuerzo de Control (Motor)")
            self.ax_s_pwm.set_ylabel("PWM (%)")
            self.ax_s_pwm.set_ylim(-5, 105)
            self.ax_s_pwm.grid(True)
            self.ax_s_pwm.plot(t_list, list(self.historial_pwm_motor), color="orange", linewidth=2)

            self.canvas.draw()

        self.root.after(300, self.actualizar_sistema) # Lazo de Polling Visual (Actualiza la GUI cada 300ms)

    def on_closing(self):
        """ Función para cerrar todo de forma limpia """
        self.hilo_activo = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.root.destroy()

if __name__ == "__main__":
    ventana = tk.Tk()
    app = InterfazControl(ventana)
    ventana.protocol("WM_DELETE_WINDOW", app.on_closing) # Cierra los hilos al presionar la 'X' de la ventana
    ventana.mainloop()