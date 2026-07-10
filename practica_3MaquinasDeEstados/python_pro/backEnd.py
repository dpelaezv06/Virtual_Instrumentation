import serial
import threading
import time
import re

class ArduinoBackend:
    def __init__(self, puerto='/dev/ttyACM0', baud_rate=115200):
        self.puerto = puerto
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.temperatura_actual = "--"
        self.color_actual = "gray"
        self.ejecutando = False
        self.hilo_lectura = None

    def conectar(self):
        try:
            self.serial_conn = serial.Serial(self.puerto, self.baud_rate, timeout=0.1)
            self.ejecutando = True
            self.hilo_lectura = threading.Thread(target=self._leer_serial_continuo, daemon=True)
            self.hilo_lectura.start()
            return True, f"Conectado a {self.puerto}"
        except serial.SerialException as e:
            return False, str(e)

    def enviar_comando(self, comando):
        if self.serial_conn and self.serial_conn.is_open:
            trama = f"{comando}_"
            self.serial_conn.write(trama.encode('utf-8'))
            print(f"Backend enviando: {trama}")
        else:
            print("Error: El puerto serial no está abierto.")

    def _leer_serial_continuo(self):
        # Expresión regular para extraer los valores R, B y G permitiendo números negativos
        # (El Arduino los envía en el orden R, B, G según el firmware)
        patron_rgb = re.compile(r"R(-?\d+)B(-?\d+)G(-?\d+)")

        while self.ejecutando and self.serial_conn and self.serial_conn.is_open:
            try:
                if self.serial_conn.in_waiting > 0:
                    linea = self.serial_conn.readline().decode('utf-8').strip()
                    
                    if linea.startswith("t_"):
                        # Extraemos la temperatura
                        self.temperatura_actual = linea.split('_')[1]
                    
                    elif linea.startswith("R"):
                        # Extraemos el color calculado por el Arduino
                        match = patron_rgb.match(linea)
                        if match:
                            r, b, g = map(int, match.groups())
                            
                            # Limitamos los valores entre 0 y 255 (Tkinter no soporta colores fuera de este rango)
                            r = max(0, min(255, r))
                            g = max(0, min(255, g))
                            b = max(0, min(255, b))
                            
                            # Formateamos a Hexadecimal (ej: #FF00AA)
                            self.color_actual = f"#{r:02x}{g:02x}{b:02x}"
                            
            except Exception as e:
                # Ignoramos pequeños errores de lectura inicial por sincronización
                pass
            
            # Pausa muy pequeña (10ms) porque ahora recibimos datos a 20Hz
            time.sleep(0.01)

    def obtener_datos(self):
        return self.temperatura_actual, self.color_actual

    def desconectar(self):
        self.ejecutando = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Conexión serial cerrada.")