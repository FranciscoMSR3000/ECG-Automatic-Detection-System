# -*- coding: utf-8 -*-
"""
Lector de ECG desde PDF
========================
Convierte archivos PDF de electrocardiogramas (ECG) a datos numéricos en formato CSV.

Flujo general:
  1. Convierte el PDF a SVG usando Spire.PDF.
  2. Parsea el SVG para localizar las señales de cada derivación.
  3. Extrae las coordenadas (X, Y) de cada señal.
  4. Guarda los datos en archivos CSV y genera gráficas PNG.

Dependencias principales:
  - spire.pdf  : conversión PDF → SVG
  - lxml       : parseo eficiente del SVG
  - numpy      : manejo de arrays numéricos
  - pandas     : exportación a CSV
  - matplotlib : generación de gráficas

Autor: fco_m
Fecha: 2024-02-28
"""
print('hola mundo')
from spire.pdf.common import *
from spire.pdf import *
import os
import svgwrite
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict
from svgpathtools import svg2paths, Path, wsvg
from collections import Counter
import time
from lxml import etree
import csv
import pandas as pd

# Marca de tiempo de inicio para medir el tiempo total de ejecución
inicio = time.time()

# Directorio de trabajo donde se encuentran los archivos PDF de entrada
os.chdir(r"C:\Users\fco_m\OneDrive\Documentos\Lector_ECG")


# ===========================================================================
# SECCIÓN: Funciones auxiliares
# ===========================================================================

def convertir_array_string_a_float(array_string):
    """
    Convierte una lista de strings numéricos a una lista de floats.

    Parámetros
    ----------
    array_string : list[str]
        Lista de cadenas de texto que representan números (e.g. ['1.2', '3.4']).

    Retorna
    -------
    list[float]
        Lista con los mismos valores convertidos a float.
    """
    nuevo_array_float = []
    for string in array_string:
        nuevo_array_float.append(float(string))
    return nuevo_array_float


def read_svg(svg_file):
    """
    Lee un archivo SVG y devuelve su contenido como cadena de texto.

    Utiliza lxml para parsear correctamente la estructura XML del SVG
    antes de convertirlo a string.

    Parámetros
    ----------
    svg_file : str
        Ruta al archivo SVG.

    Retorna
    -------
    str
        Contenido completo del SVG como string UTF-8.
    """
    tree = etree.parse(svg_file)
    root = tree.getroot()
    svg_content = etree.tostring(root, pretty_print=True).decode()
    return svg_content


def promedio_movil(signal, window_size):
    """
    Aplica un suavizado por promedio móvil (media móvil simple) a una señal.

    Se utiliza para reducir el ruido en las señales ECG de archivos "gorditos"
    (SVG de gran tamaño donde las coordenadas no están perfectamente ordenadas).

    Parámetros
    ----------
    signal : list[float]
        Señal de entrada a suavizar.
    window_size : int
        Tamaño de la ventana del promedio móvil (número de muestras).

    Retorna
    -------
    list[float]
        Señal suavizada con la misma longitud que la entrada.
    """
    smoothed_signal = []
    half_window = window_size // 2

    for i in range(len(signal)):
        # Límites de la ventana, gestionando los bordes de la señal
        start = max(0, i - half_window)
        end = min(len(signal), i + half_window + 1)
        smoothed_signal.append(sum(signal[start:end]) / (end - start))

    return smoothed_signal


def valores_repetidos(vector):
    """
    Devuelve el conjunto de elementos que aparecen más de una vez en un vector.

    Parámetros
    ----------
    vector : list
        Lista de elementos a evaluar.

    Retorna
    -------
    set
        Conjunto de elementos repetidos.
    """
    frecuencias = Counter(vector)
    repetidos = {elemento for elemento, frecuencia in frecuencias.items() if frecuencia > 1}
    return repetidos


def encontrar_indices(subcadena, cadena):
    """
    Encuentra todas las posiciones (índices) donde aparece una subcadena dentro de otra cadena.

    Parámetros
    ----------
    subcadena : str
        Texto a buscar.
    cadena : str
        Texto donde se realizará la búsqueda.

    Retorna
    -------
    list[int]
        Lista con todos los índices donde comienza la subcadena.
    """
    indices = []
    indice = cadena.find(subcadena)
    while indice != -1:
        indices.append(indice)
        indice = cadena.find(subcadena, indice + 1)
    return indices


