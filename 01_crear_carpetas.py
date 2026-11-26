import os
from pathlib import Path
from qgis.core import QgsProject

# =========================================================================
# 1. CONFIGURACIÓN GENÉRICA DEL PROYECTO
# =========================================================================
NOMBRE_PROYECTO = "Proyecto_Hidrologico"

# Ruta dinámica al Escritorio de cualquier usuario (Windows/Mac/Linux)
RUTA_BASE = Path.home() / "Desktop" / NOMBRE_PROYECTO

# =========================================================================
# 2. ARQUITECTURA DE CARPETAS EN ESPAÑOL
# =========================================================================
carpetas_proyecto = [
    "datos/brutos",          # MDE GeoTIFF original, Shapefiles INETER, CSVs
    "datos/procesados",      # MDE reproyectado, Fill Sinks, cuenca delimitada, CN
    "datos/resultados",      # Mapas finales, tablas morfométricas, hidrogramas
    "codigos",               # Scripts de Python para automatización
    "documentos",            # Memorias de cálculo, reportes y documentación
    "modelos_hec/hms",       # Archivos de exportación y proyectos HEC-HMS
    "modelos_hec/ras"        # Archivos de exportación y proyectos HEC-RAS
]

# =========================================================================
# 3. CREACIÓN AUTOMÁTICA DE DIRECTORIOS
# =========================================================================
print(f"--- INICIANDO CREACIÓN DE ENTORNO: [{NOMBRE_PROYECTO}] ---")

for subcarpeta in carpetas_proyecto:
    ruta_dir = RUTA_BASE / subcarpeta
    ruta_dir.mkdir(parents=True, exist_ok=True)
    print(f" Carpeta creada/verificada: {subcarpeta}")

# =========================================================================
# 4. REGISTRO DE VARIABLES GLOBALES EN EL PROYECTO QGIS
# =========================================================================
variables = QgsProject.instance().customVariables()
variables['ruta_base_hidrologia'] = str(RUTA_BASE)
variables['nombre_proyecto_hidrologia'] = NOMBRE_PROYECTO
QgsProject.instance().setCustomVariables(variables)

print("\n ¡Entorno de trabajo creado con éxito!")
print(f" Ruta principal registrada en QGIS: {RUTA_BASE}")
