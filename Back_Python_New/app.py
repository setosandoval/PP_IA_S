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



app = Flask(__name__, static_folder='react_build')
CORS(app)

# ---------------------------------------------------------------------------------
# Ruta opcional para convertir un archivo .tex completo a HTML (vía Pandoc)
# ---------------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------------
# Variables globales
# ---------------------------------------------------------------------------------
History = [[
    {
        "id": 0,
        "responseChatbot": (
            "Usted iniciará la práctica libre de ejercicios que el equipo pedagógico de Pensando Problemas preparó para usted.\n"
            "Por favor siéntase con toda la confianza de responder las preguntas según sus conocimientos.\n"
            "Los resultados que obtenga serán utilizados para refinar nuestro algoritmo.\n"
            "Adicionalmente, si encuentra algún problema, háganoslo saber.\n\n"
            "Atentamente: Equipo de Pensando Problemas."
        )
    },
    {
        "id": 1,
        "responseChatbot": "Lo primero que hay que saber es: ¿en qué semana de universidad estás?"
    }
]]
history_path = "Back_Python_New/react_build/"
record = []            # Registro de (id_pregunta, acierto?)
inicializador_id = 1   # ID de la pregunta actual
info = {}              # Info de la pregunta actual
success_fail = True
selected_theme = None
user_week = None

def load_history():
    global History, inicializador_id
    file_path = os.path.join(history_path, "History.json")
    inicializador_id = 1
    History = [[
        {
            "id": 0,
            "responseChatbot": (
                "Usted iniciará la práctica libre de ejercicios que el equipo pedagógico de Pensando Problemas preparó para usted.\n"
                "Por favor siéntase con toda la confianza de responder las preguntas.\n"
                "Los resultados que obtenga serán utilizados para refinar nuestro algoritmo.\n"
                "Adicionalmente, si encuentra algún problema, háganoslo saber.\n\n"
                "Atentamente: Equipo de Pensando Problemas."
            )
        },
        {
            "id": 1,
            "responseChatbot": "Lo primero que hay que saber es: ¿en qué semana de universidad estás?"
        }
    ]]
    with io.open(file_path, 'w', encoding='utf-8') as history_file:
        history_file.write(json.dumps(History))

def fail_message():
    return (
        "Se ha equivocado en la elección de la respuesta correcta. "
        "A continuación se le mostrará un ejercicio de nivel menor o igual al realizado. "
        "¿ Desea Continuar ?"
    )

def success_message():
    return (
        "Ha acertado en la elección de la respuesta correcta. "
        "A continuación se le mostrará un ejercicio de nivel superior o igual al realizado. "
        "¿ Desea Continuar ?"
    )

def tail_message():
    global record
    num_exercises = len(record)
    ejercicio_text = "ejercicio" if num_exercises == 1 else "ejercicios"
    if num_exercises == 0:
        return "Ha finalizado la práctica.\nUsted realizó 0 ejercicios.\n\n¿ Desea reiniciar un quiz ?"

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

    summary_succeed = format_difs(difs_succeed)
    summary_failed = format_difs(difs_failed)
    rec_str = (
        f"Aquí se encuentra el resumen de la práctica:\n\n"
        f"Usted ha acertado ({total_acertadas} {acertadas_text}):\n{summary_succeed}\n\n"
        f"Usted ha fallado ({total_falladas} {falladas_text}):\n{summary_failed}"
    )

    return (
        f"Ha finalizado la práctica.\n"
        f"Ha completado todos los ejercicios disponibles con los parámetros ingresados.\n"
        f"Usted realizó {num_exercises} {ejercicio_text} y el tema elegido fue {temas_str}.\n\n"
        f"{rec_str}"
        f"\n\n Espero haber ayudado en tu aprendizaje, nos vemos en la próxima práctica libre."
        f"\n\n¿ Desea reiniciar un quiz ?"
    )



def convert_latex_string_to_html(latex_str):
    """
    Convierte un string LaTeX a HTML usando Pandoc de forma temporal.
    Retorna el HTML como string.
    """
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(suffix=".tex", delete=False) as tmp_tex:
            tmp_tex.write(latex_str.encode('utf-8'))
            tmp_tex_path = tmp_tex.name

        tmp_html_path = tmp_tex_path.replace(".tex", ".html")

        subprocess.run(["pandoc", tmp_tex_path, "-o", tmp_html_path], check=True)

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
            valid_temas.update(temas)
    return sorted(valid_temas)


def retrieve_difs_for_temas(temas, week):
    """
    Retorna las dificultades disponibles para las preguntas que contienen al menos uno de los temas seleccionados.
    """
    difs = set()
    for pid, data in Preguntas.items():
        pregunta_temas = set(data['tema'].split(","))  # Separar temas en lista
        if pregunta_temas.intersection(temas) and data['week'] <= week:
            difs.add(data['dif'])
    return sorted(difs)


