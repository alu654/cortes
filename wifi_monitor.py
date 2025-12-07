import subprocess
import time
import csv
import os
from datetime import datetime
import sys
import requests
import socket

# Intentar importar speedtest, si no está, desactivar la función
try:
    import speedtest
    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False
    print("⚠️  Librería 'speedtest-cli' no encontrada. La prueba de velocidad estará desactivada.")

# --- Configuración ---
TARGET_HOST = "8.8.8.8"      # Google DNS
GATEWAY_IP = "192.168.0.1"   # IP de tu Router (Detectada automáticamente en el código si es posible)
PING_INTERVAL = 1            # Segundos entre pings
TIMEOUT = "1000"             # Milisegundos (1s)
SERVER_URL = "https://cortes-alxx.onrender.com/report" # URL de tu servidor en Render

# Identificar al usuario (Nombre del equipo)
USER_ID = socket.gethostname()

# Guardar log en el Escritorio del usuario para fácil acceso
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
LOG_FILE = os.path.join(desktop_path, "wifi_log_full.csv")

def get_gateway_ip():
    """Intenta obtener la IP del router automáticamente en macOS."""
    try:
        # Ejecutar netstat para buscar la ruta por defecto
        output = subprocess.check_output("netstat -nr | grep default", shell=True, text=True)
        for line in output.splitlines():
            parts = line.split()
            if "default" in parts[0] and "." in parts[1]: # Busca IPv4
                return parts[1]
    except:
        pass
    return "192.168.0.1" # Valor por defecto si falla

def notify(title, text):
    """Envía una notificación nativa de macOS."""
    try:
        cmd = f'display notification "{text}" with title "{title}" sound name "Frog"'
        subprocess.run(["osascript", "-e", cmd])
    except:
        pass

def run_speedtest():
    """Ejecuta un test de velocidad y retorna (bajada, subida) en Mbps."""
    if not SPEEDTEST_AVAILABLE:
        return 0, 0
    
    print("🚀 Ejecutando test de velocidad (esto puede tardar unos segundos)...")
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download() / 1_000_000 # Convertir a Mbps
        upload = st.upload() / 1_000_000
        return round(download, 2), round(upload, 2)
    except Exception as e:
        print(f"Error en speedtest: {e}")
        return 0, 0

def ping(host):
    """True si responde, False si no."""
    try:
        subprocess.check_output(
            ["ping", "-c", "1", "-W", TIMEOUT, host],
            stderr=subprocess.STDOUT
        )
        return True
    except subprocess.CalledProcessError:
        return False

def send_report_to_cloud(duration, cause, dl_speed, ul_speed):
    """Envía los datos al servidor administrador."""
    payload = {
        "user_id": USER_ID,
        "duration": round(duration, 2),
        "cause": cause,
        "download": dl_speed,
        "upload": ul_speed
    }
    try:
        # Timeout de 5 segundos para no bloquear el script si el servidor no responde
        requests.post(SERVER_URL, json=payload, timeout=5)
        print("☁️  Reporte enviado al servidor exitosamente.")
    except Exception as e:
        print(f"⚠️  No se pudo enviar reporte al servidor: {e}")

def log_event(start, end, duration, cause, dl_speed, ul_speed):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                "Inicio Corte", "Fin Corte", "Duración (s)", 
                "Causa Probable", "Bajada (Mbps)", "Subida (Mbps)"
            ])
            
        writer.writerow([
            start.strftime("%Y-%m-%d %H:%M:%S"),
            end.strftime("%Y-%m-%d %H:%M:%S"),
            round(duration, 2),
            cause,
            dl_speed if dl_speed else "N/A",
            ul_speed if ul_speed else "N/A"
        ])
    print(f"📝 Registro guardado localmente en {LOG_FILE}")

def main():
    global GATEWAY_IP
    detected_gateway = get_gateway_ip()
    if detected_gateway:
        GATEWAY_IP = detected_gateway
    
    print(f"--- 📡 MONITOR WIFI (Modo Cliente Cloud) ---")
    print(f"• Usuario:          {USER_ID}")
    print(f"• Servidor:         {SERVER_URL}")
    print(f"• Router (Gateway): {GATEWAY_IP}")
    print(f"• Internet (DNS):   {TARGET_HOST}")
    print("--------------------------------------------")

    is_connected = True
    disconnect_start = None
    
    # Estado inicial
    if not ping(TARGET_HOST):
        is_connected = False
        disconnect_start = datetime.now()
        print("⚠️  Arrancamos SIN internet.")

    while True:
        try:
            # 1. Verificar conexión a Internet
            internet_ok = ping(TARGET_HOST)
            
            if is_connected and not internet_ok:
                # SE CORTÓ
                is_connected = False
                disconnect_start = datetime.now()
                
                # Diagnóstico inmediato: ¿Es el router?
                router_ok = ping(GATEWAY_IP)
                cause = "ISP (Internet caído)" if router_ok else "Local (Router/WiFi caído)"
                
                msg = f"Caída detectada. Causa probable: {cause}"
                print(f"\n🔻 {datetime.now().strftime('%H:%M:%S')} - {msg}")
                notify("Alerta WiFi", msg)
                
            elif not is_connected and internet_ok:
                # VOLVIÓ
                is_connected = True
                disconnect_end = datetime.now()
                duration = (disconnect_end - disconnect_start).total_seconds()
                
                print(f"✅ {disconnect_end.strftime('%H:%M:%S')} - Conexión restaurada tras {round(duration, 2)}s")
                notify("WiFi Restaurado", f"Duró {round(duration, 1)}s")

                # Diagnóstico post-corte (re-verificar causa teórica basada en gateway actual)
                router_ok = ping(GATEWAY_IP)
                cause = "ISP (Internet)" if router_ok else "Local (Router/WiFi)"

                # Test de velocidad (opcional, solo si el corte fue > 5 seg para no spamear)
                dl, ul = 0, 0
                if duration > 5 and SPEEDTEST_AVAILABLE:
                    dl, ul = run_speedtest()
                    print(f"   📊 Velocidad actual: ⬇️ {dl} Mbps | ⬆️ {ul} Mbps")

                # Guardar local y enviar a la nube
                log_event(disconnect_start, disconnect_end, duration, cause, dl, ul)
                send_report_to_cloud(duration, cause, dl, ul)

            time.sleep(PING_INTERVAL)

        except KeyboardInterrupt:
            print("\n🛑 Monitor detenido.")
            break
        except Exception as e:
            print(f"Error en loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
