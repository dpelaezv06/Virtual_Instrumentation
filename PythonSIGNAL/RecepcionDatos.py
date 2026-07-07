import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import threading
from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

try:
    from serial import Serial
except ImportError as exc:
    raise ImportError(
        "Falta pyserial. Instala la librería con: .venv/bin/python -m pip install pyserial"
    ) from exc

# =====================================================================
# BACK-END: CONTROLADOR SERIAL (Lógica de Hardware y Datos)
# =====================================================================
class ControladorSerial:
    """Maneja la conexión, lectura de sensores y escritura de PWM por puerto serial."""
    def __init__(self):
        self.conexion = None
        self.hilo_activo = False
        self.ultimo_dato = None
        self.temperatura_cruda = None
        self.velocidad_cruda = None
        self.lock = threading.Lock()
        self.ultimo_pwm_enviado = None
        self.ultimo_tipo_enviado = None
        self.pendiente_ack = False
        self.ack_timestamp = 0.0
        self.ack_timeout = 0.5
        self.ultima_orden = b""

    def conectar(self, puerto, baudrate):
        try:
            self.conexion = Serial(puerto, baudrate, timeout=1)
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
        """Lee datos de forma eficiente sin retrasos artificiales."""
        while self.hilo_activo:
            if self.conexion and self.conexion.is_open:
                try:
                    # readline() espera de forma nativa a que llegue el '\n'
                    linea = self.conexion.readline()
                    if not linea:
                        continue

                    dato = linea.decode("utf-8", errors="ignore").strip()
                    if not dato:
                        continue

                    if dato.startswith("ack_t"):
                        with self.lock:
                            if self.ultimo_tipo_enviado == "t":
                                self.pendiente_ack = False
                    
                    elif dato.startswith("ack_v"):
                        with self.lock:
                            if self.ultimo_tipo_enviado == "v":
                                self.pendiente_ack = False

                    elif dato.startswith("t_"):
                        try:
                            valor = float(dato[2:])
                            with self.lock:
                                self.temperatura_cruda = valor
                                self.ultimo_dato = valor
                        except ValueError:
                            continue

                    elif dato.startswith("v_"):
                        try:
                            valor = float(dato[2:])
                            with self.lock:
                                self.velocidad_cruda = valor
                                self.ultimo_dato = valor
                        except ValueError:
                            continue

                except Exception:
                    pass
            else:
                time.sleep(0.1) # Si no está abierto el puerto, espera un poco

    def enviar_pwm(self, pwm_valor, tipo=None):
        """Envía un PWM sobre serial usando prefijos t_ o v_ y espera ack para no saturar el puerto."""
        if not self.conexion or not self.conexion.is_open:
            return

        if tipo not in ("t", "v"):
            return

        pwm_seguro = max(0, min(255, int(pwm_valor)))
        mensaje = f"{tipo}_{pwm_seguro}\n".encode("utf-8")

        try:
            ahora = time.time()
            with self.lock:
                if self.pendiente_ack:
                    if self.ultima_orden == mensaje and (ahora - self.ack_timestamp) < self.ack_timeout:
                        return
                    if (ahora - self.ack_timestamp) >= self.ack_timeout:
                        self.pendiente_ack = False

                if self.ultimo_tipo_enviado == tipo and self.ultimo_pwm_enviado == pwm_seguro and not self.pendiente_ack:
                    return

                self.conexion.write(mensaje)
                self.ultimo_pwm_enviado = pwm_seguro
                self.ultimo_tipo_enviado = tipo
                self.ultima_orden = mensaje
                self.pendiente_ack = True
                self.ack_timestamp = ahora
        except Exception as e:
            print(f"Error al enviar PWM: {e}")

    def obtener_temperatura_cruda(self):
        with self.lock:
            return self.temperatura_cruda

    def obtener_velocidad_cruda(self):
        with self.lock:
            return self.velocidad_cruda

    def obtener_ultimo_dato(self):
        with self.lock:
            return self.ultimo_dato

    def obtener_pwm_actual(self, tipo):
        """Devuelve el último valor de PWM realmente escrito por el puerto serial
        para el tipo indicado ('t' o 'v'), o None si aún no se ha enviado nada.
        Esto es lo que hay que graficar, no el valor que el PID acaba de calcular,
        ya que enviar_pwm() puede omitir la escritura (dedupe/ack) sin avisar al caller."""
        with self.lock:
            if self.ultimo_tipo_enviado == tipo:
                return self.ultimo_pwm_enviado
            return None

    def limpiar_datos(self):
        with self.lock:
            self.ultimo_dato = None
            self.temperatura_cruda = None
            self.velocidad_cruda = None


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
        self.target_t = 32.5
        self.target_s = 350.0
        
        # Ganancias PID por sistema
        self.kp_temp = tk.StringVar(value="5.0")
        self.ki_temp = tk.StringVar(value="0.1")
        self.kd_temp = tk.StringVar(value="1.0")

        self.kp_motor = tk.StringVar(value="1.5")
        self.ki_motor = tk.StringVar(value="0.05")
        self.kd_motor = tk.StringVar(value="0.3")

        # Variables internas para el cálculo matemático del PID
        self.integral_error_temp = 0.0
        self.error_previo_temp = 0.0
        self.tiempo_previo_temp = time.time()

        self.integral_error_motor = 0.0
        self.error_previo_motor = 0.0
        self.tiempo_previo_motor = time.time()

        # Historial para gráficas
        self.max_puntos = 120
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
        self.bucle_control()
        self.bucle_grafica()

    def crear_widgets(self):
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

        self.frame_pid_temp = tk.Frame(frame_pid, bg="#f0f0f0")
        self.frame_pid_temp.pack(fill="x", padx=5, pady=5)
        ttk.Label(self.frame_pid_temp, text="PID Temperatura").grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 5))
        ttk.Label(self.frame_pid_temp, text="Kp:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(self.frame_pid_temp, textvariable=self.kp_temp, width=7).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(self.frame_pid_temp, text="Ki:").grid(row=1, column=2, padx=5, pady=5)
        ttk.Entry(self.frame_pid_temp, textvariable=self.ki_temp, width=7).grid(row=1, column=3, padx=5, pady=5)
        ttk.Label(self.frame_pid_temp, text="Kd:").grid(row=1, column=4, padx=5, pady=5)
        ttk.Entry(self.frame_pid_temp, textvariable=self.kd_temp, width=7).grid(row=1, column=5, padx=5, pady=5)

        self.frame_pid_motor = tk.Frame(frame_pid, bg="#f0f0f0")
        self.frame_pid_motor.pack(fill="x", padx=5, pady=5)
        self.frame_pid_motor.pack_forget()
        ttk.Label(self.frame_pid_motor, text="PID Motor").grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 5))
        ttk.Label(self.frame_pid_motor, text="Kp:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(self.frame_pid_motor, textvariable=self.kp_motor, width=7).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(self.frame_pid_motor, text="Ki:").grid(row=1, column=2, padx=5, pady=5)
        ttk.Entry(self.frame_pid_motor, textvariable=self.ki_motor, width=7).grid(row=1, column=3, padx=5, pady=5)
        ttk.Label(self.frame_pid_motor, text="Kd:").grid(row=1, column=4, padx=5, pady=5)
        ttk.Entry(self.frame_pid_motor, textvariable=self.kd_motor, width=7).grid(row=1, column=5, padx=5, pady=5)

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
        self.lbl_temp_obj.pack(anchor="w", padx=15, pady=2)
        self.lbl_temp_med = ttk.Label(frame_display, text="Temp. Medida: Esperando datos...", font=("Helvetica", 12, "bold"), foreground="orange")
        self.lbl_temp_med.pack(anchor="w", padx=15, pady=2)
        
        # Nuevas etiquetas para errores de Temperatura
        self.lbl_temp_err_abs = ttk.Label(frame_display, text="Error Absoluto: --", font=("Helvetica", 10))
        self.lbl_temp_err_abs.pack(anchor="w", padx=15, pady=1)
        self.lbl_temp_err_rel = ttk.Label(frame_display, text="Error Relativo: --", font=("Helvetica", 10))
        self.lbl_temp_err_rel.pack(anchor="w", padx=15, pady=1)

        ttk.Separator(frame_display, orient="horizontal").pack(fill="x", padx=10, pady=10)

        self.lbl_speed_obj = ttk.Label(frame_display, text="Vel. Objetivo: --", font=("Helvetica", 11))
        self.lbl_speed_obj.pack(anchor="w", padx=15, pady=2)
        self.lbl_speed_med = ttk.Label(frame_display, text="Vel. Medida: 0.0 RPM", font=("Helvetica", 12, "bold"), foreground="green")
        self.lbl_speed_med.pack(anchor="w", padx=15, pady=2)
        
        # Nuevas etiquetas para errores de Motor
        self.lbl_speed_err_abs = ttk.Label(frame_display, text="Error Absoluto: --", font=("Helvetica", 10))
        self.lbl_speed_err_abs.pack(anchor="w", padx=15, pady=1)
        self.lbl_speed_err_rel = ttk.Label(frame_display, text="Error Relativo: --", font=("Helvetica", 10))
        self.lbl_speed_err_rel.pack(anchor="w", padx=15, pady=1)

        self.frame_derecho = ttk.LabelFrame(self.root, text=" Gráficas Dinámicas del Sistema ")
        self.frame_derecho.pack(side="right", fill="both", expand=True, padx=15, pady=10)

    def inicializar_graficas(self):
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_derecho)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ax_principal = None
        self.ax_pwm = None
        self._configurar_graficas()

    def _configurar_graficas(self):
        self.fig.clear()
        self.ax_principal = self.fig.add_subplot(121)
        self.ax_pwm = self.fig.add_subplot(122)

        if self.sistema_activo.get() == "Temperatura":
            self.ax_principal.set_title("Temperatura (Datos Reales)")
            self.ax_principal.set_ylabel("°C")
            self.ax_principal.set_ylim(25, 40)
            self.ax_pwm.set_title("PWM Resistencia (%)")
            self.ax_pwm.set_ylim(-5, 105)
        else:
            self.ax_principal.set_title("Evolución de Velocidad")
            self.ax_principal.set_ylabel("RPM")
            self.ax_principal.set_ylim(-20, 800)
            self.ax_pwm.set_title("PWM Motor (%)")
            self.ax_pwm.set_ylim(-5, 105)

        self.ax_principal.grid(True)
        self.ax_pwm.grid(True)
        self.fig.tight_layout(pad=3.0)
        if hasattr(self, "canvas"):
            self.canvas.draw()

    def cambio_sistema(self, event=None):
        if self.sistema_activo.get() == "Temperatura":
            self.contenedor_motor.pack_forget()
            self.contenedor_temp.pack(fill="x", padx=5, pady=15)
            self.frame_pid_motor.pack_forget()
            self.frame_pid_temp.pack(fill="x", padx=5, pady=5)
        else:
            self.contenedor_temp.pack_forget()
            self.contenedor_motor.pack(fill="x", padx=5, pady=15)
            self.frame_pid_temp.pack_forget()
            self.frame_pid_motor.pack(fill="x", padx=5, pady=5)

        self._configurar_graficas()

    def iniciar(self):
        if self.emergencia:
            messagebox.showwarning("Alerta", "Desactive el estado de Emergencia.")
            return
        try:
            self.backend.conectar(self.puerto_com.get(), self.baudrate)
            self.backend.limpiar_datos()
            self.med_temp = None
            
            # Reiniciar memoria del PID
            self.integral_error_temp = 0.0
            self.error_previo_temp = 0.0
            self.tiempo_previo_temp = time.time()
            self.integral_error_motor = 0.0
            self.error_previo_motor = 0.0
            self.tiempo_previo_motor = time.time()
            
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
        # Apagamos la salida por seguridad enviando 0 con el prefijo correspondiente
        tipo = "t" if self.sistema_activo.get() == "Temperatura" else "v"
        self.backend.enviar_pwm(0, tipo=tipo)
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
    # Límites físicos de la salida (duty cycle 0-255, con piso de 20
    # para vencer la zona muerta de la resistencia/motor).
    SALIDA_PWM_MIN = 40
    SALIDA_PWM_MAX = 255

    def _pid_con_antiwindup(self, error, dt, kp, ki, kd, integral_previo, error_previo):
        """Calcula P, I y D con anti-windup por integración condicionada."""
        P = kp * error
        D = kd * ((error - error_previo) / dt)

        integral_tentativo = integral_previo + error * dt
        salida_tentativa = P + ki * integral_tentativo + D

        saturado_arriba = salida_tentativa > self.SALIDA_PWM_MAX
        saturado_abajo = salida_tentativa < self.SALIDA_PWM_MIN

        if (saturado_arriba and error > 0) or (saturado_abajo and error < 0):
            integral_nuevo = integral_previo
        else:
            integral_nuevo = integral_tentativo

        I = ki * integral_nuevo
        salida = P + I + D
        return salida, integral_nuevo, P, I, D

    def calcular_pid(self, setpoint, valor_medido, modo=None):
        """Aplica la matemática del PID (con anti-windup) y devuelve un PWM entre 0 y 255."""
        modo = modo or self.sistema_activo.get()
        tiempo_actual = time.time()

        if modo == "Temperatura":
            dt = tiempo_actual - self.tiempo_previo_temp
            if dt <= 0:
                dt = 0.01
            error = setpoint - valor_medido
            try:
                kp = float(self.kp_temp.get())
                ki = float(self.ki_temp.get())
                kd = float(self.kd_temp.get())
            except ValueError:
                kp, ki, kd = 0.0, 0.0, 0.0

            salida, self.integral_error_temp, P, I, D = self._pid_con_antiwindup(
                error, dt, kp, ki, kd, self.integral_error_temp, self.error_previo_temp
            )
            self.error_previo_temp = error
            self.tiempo_previo_temp = tiempo_actual
        else:
            dt = tiempo_actual - self.tiempo_previo_motor
            if dt <= 0:
                dt = 0.01
            error = setpoint - valor_medido
            try:
                kp = float(self.kp_motor.get())
                ki = float(self.ki_motor.get())
                kd = float(self.kd_motor.get())
            except ValueError:
                kp, ki, kd = 0.0, 0.0, 0.0

            salida, self.integral_error_motor, P, I, D = self._pid_con_antiwindup(
                error, dt, kp, ki, kd, self.integral_error_motor, self.error_previo_motor
            )
            self.error_previo_motor = error
            self.tiempo_previo_motor = tiempo_actual

        salida_pwm = max(self.SALIDA_PWM_MIN, min(self.SALIDA_PWM_MAX, int(salida)))
        return salida_pwm
    # ---------------------------------------------------------

    def bucle_control(self):
        """Lazo de control sincronizado a 30ms con el Arduino."""
        if self.ejecutando:
            self.contador_tiempo += 1
            temperatura_cruda = self.backend.obtener_temperatura_cruda()
            velocidad_cruda = self.backend.obtener_velocidad_cruda()

            if temperatura_cruda is not None:
                self.med_temp = temperatura_cruda
            if velocidad_cruda is not None:
                self.med_speed = velocidad_cruda

            try: target_t = max(30.0, min(35.0, self.ref_temp.get()))
            except tk.TclError: target_t = 32.5
            try: target_s = max(0.0, min(750.0, self.ref_speed.get()))
            except tk.TclError: target_s = 350.0

            self.target_t = target_t
            self.target_s = target_s

            if self.sistema_activo.get() == "Temperatura":
                self.pwm_motor = 0.0
                if self.med_temp is not None:
                    pwm_salida_cruda = self.calcular_pid(target_t, self.med_temp, modo="Temperatura")
                    self.backend.enviar_pwm(pwm_salida_cruda, tipo="t")
                    pwm_confirmado = self.backend.obtener_pwm_actual("t")
                    if pwm_confirmado is not None:
                        self.pwm_temp_grafica = (pwm_confirmado / 255.0) * 100.0
            else:
                if self.med_speed is not None:
                    pwm_salida_cruda = self.calcular_pid(target_s, self.med_speed, modo="Motor")
                    self.backend.enviar_pwm(pwm_salida_cruda, tipo="v")
                    pwm_confirmado = self.backend.obtener_pwm_actual("v")
                    if pwm_confirmado is not None:
                        self.pwm_motor = (pwm_confirmado / 255.0) * 100.0

            # Guardar historial
            valor_temp_grafica = self.med_temp if self.med_temp is not None else 0.0
            self.tiempo_x.append(self.contador_tiempo)
            self.historial_temp_ref.append(target_t)
            self.historial_temp_med.append(valor_temp_grafica)
            self.historial_pwm_temp.append(self.pwm_temp_grafica)
            self.historial_speed_ref.append(target_s)
            self.historial_speed_med.append(self.med_speed)
            self.historial_pwm_motor.append(self.pwm_motor)

        self.root.after(30, self.bucle_control)

    def _formatear_dos_cifras_sig(self, valor):
        """Devuelve una cadena con el valor formateado a exactamente 2 cifras significativas."""
        if valor == 0:
            return "0.0"
        from math import log10, floor
        # Determina la posición de la primera cifra significativa
        orden = floor(log10(abs(valor)))
        decimales = 1 - orden
        if decimales < 0:
            decimales = 0
        return f"{valor:.{decimales}f}"

    def bucle_grafica(self):
        """Lazo lento e independiente (cada ~250 ms) para renderizado de UI."""
        if self.ejecutando:
            # 1. Cálculos e informes de Temperatura
            if self.med_temp is not None:
                incertidumbre_t_str = self._formatear_dos_cifras_sig(0.5)
                self.lbl_temp_med.config(text=f"Temp. Medida: ({self.med_temp:.2f} ± {incertidumbre_t_str}) °C", foreground="blue")
                
                err_abs_t = abs(self.target_t - self.med_temp)
                err_rel_t = (err_abs_t * 100.0 / self.target_t) if self.target_t != 0 else 0.0
                self.lbl_temp_err_abs.config(text=f"Error Absoluto: {err_abs_t:.2f} °C")
                self.lbl_temp_err_rel.config(text=f"Error Relativo: {err_rel_t:.2f} %")
            
            # 2. Cálculos e informes del Motor (Velocidad)
            incert_v_cruda = abs(self.med_speed) * (6.25e-8) * 60.0*np.sqrt(2)
            incertidumbre_v_str = self._formatear_dos_cifras_sig(incert_v_cruda)
            self.lbl_speed_med.config(text=f"Vel. Medida: ({self.med_speed:.1f} ± {incertidumbre_v_str}) RPM", foreground="green")
            
            err_abs_v = abs(self.target_s - self.med_speed)
            err_rel_v = (err_abs_v * 100.0 / self.target_s) if self.target_s != 0 else 0.0
            self.lbl_speed_err_abs.config(text=f"Error Absoluto: {err_abs_v:.1f} RPM")
            self.lbl_speed_err_rel.config(text=f"Error Relativo: {err_rel_v:.2f} %")

            self.lbl_temp_obj.config(text=f"Temp. Objetivo: {self.target_t:.2f} °C")
            self.lbl_speed_obj.config(text=f"Vel. Objetivo: {self.target_s:.1f} RPM")

            t_list = list(self.tiempo_x)

            self.ax_principal.clear()
            self.ax_pwm.clear()

            if self.sistema_activo.get() == "Temperatura":
                self.ax_principal.set_title("Temperatura (Datos Reales)")
                self.ax_principal.set_ylabel("°C")
                self.ax_principal.set_ylim(25, 40)
                self.ax_principal.grid(True)
                self.ax_principal.plot(t_list, list(self.historial_temp_ref), 'k--', label="Setpoint")
                self.ax_principal.plot(t_list, list(self.historial_temp_med), 'b-', linewidth=2, label="Medida")
                self.ax_principal.legend(loc="upper left")

                self.ax_pwm.set_title("PWM Resistencia (%)")
                self.ax_pwm.set_ylim(-5, 105)
                self.ax_pwm.grid(True)
                self.ax_pwm.plot(t_list, list(self.historial_pwm_temp), 'r-', linewidth=2)
            else:
                self.ax_principal.set_title("Evolución de Velocidad")
                self.ax_principal.set_ylabel("RPM")
                self.ax_principal.set_ylim(-20, 800)
                self.ax_principal.grid(True)
                self.ax_principal.plot(t_list, list(self.historial_speed_ref), 'k--', label="Setpoint")
                self.ax_principal.plot(t_list, list(self.historial_speed_med), 'g-', linewidth=2, label="Medida")
                self.ax_principal.legend(loc="upper left")

                self.ax_pwm.set_title("PWM Motor (%)")
                self.ax_pwm.set_ylim(-5, 105)
                self.ax_pwm.grid(True)
                self.ax_pwm.plot(t_list, list(self.historial_pwm_motor), color="orange", linewidth=2)

            self.canvas.draw_idle()

        self.root.after(250, self.bucle_grafica)

    def on_closing(self):
        tipo = "t" if self.sistema_activo.get() == "Temperatura" else "v"
        self.backend.enviar_pwm(0, tipo=tipo)
        self.backend.desconectar()
        self.root.destroy()

if __name__ == "__main__":
    ventana = tk.Tk()
    app = InterfazControl(ventana)
    ventana.protocol("WM_DELETE_WINDOW", app.on_closing)
    ventana.mainloop()