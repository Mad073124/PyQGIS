import processing
from pathlib import Path
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsSymbol,
    QgsSimpleFillSymbolLayer,
    QgsSingleSymbolRenderer
)
from qgis.utils import iface
from PyQt5.QtGui import QColor

# =========================================================================
# 1. ESTÁNDAR Y RUTAS DEL PROYECTO
# =========================================================================
variables = QgsProject.instance().customVariables()
ruta_base_str = variables.get('ruta_base_hidrologia', None)

if not ruta_base_str:
    RUTA_BASE = Path.home() / "Desktop" / "Proyecto_Hidrologico"
else:
    RUTA_BASE = Path(ruta_base_str)

DIR_PROCESADOS = RUTA_BASE / "datos/procesados"
DIR_BRUTOS = RUTA_BASE / "datos/brutos"

flow_dir_path = DIR_PROCESADOS / "Flow_Direction.tif"
punto_control_path = DIR_BRUTOS / "Punto_Control_Salida.shp"
cuenca_raster_path = DIR_PROCESADOS / "Cuenca_Raster.tif"
cuenca_vector_path = DIR_PROCESADOS / "Cuenca_Delimitada.shp"

print("==================================================================")
print("     DELIMITACIÓN AUTOMÁTICA DE LA CUENCA HIDROGRÁFICA (GRASS)    ")
print("==================================================================")

# =========================================================================
# 2. VALIDACIÓN Y EXTRACCIÓN DE COORDENADAS DEL EXUTORIO
# =========================================================================
if not flow_dir_path.exists():
    print(f" [ERROR] No existe la dirección de flujo en: {flow_dir_path}")
    raise FileNotFoundError("Ejecuta primero el script de red de drenaje.")

if not punto_control_path.exists():
    print(f" [ERROR] No existe el exutorio en: {punto_control_path}")
    raise FileNotFoundError("Insumo de punto de control ausente.")

capa_punto = QgsVectorLayer(str(punto_control_path), "Punto_Control", "ogr")
if not capa_punto.isValid() or capa_punto.featureCount() == 0:
    raise ValueError("La capa del punto de control está vacía o es inválida.")

# Obtener las coordenadas exactas X, Y en metros (UTM 16N)
f = next(capa_punto.getFeatures())
geom = f.geometry().asPoint()
coord_x, coord_y = geom.x(), geom.y()

print(f" [ENTRADA] Coordenadas del exutorio: X={coord_x:.2f}, Y={coord_y:.2f}")

# =========================================================================
# 3. PROCESAMIENTO HIDROLÓGICO Y POLIGONIZACIÓN
# =========================================================================
print(" [PROCESANDO] Trazando cuenca vertiente con GRASS (r.water.outlet)...")

# 3.1 Delimitación en formato Raster
processing.run("grass:r.water.outlet", {
    'input': str(flow_dir_path),
    'coordinates': f"{coord_x},{coord_y}",
    'output': str(cuenca_raster_path),
    'GRASS_REGION_PARAMETER': None,
    'GRASS_REGION_CELLSIZE_PARAMETER': 0
})

# 3.2 Conversión a formato Vectorial (SHP)
print(" [PROCESANDO] Poligonizando máscara raster a capa vectorial...")
processing.run("gdal:polygonize", {
    'INPUT': str(cuenca_raster_path),
    'BAND': 1,
    'FIELD': 'DN',
    'EIGHT_CONNECTEDNESS': False,
    'OUTPUT': str(cuenca_vector_path)
})

# =========================================================================
# 4. CARGA Y SIMBOLOGÍA EN EL LIENZO DE QGIS
# =========================================================================
if cuenca_vector_path.exists():
    # Remover versiones previas de la capa en la tabla de contenidos
    for l in QgsProject.instance().mapLayersByName("Cuenca Delimitada"):
        QgsProject.instance().removeMapLayer(l.id())

    capa_cuenca = QgsVectorLayer(str(cuenca_vector_path), "Cuenca Delimitada", "ogr")

    if capa_cuenca.isValid():
        # Aplicar estilo profesional: borde rojo de 0.8mm y relleno transparente
        simbolo = QgsSymbol.defaultSymbol(capa_cuenca.geometryType())
        capa_linea = QgsSimpleFillSymbolLayer.create({
            'outline_color': '255,0,0,255',
            'outline_width': '0.8',
            'color': '255,0,0,40'
        })
        simbolo.changeSymbolLayer(0, capa_linea)
        capa_cuenca.setRenderer(QgsSingleSymbolRenderer(simbolo))

        QgsProject.instance().addMapLayer(capa_cuenca)
        
        if iface and iface.mapCanvas():
            iface.mapCanvas().setExtent(capa_cuenca.extent())
            iface.mapCanvas().refresh()

        print("------------------------------------------------------------------")
        print(" [ÉXITO] Polígono de la cuenca delimitado y renderizado.")
        print(f"         Guardado en: {cuenca_vector_path}")
        print("------------------------------------------------------------------")
    else:
        print(" [ERROR] El shapefile generado no es válido.")
else:
    print(" [ERROR] Ocurrió un fallo en la generación del vector de cuenca.")