def transforma_codigo_derivacion(Cadena):
    """
    Traduce el código Unicode interno del SVG al nombre estándar de la derivación ECG.

    Los ECG contienen los nombres de las derivaciones codificados en una fuente especial
    (FF0). Esta función mapea esas cadenas Unicode a los nombres clínicos reconocibles.

    Tabla de equivalencias:
        #57417;                      → I
        #57417;&#57417;              → II
        #57417;&#57417;&#57417;      → III
        #57441;&#57430;&#57426;      → aVR
        #57441;&#57430;&#57420;      → aVL
        #57441;&#57430;&#57414;      → aVF
        #57430;.                     → V1
        #57430;c                     → V2
        #57430;f                     → V3
        #57430;M                     → V4
        #57430;v                     → V5
        #57430;8                     → V6

    Parámetros
    ----------
    Cadena : str
        Código Unicode de la derivación extraído del SVG.

    Retorna
    -------
    str
        Nombre estándar de la derivación (e.g. 'I', 'aVR', 'V3').
    """
    if Cadena == "#57417;":
        Derivacion = 'I'
    if Cadena == "#57417;&#57417;":
        Derivacion = 'II'
    if Cadena == "#57417;&#57417;&#57417;":
        Derivacion = 'III'
    if Cadena == "#57441;&#57430;&#57426;":
        Derivacion = 'aVR'
    if Cadena == "#57441;&#57430;&#57420;":
        Derivacion = 'aVL'
    if Cadena == "#57441;&#57430;&#57414;":
        Derivacion = 'aVF'
    if Cadena == "#57430;.":
        Derivacion = 'V1'
    if Cadena == "#57430;c":
        Derivacion = 'V2'
    if Cadena == "#57430;f":
        Derivacion = 'V3'
    if Cadena == "#57430;M":
        Derivacion = 'V4'
    if Cadena == "#57430;v":
        Derivacion = 'V5'
    if Cadena == "#57430;8":
        Derivacion = 'V6'

    return Derivacion


def agregar_sufijo(vector):
    """
    Añade el sufijo '_L' a los elementos duplicados dentro del vector de derivaciones.

    En algunos ECG se muestran dos tiras largas de una misma derivación (por ejemplo,
    derivación II completa al final). Esta función diferencia la primera aparición
    (nombre limpio) de la segunda (nombre + '_L').

    También elimina los corchetes que numpy añade al convertir arrays a string.

    Parámetros
    ----------
    vector : list[str]
        Lista de nombres de derivaciones, posiblemente con duplicados.

    Retorna
    -------
    list[str]
        Lista de nombres únicos: los duplicados llevan el sufijo '_L'.

    Ejemplo
    -------
    ['I', 'II', 'II'] → ['I', 'II', 'II_L']
    """
    nuevo_vector = []
    contador = {}

    for elemento in vector:
        if elemento in contador:
            contador[elemento] += 1
        else:
            contador[elemento] = 1

        sufijo = "" if contador[elemento] == 1 else "_L"
        # Eliminar corchetes de numpy y agregar sufijo diferenciador
        nuevo_vector.append(elemento.strip('[]') + sufijo)

    return nuevo_vector


# ===========================================================================
# SECCIÓN 1: Convertir PDF a SVG
# ===========================================================================

nombre_del_archivo = 'ECG_TEST_8'

# Crear objeto PdfDocument y cargar el archivo PDF de entrada
doc = PdfDocument()
doc.LoadFromFile(nombre_del_archivo + ".pdf")

# Configurar opciones de conversión a SVG (resolución por defecto)
doc.ConvertOptions.SetPdfToSvgOptions()

# Exportar cada página del PDF como archivo SVG independiente
doc.SaveToFile(nombre_del_archivo + ".svg", FileFormat.SVG)
doc.Close()


# ===========================================================================
# SECCIÓN 2: Leer el archivo SVG generado
# ===========================================================================

svg_file = nombre_del_archivo + '.svg'

# Leer el SVG completo como cadena de texto para procesarlo con búsquedas de string
svg_content = read_svg(svg_file)


# ===========================================================================
# SECCIÓN 3: Localizar las señales ECG dentro del SVG
# ===========================================================================
"""
El SVG contiene múltiples elementos gráficos. Las señales ECG se codifican como
trayectorias SVG (elemento <path> con atributo 'd'). Cada trayectoria comienza
con 'M' (moveTo) y continúa con comandos 'L' (lineTo).

Estrategia: buscar todas las trayectorias y quedarse solo con las que superan
una longitud de 1000 caracteres, ya que las señales ECG son las rutas más largas.
"""

