import matplotlib.pyplot as plt
import csv
from datetime import datetime
import os

LOG_FILE = "wifi_log_full.csv"

def plot_data():
    if not os.path.exists(LOG_FILE):
        print(f"El archivo {LOG_FILE} no existe aún. Ejecuta primero el monitor.")
        return

    times = []
    durations = []
    colors = []

    print(f"Leyendo {LOG_FILE}...")
    
    with open(LOG_FILE, 'r') as f:
        reader = csv.reader(f)
        header = next(reader, None) # Saltar cabecera
        
        for row in reader:
            try:
                # row[0] es "Inicio Corte" (YYYY-MM-DD HH:MM:SS)
                start_time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                duration = float(row[2])
                cause = row[3]

                times.append(start_time)
                durations.append(duration)
                
                # Color según causa
                if "ISP" in cause:
                    colors.append('red')   # Rojo para ISP
                else:
                    colors.append('blue')  # Azul para Router Local
            except ValueError:
                continue

    if not times:
        print("No hay datos suficientes para graficar.")
        return

    # Crear gráfica
    plt.figure(figsize=(12, 6))
    
    # Scatter plot
    plt.scatter(times, durations, c=colors, alpha=0.7, s=100)
    
    # Líneas verticales desde 0 hasta el punto (efecto 'lollipop')
    for i in range(len(times)):
        plt.plot([times[i], times[i]], [0, durations[i]], color=colors[i], alpha=0.3)

    plt.title("Registro de Cortes de WiFi")
    plt.xlabel("Hora del Corte")
    plt.ylabel("Duración (segundos)")
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    
    # Leyenda manual
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', label='Falla ISP (Internet)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', label='Falla Local (Router)')
    ]
    plt.legend(handles=legend_elements)

    plt.tight_layout()
    
    output_img = "reporte_cortes.png"
    plt.savefig(output_img)
    print(f"✅ Gráfico guardado como: {output_img}")
    plt.show()

if __name__ == "__main__":
    plot_data()

