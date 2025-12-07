from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# NOTA IMPORTANTE PARA VERCEL:
# En Vercel, las variables globales como esta lista SE BORRAN en cada petición.
# Para persistencia real necesitas una base de datos externa (Firebase, Supabase, MongoDB).
# Por ahora, esto solo funcionará mientras la instancia "caliente" siga viva, 
# pero perderás datos frecuentemente.
db_cortes = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Panel de Control - Monitor WiFi</title>
    <style>
        body { font-family: sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f4f4f9; }
        h1 { color: #333; }
        table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #007bff; color: white; }
        tr:hover { background-color: #f5f5f5; }
        .isp { color: #dc3545; font-weight: bold; }
        .local { color: #007bff; font-weight: bold; }
        .refresh { display: inline-block; margin-bottom: 20px; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; }
    </style>
    <meta http-equiv="refresh" content="10">
</head>
<body>
    <h1>📡 Reporte de Cortes (Vercel Edition)</h1>
    <a href="/" class="refresh">🔄 Actualizar Ahora</a>
    
    <table>
        <thead>
            <tr>
                <th>Usuario / PC</th>
                <th>Hora del Corte</th>
                <th>Duración</th>
                <th>Causa</th>
                <th>Velocidad</th>
            </tr>
        </thead>
        <tbody>
            {% for corte in cortes|reverse %}
            <tr>
                <td>{{ corte.user_id }}</td>
                <td>{{ corte.timestamp }}</td>
                <td>{{ corte.duration }}s</td>
                <td class="{{ 'isp' if 'ISP' in corte.cause else 'local' }}">{{ corte.cause }}</td>
                <td>{{ corte.speed }}</td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="text-align:center">Esperando reportes... (Nota: En Vercel los datos son volátiles)</td></tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

@app.route('/')
def admin_panel():
    return render_template_string(HTML_TEMPLATE, cortes=db_cortes)

@app.route('/report', methods=['POST'])
def receive_report():
    data = request.json
    registro = {
        'user_id': data.get('user_id', 'Anónimo'),
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'duration': data.get('duration'),
        'cause': data.get('cause'),
        'speed': f"⬇️ {data.get('download')} | ⬆️ {data.get('upload')}"
    }
    db_cortes.append(registro)
    return jsonify({"status": "success", "message": "Reporte guardado"}), 200

# Esta línea es crucial para Vercel
if __name__ == '__main__':
    app.run()