subcadena_inicio = 'd="M'   # Marca de inicio de una trayectoria SVG
subcadena_fin    = '"/>'    # Marca de cierre de una trayectoria SVG

# Encontrar todos los índices de inicio y fin de trayectorias en el SVG
indices_de_inicio = np.array(encontrar_indices(subcadena_inicio, svg_content))
indices_de_fin    = np.array(encontrar_indices(subcadena_fin, svg_content))

# Calcular la longitud de cada trayectoria y filtrar las que son señales ECG
Distancias = indices_de_fin - indices_de_inicio
Guia = np.where(Distancias > 1000)
Guia = np.array(Guia)[0]  # Índices de las trayectorias largas (señales ECG)


# ===========================================================================
# SECCIÓN 4: Determinar el método de procesamiento según el tamaño del SVG
# ===========================================================================
"""
Se detectaron dos formatos distintos de ECG según el dispositivo/software que los genera:

  - Método 2 (SVG < 600 KB): Las derivaciones se codifican con Unicode especial.
    Se extrae la cadena y se traduce con transforma_codigo_derivacion().

  - Método 1 (SVG > 600 KB, "gordito"): Las derivaciones aparecen carácter a carácter
    en bloques <text> consecutivos. Se concatenan esos caracteres.
    Además, las coordenadas X no están ordenadas, por lo que se necesita
    ordenarlas y aplicar suavizado por promedio móvil.
"""

Es_gordito = False

if len(svg_content) < 600000:
    print('no gordito')
    metodo = 2

if len(svg_content) > 600000:
    print('3312- tenemos un 3312')
    print('*Musica epica*')
    Es_gordito = True
    metodo = 1


# ===========================================================================
# SECCIÓN 5: Extraer los nombres de las derivaciones
# ===========================================================================
"""
El nombre de cada derivación aparece en el SVG justo después de la trayectoria
de su señal, en uno o varios bloques <text>...</text>.

Se recorre cada señal detectada, se extrae el fragmento de SVG posterior y se
identifica el nombre de la derivación según el método activo.
"""

Derivaciones = []

for j in range(0, len(Guia)):

    Derivacion_individual = []

    if j < len(Guia) - 1:
        # Fragmento del SVG entre el fin de la señal actual y el inicio de la siguiente
        Subespacio_letra_derivacion = svg_content[indices_de_fin[Guia[j]]:indices_de_inicio[Guia[j + 1]]]
        Posiciones_letras = encontrar_indices('</text>', Subespacio_letra_derivacion)

        if metodo == 1:
            # Método 1: concatenar el carácter anterior a cada </text>
            for i in Posiciones_letras:
                Derivacion_individual = np.append(Derivacion_individual, Subespacio_letra_derivacion[i - 1])

            Derivacion_individual = np.array2string(Derivacion_individual, separator='').replace("'", "")
            Derivaciones = np.append(Derivaciones, Derivacion_individual)

        if metodo == 2:
            # Método 2: extraer la cadena Unicode y traducirla al nombre estándar
            posicion_fin    = Subespacio_letra_derivacion.find("</text>")
            posicion_inicio = Subespacio_letra_derivacion.rfind(">&", 0, posicion_fin)
            porcion_deseada = Subespacio_letra_derivacion[posicion_inicio + 2: posicion_fin]
            Derivaciones = np.append(Derivaciones, transforma_codigo_derivacion(porcion_deseada))

    if j == len(Guia) - 1:
        # Última señal: no hay siguiente trayectoria, se toma un fragmento fijo de 1000 chars
        Subespacio_letra_derivacion = svg_content[indices_de_fin[Guia[j]]:indices_de_fin[Guia[j]] + 1000]
        Posiciones_letras = encontrar_indices('</text>', Subespacio_letra_derivacion)

        if metodo == 1:
            for i in Posiciones_letras:
                Derivacion_individual = np.append(Derivacion_individual, Subespacio_letra_derivacion[i - 1])

            Derivacion_individual = np.array2string(Derivacion_individual, separator='').replace("'", "")
            Derivaciones = np.append(Derivaciones, Derivacion_individual)

        if metodo == 2:
            posicion_fin    = Subespacio_letra_derivacion.find("</text>")
            posicion_inicio = Subespacio_letra_derivacion.rfind(">&", 0, posicion_fin)
            porcion_deseada = Subespacio_letra_derivacion[posicion_inicio + 2: posicion_fin]
            Derivaciones = np.append(Derivaciones, transforma_codigo_derivacion(porcion_deseada))


