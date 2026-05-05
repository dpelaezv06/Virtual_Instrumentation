import serial
import time

# Se define el puerto al que esta conectado el microcontrolador
PUERTO = 'COM3'  # en linux es /dev/tty...

# Se define la velocidad, la cual debe coincidir con el microcontrolador.
Baudrate = 115200

try:
    # Se inicializa la conexion serial. 
    # Se establece un timeout de 1 segundo para evitar bloqueos en la lectura.
    conexion_serial = serial.Serial(PUERTO, Baudrate, timeout=1)
  
    # Se incluye una pausa 
    time.sleep(2)
    
    
    # --- PROCEDIMIENTO DE ENVIO ---
    
    # Se define el mensaje a enviar, agregando un salto de linea al final.
    comando = "ENCENDER_LED\n"
    
    # Se convierte el texto a formato de bytes (UTF-8) y se envia por el puerto.
    conexion_serial.write(comando.encode('utf-8'))
    print("Comando enviado al microcontrolador.")
    
    
    
    # --- PROCEDIMIENTO DE RECEPCION ---
    
    time.sleep(0.1)
    
    # Se verifica si hay bytes esperando en el bufer de entrada de la computadora.
    if conexion_serial.in_waiting > 0:
        
        # Se lee la linea de respuesta proveniente del microcontrolador.
        respuesta_bytes = conexion_serial.readline()
        
        # Se convierte la respuesta de bytes a texto
        respuesta_texto = respuesta_bytes.decode('utf-8').strip()


except serial.SerialException as error:
    # Se captura y muestra cualquier error relacionado con la apertura del puerto.
    print(f"Error al abrir el puerto serial: {error}")

finally:
    # Se asegura que el puerto se cierre correctamente al finalizar o si ocurre un error.
    if 'conexion_serial' in locals() and conexion_serial.is_open:
        conexion_serial.close()
        print("Puerto serial cerrado.")