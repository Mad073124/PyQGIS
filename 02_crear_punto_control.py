import os
from pathlib import Path
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsVectorFileWriter,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform
)
from qgis.utils import iface
from PyQt5.QtWidgets import QInputDialog

# =========================================================================
# 1. RUTA BASE Y CARPETA DE DESTINO AUTOMÁTICA
# =========================================================================
variables = QgsProject.instance().customVariables()
ruta_base_str = variables.get('ruta_base_hidrologia', None)

if not ruta_base_str:
    RUTA_BASE = Path.home() / "Desktop" / "Proyecto_Hidrologico"
else:
    RUTA_BASE = Path(ruta_base_str)

DIR_BRUTOS = RUTA_BASE / "datos/brutos"
RUTA_SALIDA_SHP = DIR_BRUTOS / "Punto_Control_Salida.shp"

# Asegurar existencia de la carpeta
DIR_BRUTOS.mkdir(parents=True, exist_ok=True)

# Definición de Sistemas de Coordenadas
crs_utm = QgsCoordinateReferenceSystem("EPSG:32616")  # UTM 16N
crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326") # WGS84 (Google Maps)

QgsProject.instance().setCrs(crs_utm)

print("==================================================================")
print("  GENERACIÓN INTERACTIVA Y AUTOMÁTICA DEL PUNTO DE CONTROL  ")
print("==================================================================")

# =========================================================================
# 2. CAPTURA INTERACTIVA VÍA VENTANAS EMERGENTES (QInputDialog)
# =========================================================================
lat_str, ok_lat = QInputDialog.getText(
    None, 
    "Punto de Control", 
    "Ingresa la Latitud de Google Maps (ejemplo: 12.13642):"
)

if not ok_lat or not lat_str.strip():
    print(" [CANCELADO] Entrada de coordenadas cancelada.")
    raise SystemExit

lon_str, ok_lon = QInputDialog.getText(
    None, 
    "Punto de Control", 
    "Ingresa la Longitud de Google Maps (ejemplo: -85.80779):"
)

if not ok_lon or not lon_str.strip():
    print(" [CANCELADO] Entrada de coordenadas cancelada.")
    raise SystemExit

try:
    lat = float(lat_str.strip())
    lon = float(lon_str.strip())
    
    # Auto-corrección si faltó el punto decimal
    if abs(lon) > 180:
        lon = lon / 100000.0
        print(f" [AVISO] Longitud ajustada a: {lon}")
        
    if abs(lat) > 90:
        lat = lat / 100000.0
        print(f" [AVISO] Latitud ajustada a: {lat}")

except ValueError:
    print("\n [ERROR] Ingresa valores numéricos válidos.")
    raise

# =========================================================================
# 3. REPROYECCIÓN A UTM ZONA 16N
# =========================================================================
transformador = QgsCoordinateTransform(crs_wgs84, crs_utm, QgsProject.instance())
punto_utm = transformador.transform(QgsPointXY(lon, lat))

print(f"\n [TRANSFORMACIÓN] WGS84 ({lat}, {lon}) -> UTM 16N: X={punto_utm.x():.2f} m, Y={punto_utm.y():.2f} m")

# =========================================================================
# 4. CREACIÓN, EXPORTACIÓN Y DESPLIEGUE EN EL LIENZO
# =========================================================================
capa_punto_mem = QgsVectorLayer("Point?crs=EPSG:32616", "Punto_Control_Salida", "memory")
pr = capa_punto_mem.dataProvider()

feature = QgsFeature()
feature.setGeometry(QgsGeometry.fromPointXY(punto_utm))
pr.addFeatures([feature])
capa_punto_mem.updateExtents()

# Limpiar capas con el mismo nombre en la leyenda antes de agregar
capas_previas = QgsProject.instance().mapLayersByName("Punto de Control (Salida)")
for capa in capas_previas:
    QgsProject.instance().removeMapLayer(capa.id())

# Guardar en disco duro
opciones = QgsVectorFileWriter.SaveVectorOptions()
opciones.driverName = "ESRI Shapefile"
opciones.fileEncoding = "UTF-8"

QgsVectorFileWriter.writeAsVectorFormatV3(
    capa_punto_mem,
    str(RUTA_SALIDA_SHP),
    QgsProject.instance().transformContext(),
    opciones
)

# Cargar directamente desde el archivo guardado
capa_final = QgsVectorLayer(str(RUTA_SALIDA_SHP), "Punto de Control (Salida)", "ogr")

if capa_final.isValid():
    QgsProject.instance().addMapLayer(capa_final)
    iface.mapCanvas().setExtent(capa_final.extent())
    iface.mapCanvas().refresh()
    print("------------------------------------------------------------------")
    print(f" [ÉXITO] Shapefile generado y cargado correctamente en:")
    print(f"         {RUTA_SALIDA_SHP}")
    print("------------------------------------------------------------------")
else:
    # Alternativa de respaldo directo desde la memoria si el sistema operativo bloquea el archivo
    QgsProject.instance().addMapLayer(capa_punto_mem)
    print("------------------------------------------------------------------")
    print(f" [AVISO] Se cargó el punto desde memoria. Shapefile guardado en:")
    print(f"         {RUTA_SALIDA_SHP}")
    print("------------------------------------------------------------------")