# ===========================================================================
# SECCIÓN 6: Normalizar nombres de derivaciones
# ===========================================================================

# Diferencia las derivaciones duplicadas añadiendo '_L' y elimina corchetes de numpy
Derivaciones = agregar_sufijo(Derivaciones)
print(Derivaciones)


# ===========================================================================
# SECCIÓN 7: Extraer señales y exportar resultados
# ===========================================================================
"""
Para cada señal detectada se:
  1. Extrae la trayectoria SVG (comandos 'M' y 'L' con coordenadas X, Y).
  2. Elimina coordenadas duplicadas para evitar artefactos.
  3. Exporta las coordenadas a CSV.
  4. Genera y guarda una gráfica PNG de la señal.

Los archivos de salida se guardan en un subdirectorio con el nombre del ECG.
"""

# Crear y entrar en el subdirectorio de salida
nombre_directorio = nombre_del_archivo
os.makedirs(nombre_directorio)
os.chdir(nombre_directorio)

for j in range(0, len(Guia)):

    # Extraer el contenido de la trayectoria SVG (sin el prefijo 'M' ni el sufijo '/>')
    Test_letras = svg_content[indices_de_inicio[Guia[j]] + 4:indices_de_fin[Guia[j]] - 40]

    # Separar la trayectoria en comandos individuales usando el separador 'L' (lineTo)
    commands = Test_letras.split('L')
    # Eliminar comandos duplicados preservando el orden de aparición
    commands = list(dict.fromkeys(commands).keys())

    # Extraer las coordenadas X e Y de cada comando
    X = []
    Y = []
    for i in range(1, len(commands) - 2):
        partes = commands[i].split()
        X = np.append(X, partes[0])
        Y = np.append(Y, partes[1])

    # Convertir de string a float
    X = convertir_array_string_a_float(X)
    Y = convertir_array_string_a_float(Y)

    # -------------------------------------------------------------------
    # Camino A: SVG estándar (método 2 / no gordito)
    # Las coordenadas ya están en orden cronológico, sin necesidad de suavizado.
    # -------------------------------------------------------------------
    if Es_gordito == False:

        X = np.array(X)
        Y = np.array(Y)

        encabezado_X = Derivaciones[j] + ' X'
        encabezado_Y = Derivaciones[j] + ' Y'

        df = pd.DataFrame()
        df[encabezado_X] = X
        df[encabezado_Y] = Y

        # Guardar CSV (modo 'a' para poder concatenar varias ejecuciones)
        Datos_salida = nombre_del_archivo + Derivaciones[j] + ".csv"
        df.to_csv(Datos_salida, index=False, mode='a')
        print(encabezado_X)

        # Generar y guardar gráfica de la señal
        plt.figure()
        plt.plot(X, Y)
        plt.savefig(Derivaciones[j] + '.png')

    # -------------------------------------------------------------------
    # Camino B: SVG "gordito" (método 1)
    # Las coordenadas NO están en orden cronológico → ordenar por X.
    # El ruido adicional se reduce con un promedio móvil.
    # -------------------------------------------------------------------
    if Es_gordito == True:

        # Ordenar los puntos por valor de X (eje temporal)
        indices_ordenados = sorted(range(len(X)), key=lambda i: X[i])
        X_ordenado = np.array([X[i] for i in indices_ordenados])
        Y_ordenado = np.array([Y[i] for i in indices_ordenados])

        # Suavizar la señal para reducir artefactos del reordenamiento
        window_size = 20
        Y_ordenado = promedio_movil(Y_ordenado, window_size)

        encabezado_X = Derivaciones[j] + ' X'
        encabezado_Y = Derivaciones[j] + ' Y'

        df = pd.DataFrame()
        df[encabezado_X] = X_ordenado
        df[encabezado_Y] = Y_ordenado

        Datos_salida = nombre_del_archivo + Derivaciones[j] + ".csv"
        df.to_csv(Datos_salida, index=False, mode='a')
        print(encabezado_X)

        plt.figure()
        plt.plot(X_ordenado, Y_ordenado)
        plt.savefig(Derivaciones[j] + '.png')


# ===========================================================================
# SECCIÓN 8: Tiempo total de ejecución
# ===========================================================================

Fin = time.time()
print(f"Tiempo total de ejecución: {Fin - inicio:.2f} segundos")
