# Lector de ECG desde PDF

Herramienta para extraer las señales de un electrocardiograma (ECG) a partir de un archivo PDF, convirtiéndolas en datos numéricos (CSV) y gráficas (PNG).

---

## ¿Qué hace?

1. **Convierte** el PDF del ECG a formato SVG.
2. **Parsea** el SVG para localizar automáticamente las 12 derivaciones.
3. **Extrae** las coordenadas (X, Y) de cada señal.
4. **Exporta** los datos a archivos CSV y genera gráficas PNG de cada derivación.

---

## Requisitos

### Python
Versión recomendada: **Python 3.8+**

### Dependencias

Instalar con pip:

```bash
pip install spire.pdf svgwrite matplotlib numpy svgpathtools lxml pandas
```

| Librería        | Uso                                          |
|-----------------|----------------------------------------------|
| `spire.pdf`     | Conversión PDF → SVG                         |
| `lxml`          | Parseo del archivo SVG                       |
| `numpy`         | Manejo de arrays numéricos                   |
| `pandas`        | Exportación de datos a CSV                   |
| `matplotlib`    | Generación de gráficas PNG                   |
| `svgpathtools`  | Herramientas auxiliares para rutas SVG       |
| `svgwrite`      | Escritura de SVG (importado, uso futuro)     |

---

## Estructura del proyecto

```
Lector_ECG/
│
├── lector_ecg.py          # Script principal
├── ECG_TEST_8.pdf         # Archivo de entrada (PDF del ECG)
│
└── ECG_TEST_8/            # Carpeta de salida (creada automáticamente)
    ├── I.csv              # Datos de la derivación I
    ├── I.png              # Gráfica de la derivación I
    ├── II.csv
    ├── II.png
    ├── ...                # (una por cada derivación detectada)
    └── V6.csv
```

---

## Uso

1. Coloca el archivo PDF del ECG en el directorio de trabajo.
2. Edita la variable `nombre_del_archivo` en el script:

```python
nombre_del_archivo = 'ECG_TEST_8'  # Sin extensión .pdf
```

3. Ejecuta el script:

```bash
python lector_ecg.py
```

4. Los resultados aparecerán en una subcarpeta con el mismo nombre que el archivo.

---

## Modos de procesamiento

El script detecta automáticamente el formato del ECG según el tamaño del SVG generado:

| Condición              | Modo        | Descripción                                                                 |
|------------------------|-------------|-----------------------------------------------------------------------------|
| SVG < 600 KB           | **Estándar** | Coordenadas en orden cronológico. Derivaciones en Unicode estándar.        |
| SVG > 600 KB (gordito) | **Gordito**  | Coordenadas desordenadas → se ordenan por X y se aplica promedio móvil.   |

> El modo "gordito" corresponde a ECGs generados por equipos modelo **3312** u otros que producen SVGs de mayor tamaño.

---

## Derivaciones soportadas

| Derivación | Código Unicode interno |
|------------|------------------------|
| I          | `#57417;`              |
| II         | `#57417;&#57417;`      |
| III        | `#57417;&#57417;&#57417;` |
| aVR        | `#57441;&#57430;&#57426;` |
| aVL        | `#57441;&#57430;&#57420;` |
| aVF        | `#57441;&#57430;&#57414;` |
| V1 – V6   | `#57430;` + sufijo     |

Si una derivación aparece dos veces (tira larga), la segunda se guarda con el sufijo `_L` (e.g., `II_L`).

---

## Formato de salida CSV

Cada archivo CSV contiene dos columnas:

```
I X, I Y
123.45, 67.89
...
```

Donde `X` representa la posición horizontal (tiempo relativo) e `Y` la amplitud de la señal.

---

## Notas

- El script crea la carpeta de salida automáticamente. Si ya existe, lanzará un error. Elimina o renombra la carpeta antes de volver a ejecutar.
- Las gráficas PNG se generan con los ejes en coordenadas SVG (Y puede estar invertido respecto a la visualización clínica habitual).
- El suavizado por promedio móvil en modo gordito usa una ventana de **20 muestras** (configurable en el código).
