from flask import Flask, render_template, request, redirect, jsonify
import pyodbc
from config import SQL_SERVER
import logging

app = Flask(__name__)

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

# Context manager para conexión a la base de datos
from contextlib import contextmanager

@contextmanager
def db_connection():
    conn_str = (
        f"DRIVER={{{SQL_SERVER['driver']}}};"
        f"SERVER={SQL_SERVER['server']};"
        f"DATABASE={SQL_SERVER['database']};"
        f"UID={SQL_SERVER['username']};"
        f"PWD={SQL_SERVER['password']}"
    )
    conn = pyodbc.connect(conn_str)
    try:
        yield conn
    finally:
        conn.close()

# Página principal
@app.route('/')
def index():
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            total_users = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM reportes")
            total_reports = cursor.fetchone()[0]
        return render_template('index.html', total_users=total_users, total_reports=total_reports)
    except Exception as e:
        logging.error(f"Error en index: {e}")
        return render_template('error.html', error="Ocurrió un error inesperado.")

# Crear usuario
@app.route('/usuarios/crear', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        if not nombre or not email:
            return render_template('crear_user.html', error="Nombre y correo son obligatorios.")
        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO usuarios (nombre, email) VALUES (?, ?)", (nombre, email))
                conn.commit()
            return redirect('/usuarios')
        except Exception as e:
            logging.error(f"Error al crear usuario: {e}")
            return render_template('error.html', error="No se pudo crear el usuario.")
    return render_template('crear_user.html')

# Ver usuarios
@app.route('/usuarios')
def ver_usuarios():
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios")
            usuarios = cursor.fetchall()
        return render_template('users.html', usuarios=usuarios)
    except Exception as e:
        logging.error(f"Error al obtener usuarios: {e}")
        return render_template('error.html', error="No se pudieron obtener los usuarios.")

# API REST - USUARIOS
@app.route('/api/usuarios', methods=['GET', 'POST'])
def api_usuarios():
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            if request.method == 'POST':
                data = request.get_json()
                nombre = data.get('nombre', '').strip()
                email = data.get('email', '').strip()
                if not nombre or not email:
                    return jsonify({'error': 'Nombre y correo son obligatorios.'}), 400
                cursor.execute("INSERT INTO usuarios (nombre, email) VALUES (?, ?)", (nombre, email))
                conn.commit()
                return jsonify({'message': 'Usuario creado'}), 201
            else:
                cursor.execute("SELECT * FROM usuarios")
                rows = cursor.fetchall()
                usuarios = [{'id': r[0], 'nombre': r[1], 'email': r[2]} for r in rows]
                return jsonify(usuarios)
    except Exception as e:
        logging.error(f"Error en API usuarios: {e}")
        return jsonify({'error': 'Ocurrió un error inesperado.'}), 500

# API REST - REPORTES
@app.route('/api/reportes', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_reportes():
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            if request.method == 'POST':
                data = request.get_json()
                empresa = data.get('empresa', '').strip()
                descripcion = data.get('descripcion', '').strip()
                estado = data.get('estado', '').strip()
                if not empresa or not descripcion or not estado:
                    return jsonify({'error': 'Todos los campos son obligatorios.'}), 400
                cursor.execute("INSERT INTO reportes (empresa, descripcion, estado) VALUES (?, ?, ?)",
                               (empresa, descripcion, estado))
                conn.commit()
                return jsonify({'message': 'Reporte creado'}), 201
            elif request.method == 'PUT':
                data = request.get_json()
                if not data.get('id'):
                    return jsonify({'error': 'ID es obligatorio.'}), 400
                cursor.execute("UPDATE reportes SET empresa=?, descripcion=?, estado=? WHERE id=?",
                               (data.get('empresa', '').strip(),
                                data.get('descripcion', '').strip(),
                                data.get('estado', '').strip(),
                                data['id']))
                conn.commit()
                return jsonify({'message': 'Reporte actualizado'})
            elif request.method == 'DELETE':
                data = request.get_json()
                if not data.get('id'):
                    return jsonify({'error': 'ID es obligatorio.'}), 400
                cursor.execute("DELETE FROM reportes WHERE id=?", (data['id'],))
                conn.commit()
                return jsonify({'message': 'Reporte eliminado'})
            else:
                cursor.execute("SELECT * FROM reportes")
                rows = cursor.fetchall()
                reportes = [{'id': r[0], 'empresa': r[1], 'descripcion': r[2], 'estado': r[3]} for r in rows]
                return jsonify(reportes)
    except Exception as e:
        logging.error(f"Error en API reportes: {e}")
        return jsonify({'error': 'Ocurrió un error inesperado.'}), 500

# Ver reportes
@app.route('/reportes')
def ver_reportes():
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reportes")
            reportes = cursor.fetchall()
        return render_template('reports.html', reportes=reportes)
    except Exception as e:
        logging.error(f"Error al obtener reportes: {e}")
        return render_template('error.html', error="No se pudieron obtener los reportes.")

# Manejo de errores
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('error.html', error="Página no encontrada"), 404

if __name__ == '__main__':
    app.run(debug=True)
