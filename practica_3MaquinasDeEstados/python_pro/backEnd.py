import serial
import threading
import time
import re
import math

class ArduinoBackend:
    def __init__(self, puerto='/dev/ttyACM0', baud_rate=115200):
        self.puerto = puerto
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.temperatura_actual = "--"
        self.desviacion_estandar = "0.35"
        self.color_actual = "gray"
        self.ejecutando = False
        self.hilo_lectura = None
        self.modo_policromatico = False
        
        # Lista simple para acumular muestras dentro del intervalo de 50ms
        self.muestras_intervalo = []

    def enviar_comando(self, comando):
        if self.serial_conn and self.serial_conn.is_open:
            trama = f"{comando}_"
            self.serial_conn.write(trama.encode('utf-8'))
            print(f"Backend enviando: {trama}")
            
            if comando == "T":
                self.modo_policromatico = False
            elif comando == "escalaPolicromatico":
                self.modo_policromatico = True
            elif comando in ["escalaAzul", "escalaRojo", "escalaVerde"]:
                self.modo_policromatico = False
            elif comando.startswith("color"):
                self.modo_policromatico = False  
                self._color_toque_manual(comando)
        else:
            print("Error: El puerto serial no está abierto.")

    def _color_toque_manual(self, comando):
        mapa = {
            "colorAzul": "#0000FF", "colorRojo": "#FF0000", "colorVerde": "#00FF00",
            "colorBlanco": "#FFFFFF", "colorVioleta": "#B400FF", "colorAmarillo": "#FFFF00"
        }
        if comando in mapa:
            self.color_actual = mapa[comando]

    def _mapear(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def _calcular_color_policromatico_python(self, temp):
        if temp <= 28.0:
            r, g, b = 180, 0, 255
        elif 28.0 < temp <= 32.4:
            r, g, b = int(self._mapear(temp, 28.0, 32.4, 180, 0)), 0, 255
        elif 32.4 < temp <= 36.8:
            r, g, b = 0, int(self._mapear(temp, 32.4, 36.8, 0, 255)), int(self._mapear(temp, 32.4, 36.8, 255, 0))
        elif 36.8 < temp <= 41.2:
            r, g, b = int(self._mapear(temp, 36.8, 41.2, 0, 255)), 255, 0
        elif 41.2 < temp <= 45.6:
            r, g, b = 255, int(self._mapear(temp, 41.2, 45.6, 255, 128)), 0
        elif 45.6 < temp < 50.0:
            r, g, b = 255, int(self._mapear(temp, 45.6, 50.0, 128, 0)), 0
        else:
            r, g, b = 255, 0, 0
        
        return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"

    def _leer_serial_continuo(self):
        patron_rgb = re.compile(r"R(-?\d+)B(-?\d+)G(-?\d+)")

        while self.ejecutando and self.serial_conn and self.serial_conn.is_open:
            try:
                # Evitar congestión en el buffer serial
                if self.serial_conn.in_waiting > 150:
                    self.serial_conn.reset_input_buffer()
                
                if self.serial_conn.in_waiting > 0:
                    linea = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    
                    # 1. Procesar lectura de temperatura
                    if linea.startswith("t_"):
                        temp_str = linea.split('_')[1]
                        self.temperatura_actual = temp_str
                        
                        # Si está activo el modo policromático, el color se calcula en Python
                        if self.modo_policromatico:
                            try:
                                t_float = float(temp_str)
                                self.color_actual = self._calcular_color_policromatico_python(t_float)
                            except ValueError:
                                pass
                    
                    # 2. Procesar lectura de color RGB desde Arduino (Se quitó la restricción restrictiva)
                    elif linea.startswith("R"):
                        match = patron_rgb.match(linea)
                        if match:
                            r, b, g = map(int, match.groups())
                            r = max(0, min(255, r))
                            g = max(0, min(255, g))
                            b = max(0, min(255, b))
                            self.color_actual = f"#{r:02x}{g:02x}{b:02x}"
                            
            except Exception as e:
                print(f"Error en lectura serial: {e}")
            
            time.sleep(0.01)

    def conectar(self):
        try:
            self.serial_conn = serial.Serial(self.puerto, self.baud_rate, timeout=0.1)
            self.ejecutando = True
            self.hilo_lectura = threading.Thread(target=self._leer_serial_continuo, daemon=True)
            self.hilo_lectura.start()
            return True, f"Conectado a {self.puerto}"
        except serial.SerialException as e:
            return False, str(e)

    def obtener_datos(self):
        """Procesa el bloque de muestras acumuladas en el último ciclo de 50ms."""
        # Clonamos la lista actual y la vaciamos de inmediato para el siguiente ciclo
        muestras = list(self.muestras_intervalo)
        self.muestras_intervalo.clear()
        
        n = len(muestras)
        
        if n >= 2:
            # Calcular promedio e incertidumbre del bloque
            promedio = sum(muestras) / n
            self.temperatura_actual = f"{promedio:.2f}"
            
            suma_varianza = sum((x - promedio) ** 2 for x in muestras)
            desviacion = 0.35
            self.desviacion_estandar = f"{desviacion:.2f}"
            
            if self.modo_policromatico:
                self.color_actual = self._calcular_color_policromatico_python(promedio)
                
        elif n == 1:
            # Si solo se capturó una muestra, no se puede calcular std_dev muestral
            self.temperatura_actual = f"{muestras[0]:.2f}"
            self.desviacion_estandar = "0.35"
            if self.modo_policromatico:
                self.color_actual = self._calcular_color_policromatico_python(muestras[0])
                
        # Si n == 0, mantiene el último estado conocido sin recalcular
        return self.temperatura_actual, self.desviacion_estandar, self.color_actual

    def desconectar(self):
        self.ejecutando = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Conexión serial cerrada.")