def init_question(selected_dif):
    """
    Selecciona una pregunta al azar que pertenezca a al menos uno de los temas elegidos.
    Ahora selecciona de manera equitativa entre temas individuales y combinaciones.
    """
    global selected_theme, user_week
    temas_seleccionados = set(selected_theme.split(","))  # Convertir los temas ingresados a un conjunto

    # Filtrar preguntas que tienen al menos uno de los temas seleccionados
    candidates = [
        pid for pid, data in Preguntas.items()
        if temas_seleccionados & set(data['tema'].split(","))  # Usamos & para verificar intersección
        and data['dif'] == selected_dif
        and data['week'] <= user_week
    ]

    if not candidates:
        return None  # No hay preguntas disponibles

    return random.choice(candidates)  # Selecciona una pregunta aleatoria de la lista filtrada



def call_question(pid):
    return Preguntas[pid]

def update_question(success_fail, pid):
    """
    Selecciona la siguiente pregunta aleatoria dentro del conjunto total de preguntas disponibles.
    - Si una pregunta se acierta, se elimina del conjunto.
    - Si una pregunta se falla, sigue disponible.
    """
    global selected_theme, user_week
    temas_seleccionados = set(selected_theme.split(","))

    # Registrar la pregunta en el historial
    record.append((pid, success_fail))

    # Construir una lista de todas las preguntas disponibles (las que NO han sido acertadas)
    available_questions = [
        qid for qid, data in Preguntas.items()
        if set(data['tema'].split(",")) & temas_seleccionados and data['week'] <= user_week
        and not any(r[0] == qid and r[1] for r in record)  # Eliminar solo preguntas ya acertadas
    ]

    if not available_questions:  # Si no hay más preguntas disponibles, terminar el quiz
        return None

    return random.choice(available_questions)  # Selecciona una pregunta aleatoria de las disponibles




