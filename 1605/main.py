from flask import Flask, render_template, request, redirect, jsonify
import pyodbc
from config import SQL_SERVER

app = Flask(__name__)

# Conexión SQL Server
def get_db_connection():
    conn_str = (
        f"DRIVER={{{SQL_SERVER['driver']}}};"
        f"SERVER={SQL_SERVER['server']};"
        f"DATABASE={SQL_SERVER['database']};"
        f"UID={SQL_SERVER['username']};"
        f"PWD={SQL_SERVER['password']}"
    )
    return pyodbc.connect(conn_str)

# Página principal
@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM reportes")
        total_reports = cursor.fetchone()[0]
        conn.close()
        return render_template('index.html', total_users=total_users, total_reports=total_reports)
    except Exception as e:
        return render_template('error.html', error=str(e))

# Crear usuario
@app.route('/usuarios/crear', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (nombre, email) VALUES (?, ?)", (nombre, email))
            conn.commit()
            conn.close()
            return redirect('/usuarios')
        except Exception as e:
            return render_template('error.html', error=str(e))
    return render_template('crear_user.html')

# Ver usuarios
@app.route('/usuarios')
def ver_usuarios():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
        conn.close()
        return render_template('users.html', usuarios=usuarios)
    except Exception as e:
        return render_template('error.html', error=str(e))

# API REST - USUARIOS
@app.route('/api/usuarios', methods=['GET', 'POST'])
def api_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.get_json()
        cursor.execute("INSERT INTO usuarios (nombre, email) VALUES (?, ?)", (data['nombre'], data['email']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Usuario creado'}), 201
    else:
        cursor.execute("SELECT * FROM usuarios")
        rows = cursor.fetchall()
        conn.close()
        usuarios = [{'id': r[0], 'nombre': r[1], 'email': r[2]} for r in rows]
        return jsonify(usuarios)

# API REST - REPORTES
@app.route('/api/reportes', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_reportes():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.get_json()
        cursor.execute("INSERT INTO reportes (empresa, descripcion, estado) VALUES (?, ?, ?)",
                       (data['empresa'], data['descripcion'], data['estado']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Reporte creado'}), 201
    elif request.method == 'PUT':
        data = request.get_json()
        cursor.execute("UPDATE reportes SET empresa=?, descripcion=?, estado=? WHERE id=?",
                       (data['empresa'], data['descripcion'], data['estado'], data['id']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Reporte actualizado'})
    elif request.method == 'DELETE':
        data = request.get_json()
        cursor.execute("DELETE FROM reportes WHERE id=?", (data['id'],))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Reporte eliminado'})
    else:
        cursor.execute("SELECT * FROM reportes")
        rows = cursor.fetchall()
        conn.close()
        reportes = [{'id': r[0], 'empresa': r[1], 'descripcion': r[2], 'estado': r[3]} for r in rows]
        return jsonify(reportes)

# Manejo de errores
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('error.html', error="Página no encontrada"), 404

@app.route('/reportes')
def ver_reportes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reportes")
        reportes = cursor.fetchall()
        conn.close()
        return render_template('reports.html', reportes=reportes)
    except Exception as e:
        return render_template('error.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True)
