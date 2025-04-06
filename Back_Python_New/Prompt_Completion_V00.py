#----------------------------------------------------------#
# Proyecto: Pensando Problemas IA
# Nombre: Implementación Prompt/Completion V00
# Por: Mateo Alejandro Rodríguez Ramírez
#----------------------------------------------------------#

import os
import re

def load_preguntas_from_latex(file_name):
    """
    Lee el archivo LaTeX y extrae preguntas según el patrón:
    \begin{question}{id}{tema}{dif}{res}{enunciado}
    \end{question}
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = r"\\begin\{question\}\{(\d+)\}\{([^\}]+)\}\{(\d+)\}\{([^\}]+)\}\{(\d+)\}\{([\s\S]+?)\}\s*\\end\{question\}"



    preguntas = {}
    matches = re.findall(pattern, content, re.DOTALL)

    for match in matches:
        qid_str, tema, dif_str, res_str, week_str, enunciado = match

        qid = int(qid_str)
        dif = int(dif_str)
        week = int(week_str) 

        res_list = [r.strip() for r in res_str.split(',')]
        preguntas[qid] = {
            'tema': tema,
            'dif': dif,
            'res': res_list,
            'week': week,
            'enunciado': enunciado.strip()
        }
    return preguntas

Preguntas = load_preguntas_from_latex("Preguntas.tex")

print(Preguntas)