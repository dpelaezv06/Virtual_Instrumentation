import serial
import threading
import time

class ArduinoBackend:
    def __init__(self, puerto='/dev/ttyACM0', baud_rate=115200):
        self.puerto = puerto
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.temperatura_actual = "--"
        self.color_actual = "gray"  # Color inicial para el cuadrado virtual
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
            
            # Mapeamos el comando enviado con el color que debe mostrar el cuadrado
            self._actualizar_color_virtual(comando)
        else:
            print("Error: El puerto serial no está abierto.")

    def _actualizar_color_virtual(self, comando):
        """Traduce el comando del Arduino a un color comprensible por Tkinter."""
        mapa_colores = {
            "escalaAzul": "blue", "colorAzul": "blue",
            "escalaRojo": "red", "colorRojo": "red",
            "escalaVerde": "green", "colorVerde": "green",
            "colorBlanco": "white",
            "colorVioleta": "purple",
            "colorAmarillo": "yellow",
            "escalaPolicromatico": "cyan",  # Usamos cyan para representar el policromático en pantalla
            "OFF": "gray"
        }
        if comando in mapa_colores:
            self.color_actual = mapa_colores[comando]

    def _leer_serial_continuo(self):
        while self.ejecutando and self.serial_conn and self.serial_conn.is_open:
            try:
                if self.serial_conn.in_waiting > 0:
                    linea = self.serial_conn.readline().decode('utf-8').strip()
                    if linea.startswith("t_"):
                        self.temperatura_actual = linea.split('_')[1]
            except Exception as e:
                print(f"Error de lectura en backend: {e}")
            time.sleep(0.05)

    def obtener_datos(self):
        """Devuelve la temperatura y el color actual para el frontend."""
        return self.temperatura_actual, self.color_actual

    def desconectar(self):
        self.ejecutando = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Conexión serial cerrada.")