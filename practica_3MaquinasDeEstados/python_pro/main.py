import tkinter as tk
from backend import ArduinoBackend
from frontend import ArduinoApp

def main():
    # 1. Crear la ventana principal de Tkinter
    root = tk.Tk()
    
    # 2. Instanciar el backend con el puerto correspondiente
    mi_backend = ArduinoBackend(puerto='/dev/ttyACM0', baud_rate=115200)
    
    # 3. Instanciar el frontend y pasarle el backend (Inyección de dependencias)
    app = ArduinoApp(root, mi_backend)
    
    # 4. Interceptar el cierre de la ventana para apagar el hilo serial de forma segura
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 5. Arrancar el bucle principal de la interfaz gráfica
    root.mainloop()

if __name__ == "__main__":
    main()

    