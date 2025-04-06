#----------------------------------------------------------#
# Proyecto: Pensando Problemas IA
# Nombre: Construcción Preliminar de Matrices de Similitud
# Por: Mateo Alejandro Rodríguez Ramírez
#----------------------------------------------------------#

#-------------------------------
# Cargue de Paquetes:
import os
import graph_tools
import random


import itertools as it
import pandas as pd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import sklearn.metrics as metrics

#-------------------------------
# Cargue de Base de Datos
direccion = r'./' # Fijado de la dirección
os.chdir(direccion) # Fijado del Directorio
os.listdir() # Verificación del contenido del Directorio

Base = pd.read_excel('./CLASIFICACION_EJERCICIOS_TRADUCCION.xlsx',sheet_name='Raw') # Cargue de la base completa
Base = Base[Base.sum(axis=1)>0] # Eliminación de Filas innecesarias

Base.columns # Verificación Columnas
Base.index # Verificación Indice Filas

#-------------------------------
# Funciones de Tratamiento de Vectores: Matrices de Métricas
dimensions = Base.shape # Dimensiones de los Datos
n_nodes = dimensions[0] # Número de Nodos-Preguntas
n_vars = dimensions[1]-1 # Número de Variables-Conceptos
Base_Metrizable = Base.iloc[:,:n_vars] # Base de datos que no tiene en cuenta Niveles de Dificultad
Tratamientos = {'Mean_Sim':(1/n_vars)*(metrics.pairwise.manhattan_distances(Base_Metrizable)),
                'Cosine_Sim':metrics.pairwise.cosine_similarity(Base_Metrizable)
                } # Matrices de Similitud: % de diferencias, sim coseno. 
Filtros = {'Mean_Sim':'A<={}'.format(0.2),
           'Cosine_Sim':'A>={}'.format(np.cos(np.pi/4))
           } # Filtrado de las Matrices de Similitud: % dif<=20%, coseno>=cos(pi/4).

Tratados = {} # Creación de Matrices de Adyacencia Simétricas, Primera Aproximación: Sin Dificultad Incluida
for i in Tratamientos.keys():
    A = Tratamientos[i] # Base de similitudes a tratar
    Tratados[i] = eval(Filtros[i]) # Filtrado según criterio
    for j in range(n_nodes): # Eliminación de Self Loops
        Tratados[i][j][j]=0 
    print('Realizado: {} \n'.format(i)+'-'*30)

Tratados_Dificultad = {} # Creación de Matrices de Adyacencia, Segunda Aproximación: Niveles de dificultad cercanos: max 1 und de diferencia del mayor al menor
Dificultades = Base['Dificultad']
for k in Tratados:
    A = Tratados[k]
    m = A.shape[0]
    for i in range(m):
        for j in range(m):
            diff = Dificultades[i]-Dificultades[j]
            if (diff == 1) | (diff == 0):
                pass
            else:
                A[i][j] = False
    Tratados_Dificultad[k] = A
    print('Realizado: {} \n'.format(k)+'-'*30)

#-------------------------------
# Creación de Grafos (Primera aproximación): Sin tener en cuenta la dificultad.

Grafos = {i:nx.from_numpy_array(Tratados[i]) for i in Tratados} # Creación de Grafos a partir de Matriz de Adyacencia.

for grafo in Grafos.values(): # Grafico de los Grafos
    nx.draw(grafo)
    plt.show()

#-------------------------------
# Creación de Grafos (Segunda aproximación): Teniendo en cuenta la dificultad.

Grafos_Dificultad = {i:nx.from_numpy_array(Tratados_Dificultad[i],create_using=nx.DiGraph) for i in Tratados_Dificultad} # Creación de Grafos a partir de Matriz de Adyacencia.

for grafo in Grafos_Dificultad.values(): # Grafico de los Grafos
    nx.draw(grafo)
    plt.show()
