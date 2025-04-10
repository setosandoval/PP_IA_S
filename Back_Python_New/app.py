import os
import io
import json
import random
import subprocess
import tempfile
import re

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from Prompt_Completion_V00 import Preguntas  # Debe tener 'week' en cada pregunta

##### PRUEBA
import pypandoc

try:
    pandoc_path = pypandoc.get_pandoc_path()
except OSError:
    print("Pandoc no encontrado, descargando...")
    pypandoc.download_pandoc()
    pandoc_path = pypandoc.get_pandoc_path()
##### 

app = Flask(__name__, static_folder='react_build')
CORS(app)

# ---------------------------------------------------------------------------------
# Ruta opcional para convertir un archivo .tex completo a HTML (vía Pandoc)
# ---------------------------------------------------------------------------------
##### PRUEBA
@app.route('/api/convert_latex', methods=['GET'])
def convert_latex_to_html():
    try:
        import pypandoc
        pandoc_path = pypandoc.get_pandoc_path()

        tex_path = os.path.join(os.getcwd(), "Preguntas.tex")
        html_path = os.path.join(os.getcwd(), "Preguntas.html")

        subprocess.run([pandoc_path, tex_path, "-o", html_path], check=True)

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return jsonify({"html": html_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

'''
@app.route('/api/convert_latex', methods=['GET'])
def convert_latex_to_html():
    try:
        tex_path = os.path.join(os.getcwd(), "Preguntas.tex")
        html_path = os.path.join(os.getcwd(), "Preguntas.html")
        subprocess.run(["pandoc", tex_path, "-o", html_path], check=True)

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return jsonify({"html": html_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

'''

# ---------------------------------------------------------------------------------
# Variables globales
# ---------------------------------------------------------------------------------
WELCOME_MESSAGE = (
    "¡Bienvenido/a a PP-BOT!\n\n"
    "Estás a punto de comenzar la práctica libre de ejercicios.\n\n"
    "De momento, únicamente hay ejercicios de traducción disponibles.\n\n"
    "Las preguntas son de opción múltiple: responde con a, b, c, o d en el chat.\n\n"
    "Esta es una versión de prueba, así que te agradeceríamos mucho que nos compartas cualquier error, detalle, typo o problema que encuentres; ya sea en la interfaz, las preguntas o cualquier otro aspecto.\n\n"
    "Todo comentario nos ayuda a mejorar.\n\n"
    "Atentamente,\n"
    "El equipo de Pensando Problemas.\n\n"
)

History = [[
    {"id": 0, "responseChatbot": WELCOME_MESSAGE},
    {"id": 1, "responseChatbot": "¿En qué semana de universidad estás?"}
]]
history_path = "Back_Python_New/react_build/"
record = []            # Registro de (id_pregunta, acierto?)
inicializador_id = 1   # ID de la pregunta actual
info = {}              # Info de la pregunta actual
success_fail = True
selected_theme = None
user_week = None
current_question_responded = False  # Nuevo: para controlar si una pregunta ya ha sido respondida

def reset_global_state():
    """Reinicia todas las variables globales al estado inicial"""
    global record, inicializador_id, info, success_fail, selected_theme, user_week, current_question_responded
    record = []
    inicializador_id = 1
    info = {}
    success_fail = True
    selected_theme = None
    user_week = None
    current_question_responded = False

def load_history():
    """Inicializa el historial y lo guarda en un archivo JSON"""
    global History, inicializador_id
    file_path = os.path.join(history_path, "History.json")
    inicializador_id = 1
    History = [[
        {"id": 0, "responseChatbot": WELCOME_MESSAGE},
        {"id": 1, "responseChatbot": "¿En qué semana de universidad estás?"}
    ]]
    # Asegurarse de que el directorio existe
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with io.open(file_path, 'w', encoding='utf-8') as history_file:
        history_file.write(json.dumps(History))

def fail_message():
    return (
        "Se ha equivocado en la elección de la respuesta correcta.\n\n"
        "¿Desea continuar con el mismo tema, elegir otro tema, o finalizar?\n\n"
        "Escriba 'si' para continuar con el mismo tema, 'no' para elegir otro tema, o 'finalizar' para terminar."
    )

def success_message():
    return (
        "Ha acertado en la elección de la respuesta correcta. \n\n"
        "¿Desea continuar con el mismo tema?\n\n"
        "Escriba 'si' para continuar con el mismo tema, 'no' para elegir otro tema, o 'finalizar' para terminar."
    )

def tail_message():
    """Genera un mensaje de resumen al finalizar el quiz"""
    global record
    num_exercises = len(record)
    ejercicio_text = "ejercicio" if num_exercises == 1 else "ejercicios"
    if num_exercises == 0:
        return "Ha finalizado la práctica.\n\nUsted realizó 0 ejercicios.\n\n¿Desea reiniciar un quiz?"

    themes = []
    difs_succeed = {}
    difs_failed = {}

    for (pid, was_correct) in record:
        tema = Preguntas[pid]['tema']
        dif = Preguntas[pid]['dif']
        if tema not in themes:
            themes.append(tema)
        if was_correct:
            difs_succeed[dif] = difs_succeed.get(dif, 0) + 1
        else:
            difs_failed[dif] = difs_failed.get(dif, 0) + 1

    temas_str = ", ".join(str(t) for t in themes)
    total_acertadas = sum(difs_succeed.values())
    total_falladas = sum(difs_failed.values())
    acertadas_text = "acertada" if total_acertadas == 1 else "acertadas"
    falladas_text = "fallada" if total_falladas == 1 else "falladas"

    def format_difs(difs_dict):
        lines = []
        for level, count in sorted(difs_dict.items()):
            pregunta_text = "pregunta" if count == 1 else "preguntas"
            lines.append(f"\t- {count} {pregunta_text} del nivel {level}")
        return "\n".join(lines)

    summary_succeed = format_difs(difs_succeed) if difs_succeed else "\t- Ninguna"
    summary_failed = format_difs(difs_failed) if difs_failed else "\t- Ninguna"
    
    rec_str = (
        f"Aquí se encuentra el resumen de la práctica:\n\n"
        f"Usted ha acertado ({total_acertadas} {acertadas_text}):\n{summary_succeed}\n\n"
        f"Usted ha fallado ({total_falladas} {falladas_text}):\n{summary_failed}"
    )

    return (
        f"Ha finalizado la práctica.\n"
        f"Ha completado todos los ejercicios disponibles con los parámetros ingresados.\n\n"
        f"Usted realizó {num_exercises} {ejercicio_text} y el tema elegido fue {temas_str}.\n\n"
        f"{rec_str}"
        f"\n\n Espero haber ayudado en tu aprendizaje, nos vemos en la próxima práctica libre."
        f"\n\n¿Desea reiniciar un quiz?"
    )

def convert_latex_string_to_html(latex_str):
    import tempfile
    import pypandoc
    try:
        pandoc_path = pypandoc.get_pandoc_path()

        with tempfile.NamedTemporaryFile(suffix=".tex", delete=False) as tmp_tex:
            tmp_tex.write(latex_str.encode('utf-8'))
            tmp_tex_path = tmp_tex.name

        tmp_html_path = tmp_tex_path.replace(".tex", ".html")

        subprocess.run([pandoc_path, tmp_tex_path, "-o", tmp_html_path], check=True)

        with open(tmp_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        os.remove(tmp_tex_path)
        os.remove(tmp_html_path)

        return html_content
    except Exception as e:
        return f"<p>Error al convertir LaTeX: {str(e)}</p>"

def get_available_temas(week):
    """
    Retorna la lista de temas que aparecen en preguntas con week <= user_week.
    Permite múltiples temas por pregunta.
    """
    valid_temas = set()
    for pid, data in Preguntas.items():
        if data['week'] <= week:
            temas = data['tema'].split(",")  # Permitir múltiples temas separados por comas
            valid_temas.update([tema.strip() for tema in temas])  # Añadimos .strip() para limpiar espacios
    return sorted(valid_temas)

def retrieve_difs_for_temas(temas, week):
    """
    Retorna las dificultades disponibles para las preguntas que contienen al menos uno de los temas seleccionados.
    """
    difs = set()
    for pid, data in Preguntas.items():
        pregunta_temas = set(tema.strip() for tema in data['tema'].split(","))  # Limpiar espacios
        if pregunta_temas.intersection(temas) and data['week'] <= week:
            difs.add(data['dif'])
    return sorted(difs)

def init_question(selected_dif):
    """
    Selecciona una pregunta al azar que pertenezca a al menos uno de los temas elegidos.
    Ahora selecciona de manera equitativa entre temas individuales y combinaciones.
    """
    global selected_theme, user_week
    temas_seleccionados = set(tema.strip() for tema in selected_theme.split(","))  # Limpiamos espacios

    # Filtrar preguntas que tienen al menos uno de los temas seleccionados
    candidates = [
        pid for pid, data in Preguntas.items()
        if set(tema.strip() for tema in data['tema'].split(",")) & temas_seleccionados  # Limpiamos espacios
        and data['dif'] == selected_dif
        and data['week'] <= user_week
        and not any(r[0] == pid and r[1] for r in record)  # Excluir preguntas ya acertadas
    ]

    if not candidates:
        return None  # No hay preguntas disponibles

    return random.choice(candidates)  # Selecciona una pregunta aleatoria de la lista filtrada

def call_question(pid):
    """Obtiene la información de una pregunta por su ID"""
    return Preguntas[pid]

def update_question(success_fail, pid):
    """
    Selecciona la siguiente pregunta aleatoria dentro del conjunto total de preguntas disponibles.
    - Si una pregunta se acierta, se elimina del conjunto.
    - Si una pregunta se falla, sigue disponible.
    """
    global selected_theme, user_week, record
    temas_seleccionados = set(tema.strip() for tema in selected_theme.split(","))  # Limpiamos espacios

    # Construir una lista de todas las preguntas disponibles (las que NO han sido acertadas)
    available_questions = [
        qid for qid, data in Preguntas.items()
        if set(tema.strip() for tema in data['tema'].split(",")) & temas_seleccionados and data['week'] <= user_week
        and not any(r[0] == qid and r[1] for r in record)  # Eliminar solo preguntas ya acertadas
    ]

    if not available_questions:  # Si no hay más preguntas disponibles, terminar el quiz
        return None

    return random.choice(available_questions)  # Selecciona una pregunta aleatoria de las disponibles

def normalize_answer(answer):
    """Normaliza una respuesta para compararla"""
    normalized = answer.strip().lower()
    
    # Para respuestas de opción múltiple, extraer solo la letra a, b, c, d si es una sola letra
    if len(normalized) == 1 and normalized in 'abcd':
        return normalized

@app.route('/api/query', methods=['POST'])
def receive_question():
    global inicializador_id, record, info, success_fail, selected_theme
    global user_week, current_question_responded

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibió información'}), 400

        responseStudent = data.get('responseStudent', '')
        history = data.get('history') or []
        q_id = history[-1]['id'] if history else 0
        question_txt = history[-1]['responseChatbot'] if history else ""

        # Manejo de comando de reinicio
        if responseStudent.strip().lower() == "reiniciar":
            reset_global_state()
            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': "reinit"
            }
            return jsonify({'message': resp})

        # 1. El chatbot preguntó la semana
        if "En qué semana de universidad estás" in question_txt:
            try:
                week = int(responseStudent.strip())
                if week <= 0:
                    raise ValueError("Semana debe ser un número positivo")
            except ValueError:
                resp = {
                    'id': q_id,
                    'responseStudent': responseStudent,
                    'responseChatbot': "Respuesta inválida. Ingrese un número de semana positivo."
                }
                return jsonify({'message': resp})

            user_week = week

            # Filtrar temas según las preguntas con week <= user_week
            allowed_temas = get_available_temas(week)
            
            if not allowed_temas:
                msg = (
                    "No hay preguntas disponibles para tu semana.\n\n"
                    f"Semana: {week}\n\n"
                    "¿Deseas reiniciar un quiz?"
                )
                resp = {
                    'id': q_id,
                    'responseStudent': responseStudent,
                    'responseChatbot': msg
                }
                return jsonify({'message': resp})
                
            # Dificultades para esos temas
            difs = retrieve_difs_for_temas(allowed_temas, week)

            temas_str = "\n".join(f"- {t}" for t in allowed_temas)
            difs_str = ", ".join(str(d) for d in difs)

            msg = (
                "Elige un tema y una dificultad dentro de la lista para empezar el quiz:\n\n"
                f"Temas:\n{temas_str}\n\n"
                f"Dificultades: {difs_str}\n\n"
                "Tú respuesta debe ser: tema dificultad (ej: lógica 2)\n\n"
                "Para múltiples temas: lógica, conjuntos 2\n\n"
                "Por favor escribe con tildes las palabras cuando corresponda."
            )
            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': msg
            }
            return jsonify({'message': resp})

        # 2. El usuario selecciona tema y dificultad
        if "Elige un tema y una dificultad" in question_txt:
            # Obtener temas y dificultades disponibles
            allowed_temas = get_available_temas(user_week)
            difs = retrieve_difs_for_temas(allowed_temas, user_week)

            temas_usuario = []
            selected_dif = None

            # Procesar la respuesta del usuario
            # Primero intentamos buscar el número al final
            match = re.search(r'(\d+)$', responseStudent.strip())
            if not match:
                # No hay número al final
                temas_str = ", ".join(allowed_temas)
                difs_str = ", ".join(map(str, difs))
                msg = (
                    "No entendí tu respuesta. Debe terminar con un número de dificultad.\n\n"
                    "Elige uno o más temas separados por comas y una dificultad dentro de la lista:\n\n"
                    f"Temas: {temas_str}\n\n"
                    f"Dificultades: {difs_str}\n\n"
                    "Ejemplo: lógica, conjuntos 2\n\n"
                    "Por favor, intenta nuevamente con el formato correcto. Escribe con tildes las palabras cuando corresponda."
                )
                return jsonify({'message': {'id': q_id, 'responseStudent': responseStudent, 'responseChatbot': msg}})
            
            # Extraer la dificultad
            try:
                selected_dif = int(match.group(1))
            except ValueError:
                selected_dif = None
                
            # Extraer los temas (todo lo demás antes del número)
            temas_text = responseStudent[:match.start()].strip()
            temas_ingresados = [t.strip() for t in temas_text.split(",")]
            
            # Verificar que los temas ingresados sean válidos
            for tema in temas_ingresados:
                if tema.lower() in [t.lower() for t in allowed_temas]:
                    temas_usuario.append(tema)

            if not temas_usuario or selected_dif not in difs:
                temas_str = ", ".join(allowed_temas)
                difs_str = ", ".join(map(str, difs))
                msg = (
                    "No entendí tu respuesta. Debe terminar con un número de dificultad.\n\n"
                    "Elige uno o más temas separados por comas y una dificultad dentro de la lista:\n\n"
                    f"Temas: {temas_str}\n\n"
                    f"Dificultades: {difs_str}\n\n"
                    "Ejemplo: lógica, conjuntos 2\n\n"
                    "Por favor, intenta nuevamente con el formato correcto. Escribe con tildes las palabras cuando corresponda."
                )
                return jsonify({'message': {'id': q_id, 'responseStudent': responseStudent, 'responseChatbot': msg}})

            # Guardamos los temas seleccionados en una cadena separada por comas
            selected_theme = ",".join(temas_usuario)

            # Limpiar el registro para el nuevo quiz
            record = []

            # Seleccionar una pregunta con al menos uno de los temas elegidos
            inicializador_id = init_question(selected_dif)
            if inicializador_id is None:
                temas_str = ", ".join(allowed_temas)
                difs_str = ", ".join(map(str, difs))
                msg = (
                    "No hay ejercicios disponibles con los temas y dificultad indicados.\n\n"
                    "Elige uno o más temas separados por comas y una dificultad dentro de la lista:\n\n"
                    f"Temas: {temas_str}\n"
                    f"Dificultades: {difs_str}\n\n"
                    "Ejemplo: lógica, conjuntos 2\n\n"
                    "Por favor, intenta nuevamente con el formato correcto."
                    
                )
                return jsonify({'message': {'id': q_id, 'responseStudent': responseStudent, 'responseChatbot': msg}})

            # Nuevo: marcar que la pregunta no ha sido respondida
            current_question_responded = False
            
            # Obtener el enunciado y convertirlo a HTML
            latex_str = Preguntas[inicializador_id]['enunciado']
            responseChatbot = convert_latex_string_to_html(latex_str)

            return jsonify({'message': {'id': q_id, 'responseStudent': responseStudent, 'responseChatbot': responseChatbot}})

        # 3. Manejo de "¿Desea Continuar?" o "¿Desea reiniciar?"
        if "¿Desea continuar con el mismo tema?" in question_txt or "¿Desea continuar con el mismo tema, elegir otro tema, o finalizar?" in question_txt:
            # Respuesta después de un fallo
            resp_normalizada = responseStudent.lower().strip()
            if resp_normalizada in ["si", "sí", "yes", "s"]:
                # Continuar con el mismo tema y dificultad
                new_id = update_question(success_fail, inicializador_id)
                if new_id is None:
                    responseChatbot = tail_message()
                else:
                    inicializador_id = new_id
                    current_question_responded = False
                    latex_str = Preguntas[inicializador_id]['enunciado']
                    responseChatbot = convert_latex_string_to_html(latex_str)
            elif resp_normalizada in ["no", "n"]:
                # Volver a preguntar por tema y dificultad
                allowed_temas = get_available_temas(user_week)
                difs = retrieve_difs_for_temas(allowed_temas, user_week)
                temas_str = "\n".join(f"- {t}" for t in allowed_temas)
                difs_str = ", ".join(str(d) for d in difs)

                responseChatbot = (
                    "Elige un tema y una dificultad dentro de la lista para continuar el quiz:\n\n"
                    f"Temas:\n{temas_str}\n\n"
                    f"Dificultades: {difs_str}\n\n"
                    "Tu respuesta debe ser: tema dificultad (ej: lógica 2)\n"
                    "Para múltiples temas: lógica, conjuntos 2\n"
                    "Por favor escribe con tildes las palabras cuando corresponda."
                )
            elif resp_normalizada in ["finalizar", "terminar", "fin", "salir", "exit"]:
                # Finalizar el quiz
                responseChatbot = tail_message()
            else:
                responseChatbot = "No entendí tu respuesta. ¿Desea continuar con el mismo tema (sí), elegir otro tema (no), o finalizar?"

            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': resp})

        if "¿Desea reiniciar un quiz?" in question_txt or "¿Desea reiniciar un quiz?" in question_txt:
            resp_normalizada = responseStudent.lower().strip()
            if resp_normalizada in ["si", "sí", "yes", "s"]:
                reset_global_state()
                responseChatbot = "reinit"
            elif resp_normalizada in ["no", "n"]:
                responseChatbot = os.path.join('react_build','static', 'Images', 'exit.png')
            else:
                responseChatbot = "No entendí tu respuesta. ¿Desea reiniciar un quiz? (sí/no)"

            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': resp})

        # 4. Evaluar la respuesta a una pregunta
        # Verificamos si la pregunta es un HTML (enunciado de ejercicio)
        if "<html" in question_txt or "<p>" in question_txt:
            # Es una pregunta con formato HTML (enunciado)
            if current_question_responded:
                # Si ya respondió a esta pregunta, probablemente sea un error de UI
                responseChatbot = "Ya has respondido a esta pregunta. ¿Desea Continuar? (si/no)"
            else:
                info = call_question(inicializador_id)
                # Chequeo de acierto para respuestas de opción múltiple
                normalized_response = normalize_answer(responseStudent)
                normalized_correct = [normalize_answer(r) for r in info['res']]
                
                # Verificar si la respuesta es válida (a, b, c, d)
                if normalized_response not in ['a', 'b', 'c', 'd'] and not any(normalized_response == correct for correct in normalized_correct):
                    responseChatbot = (
                        "Por favor, responde con una de las opciones: a, b, c, o d.\n\n"
                        "Inténtalo de nuevo con la misma pregunta."
                    )
                    current_question_responded = False  # Permitir responder de nuevo
                    resp = {
                        'id': q_id,
                        'responseStudent': responseStudent,
                        'responseChatbot': responseChatbot
                    }
                    return jsonify({'message': resp})
                    
                success_fail = normalized_response in normalized_correct
                
                # Marcar como respondida para evitar respuestas duplicadas
                current_question_responded = True
                
                responseChatbot = success_message() if success_fail else fail_message()
            
            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': resp})

        # Si llegamos aquí, la respuesta del usuario no coincide con ningún estado esperado
        responseChatbot = (
            "No entendí tu respuesta en el contexto actual.\n\n"
            "Por favor, sigue las instrucciones proporcionadas o escribe 'reiniciar' para comenzar de nuevo."
        )
        
        resp = {
            'id': q_id,
            'responseStudent': responseStudent,
            'responseChatbot': responseChatbot
        }
        return jsonify({'message': resp})

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error en /api/query: {str(e)}\n{error_details}")
        return jsonify({'error': f"Error en el servidor: {str(e)}"}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# ---------------------------------------------------------------------------------
if __name__ == '__main__':
    load_history()
    app.run(host="0.0.0.0", port=3001, debug=True)