@app.route('/api/query', methods=['POST'])
def receive_question():
    global inicializador_id, record, info, success_fail, selected_theme
    global user_week

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibió información'}), 400

        responseStudent = data.get('responseStudent', '')
        history = data.get('history') or []
        q_id = history[-1]['id'] if history else 0
        question_txt = history[-1]['responseChatbot'] if history else ""

        if responseStudent.strip().lower() == "reiniciar":
            record.clear()
            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': "reinit"
            }
            return jsonify({'message': resp})

        # 1. El chatbot preguntó la semana
        if "en qué semana de universidad estás" in question_txt:
            try:
                week = int(responseStudent.strip())
            except:
                resp = {
                    'id': q_id,
                    'responseStudent': responseStudent,
                    'responseChatbot': "Respuesta inválida. Ingrese un número de semana."
                }
                return jsonify({'message': resp})

            user_week = week

            # Filtrar temas según las preguntas con week <= user_week
            allowed_temas = get_available_temas(week)
            # Dificultades para esos temas
            difs = retrieve_difs_for_temas(allowed_temas, week)

            if not allowed_temas or not difs:
                msg = (
                    "No hay preguntas disponibles para tu semana.\n"
                    f"Semana: {week}\n"
                    "¿Deseas reiniciar un quiz?"
                )
                resp = {
                    'id': q_id,
                    'responseStudent': responseStudent,
                    'responseChatbot': msg
                }
                return jsonify({'message': resp})

            temas_str = "\n".join(f"- {t}" for t in allowed_temas)
            difs_str = ", ".join(str(d) for d in difs)

            msg = (
                "Elige un tema y una dificultad dentro de la lista para empezar el quiz:\n\n"
                f"Temas:\n{temas_str}\n\n"
                f"Dificultades:\n{difs_str}\n\n"
                "Tu respuesta debe ser: tema dificultad (ej: logica 2)"
            )
            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': msg
            }
            return jsonify({'message': resp})

        if "Elige un tema y una dificultad" in question_txt:
            # Obtener temas y dificultades disponibles
            allowed_temas = get_available_temas(user_week)
            difs = retrieve_difs_for_temas(allowed_temas, user_week)

            temas_usuario = []
            selected_dif = None

            # Procesar la respuesta del usuario
            response_parts = responseStudent.lower().strip().split()
            
            if len(response_parts) < 2:  # Verifica que haya al menos un tema y una dificultad
                temas_str = ", ".join(allowed_temas)
                difs_str = ", ".join(map(str, difs))
                msg = (
                    "No entendí tu respuesta.\n"
                    "Elige uno o más temas separados por comas y una dificultad dentro de la lista:\n\n"
                    f"Temas: {temas_str}\n"
                    f"Dificultades: {difs_str}\n\n"
                    "Ejemplo: logica, conjuntos 2"
                )
                return jsonify({'message': {'id': q_id, 'responseStudent': responseStudent, 'responseChatbot': msg}})

            # Extraer la dificultad (debe ser el último elemento)
            try:
                selected_dif = int(response_parts[-1])
            except ValueError:
                selected_dif = None  # No es un número válido

            # Extraer los temas (todo lo demás antes del número)
            temas_ingresados = " ".join(response_parts[:-1]).replace(" ", "").split(",")

            # Verificar que los temas ingresados sean válidos
            for tema in temas_ingresados:
                if tema in allowed_temas:
                    temas_usuario.append(tema)

            if not temas_usuario or selected_dif not in difs:
                temas_str = ", ".join(allowed_temas)
                difs_str = ", ".join(map(str, difs))
                msg = (
                    "No entendí tu respuesta.\n"
                    "Elige uno o más temas separados por comas y una dificultad dentro de la lista:\n\n"
                    f"Temas: {temas_str}\n"
                    f"Dificultades: {difs_str}\n\n"
                    "Ejemplo: logica, conjuntos 2"
                )
                return jsonify({'message': {'id': q_id, 'responseStudent': responseStudent, 'responseChatbot': msg}})

            # Guardamos los temas seleccionados en una cadena separada por comas
            selected_theme = ",".join(temas_usuario)

            # Seleccionar una pregunta con al menos uno de los temas elegidos
            inicializador_id = init_question(selected_dif)
            if inicializador_id is None:
                temas_str = ", ".join(allowed_temas)
                difs_str = ", ".join(map(str, difs))
                msg = (
                    "No hay ejercicios disponibles con los temas y dificultad indicados.\n"
                    "Elija temas y dificultad dentro de la lista disponible:\n\n"
                    f"Temas: {temas_str}\n"
                    f"Dificultades: {difs_str}\n\n"
                    "Ejemplo: logica, conjuntos 2"
                )
                return jsonify({'message': {'id': q_id, 'responseStudent': responseStudent, 'responseChatbot': msg}})

            latex_str = Preguntas[inicializador_id]['enunciado']
            responseChatbot = convert_latex_string_to_html(latex_str)

            return jsonify({'message': {'id': q_id, 'responseStudent': responseStudent, 'responseChatbot': responseChatbot}})


        # 3. Manejo de "¿Desea Continuar?" o "¿Desea reiniciar?"
        if "¿ Desea Continuar ?" in question_txt:
            if responseStudent.lower() in ["si", "sí", "yes"]:
                new_id = update_question(success_fail, inicializador_id)
                if new_id is None:
                    responseChatbot = (
                        "Lamentablemente no hay más preguntas, ya completó todos los ejercicios posibles con los parámetros ingresados.\n\n"
                        + tail_message()
                    )

                else:
                    inicializador_id = new_id
                    latex_str = Preguntas[inicializador_id]['enunciado']
                    responseChatbot = convert_latex_string_to_html(latex_str)
            elif responseStudent.lower() in ["no"]:
                responseChatbot = tail_message()
            else:
                responseChatbot = "No entendí tu respuesta. ¿ Desea Continuar ?"

            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': resp})

        if "¿ Desea reiniciar un quiz ?" in question_txt:
            if responseStudent.lower() in ["si", "sí", "yes"]:
                record.clear()
                responseChatbot = "reinit"
            elif responseStudent.lower() in ["no"]:
                responseChatbot = os.path.join('react_build','static', 'Images', 'exit.png')
            else:
                responseChatbot = "No entendí tu respuesta. ¿ Desea reiniciar un quiz ?"

            resp = {
                'id': q_id,
                'responseStudent': responseStudent,
                'responseChatbot': responseChatbot
            }
            return jsonify({'message': resp})

        # 4. Evaluar la respuesta
        if not responseStudent.strip():
            return jsonify({'error': 'La pregunta está vacía'}), 400

        info = call_question(inicializador_id)
        # Chequeo de acierto
        normalized_response = normalize_answer(responseStudent)
        normalized_correct = [normalize_answer(r) for r in info['res']]
        success_fail = normalized_response in normalized_correct
        record.append((inicializador_id, success_fail))

        responseChatbot = success_message() if success_fail else fail_message()
        resp = {
            'id': q_id,
            'responseStudent': responseStudent,
            'responseChatbot': responseChatbot
        }
        return jsonify({'message': resp})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

def normalize_answer(answer):
    normalized = answer.strip().lower()
    normalized = re.sub(r"[\(\)\[\]\{\}]", "", normalized)
    return normalized.strip()

# ---------------------------------------------------------------------------------
if __name__ == '__main__':
    load_history()
    app.run(host="0.0.0.0", port=3001, debug=True)
