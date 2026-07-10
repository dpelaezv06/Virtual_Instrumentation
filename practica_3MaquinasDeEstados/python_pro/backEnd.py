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
        self.modo_policromatico = False

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
            
            # Detectamos si activaron el modo policromático o un color fijo de toque
            if comando == "escalaPolicromatico":
                self.modo_policromatico = True
            elif comando in ["escalaAzul", "escalaRojo", "escalaVerde"]:
                self.modo_policromatico = False
            elif comando.startswith("color"):
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
        """Réplica del algoritmo de tu compañera para que la interfaz se pinte perfecta."""
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
        # El Arduino imprime: R -> B -> G. Ajustamos la expresión regular a ese orden exacto.
        patron_rgb = re.compile(r"R(-?\d+)B(-?\d+)G(-?\d+)")

        while self.ejecutando and self.serial_conn and self.serial_conn.is_open:
            try:
                if self.serial_conn.in_waiting > 0:
                    linea = self.serial_conn.readline().decode('utf-8').strip()
                    
                    if linea.startswith("t_"):
                        temp_str = linea.split('_')[1]
                        self.temperatura_actual = temp_str
                        
                        # Si estamos en modo policromático, calculamos el color en Python visualmente
                        if self.modo_policromatico:
                            try:
                                t_float = float(temp_str)
                                self.color_actual = self._calcular_color_policromatico_python(t_float)
                            except ValueError:
                                pass
                    
                    elif linea.startswith("R") and not self.modo_policromatico:
                        match = patron_rgb.match(linea)
                        if match:
                            # Extraemos en el orden en que el Arduino los envía: R, B, G
                            r, b, g = map(int, match.groups())
                            r = max(0, min(255, r))
                            g = max(0, min(255, g))
                            b = max(0, min(255, b))
                            self.color_actual = f"#{r:02x}{g:02x}{b:02x}"
                            
            except Exception as e:
                pass
            
            time.sleep(0.01)

    def obtener_datos(self):
        return self.temperatura_actual, self.color_actual

    def desconectar(self):
        self.ejecutando = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Conexión serial cerrada.")