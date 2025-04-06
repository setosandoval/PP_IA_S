#----------------------------------------------------------#
# Proyecto: Pensando Problemas IA
# Nombre: Implementación Pipeline V00
# Por: Mateo Alejandro Rodríguez Ramírez
#----------------------------------------------------------#


import os
import random
import psutil
from Prompt_Completion_V00 import Preguntas

k = 140
emph = '#' + '-'*k + '#'

def init_message():
    print(emph)
    codigo = input('\nEscriba su Código de Estudiante: ')
    print(emph)
    return codigo

def head():
    head_message = (
        emph + '\nUsted iniciará la práctica libre de ejercicios.\n'
        'Por favor sientase con toda la confianza de responder las preguntas.\n'
        'Los resultados que obtenga serán utilizados para refinar nuestro algoritmo.\n\n'
        'Atentamente: Equipo de Pensando Problemas.\n' + emph
    )
    print(head_message)

def tail(n):
    tail_message = (
        '\n\n' + emph +
        f'\nHa finalizado la práctica.\nUsted realizó {n} ejercicios.\n' +
        emph
    )
    print(tail_message)

def ask_message():
    ask_msg = input('\n\nEscriba su respuesta: ')
    return ask_msg

def fail_message():
    fail_msg = (
        '\n\nSe ha equivocado en la elección de la respuesta correcta. '
        'A continuación se le mostrará un ejercicio de nivel menor o igual.\n\n'
    )
    print(fail_msg)

def success_message():
    success_msg = (
        '\n\nHa acertado en la elección de la respuesta correcta. '
        'A continuación se le mostrará un ejercicio de nivel superior o igual.\n\n'
    )
    print(success_msg)

def continuacion():
    continuar = input('\n¿Desea Continuar (yes:1,no:0)?: ')
    return (continuar == '1')

def call_question_text(pid):
    pregunta = Preguntas[pid]
    print("Pregunta:", pregunta['enunciado'])

def call_question(pid):
    return Preguntas[pid]

def close_image():
    for proc in psutil.process_iter():
        try:
            if proc.name() == "display":
                proc.kill()
        except:
            pass

def update_question(success_fail, info, pid):
    dificultad_actual = Preguntas[pid]['dif']
    candidates = []
    for qid, data in Preguntas.items():
        if qid == pid:
            continue
        if success_fail:
            if data['dif'] >= dificultad_actual:
                candidates.append(qid)
        else:
            if data['dif'] <= dificultad_actual:
                candidates.append(qid)

    if not candidates:
        print('\nNo hay más ejercicios disponibles.\n')
        return None
    return random.choice(candidates)

def program():
    record = []
    enter = True
    n = 0
    pid = 1
    while enter:
        if n == 0:
            head()
        n += 1

        # Muestra la pregunta
        call_question_text(pid)
        info = call_question(pid)
        response = ask_message()
        success_fail = (response.strip().lower() in [r.lower() for r in info['res']])
        record.append((pid, success_fail))

        if success_fail:
            success_message()
        else:
            fail_message()

        enter = continuacion()
        pid = update_question(success_fail, info, pid)
        if pid is None:
            enter = False

        if not enter:
            tail(n)
    return record

def run_program():
    nombre = init_message()
    puntaje = program()
    return {nombre: puntaje}

if __name__ == "__main__":
    run_program()




