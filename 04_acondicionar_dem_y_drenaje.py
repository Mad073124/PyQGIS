import os
import processing
from pathlib import Path
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsRasterBandStats,
    QgsColorRampShader,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer
)
from qgis.utils import iface
from PyQt5.QtGui import QColor

# =========================================================================
# 1. RUTAS DEL PROYECTO
# =========================================================================
variables = QgsProject.instance().customVariables()
ruta_base_str = variables.get('ruta_base_hidrologia', None)

if not ruta_base_str:
    RUTA_BASE = Path.home() / "Desktop" / "Proyecto_Hidrologico"
else:
    RUTA_BASE = Path(ruta_base_str)

DIR_PROCESADOS = RUTA_BASE / "datos/procesados"
DIR_BRUTOS = RUTA_BASE / "datos/brutos"

dem_input = DIR_PROCESADOS / "DEM_UTM16N.tif"
channel_raster = DIR_PROCESADOS / "channel_raster.tif"
flow_dir_path = DIR_PROCESADOS / "Flow_Direction.tif"
channel_vector = DIR_PROCESADOS / "red_drenaje.shp"
punto_control_path = DIR_BRUTOS / "Punto_Control_Salida.shp"

print("==================================================================")
print("   EXTRACCIÓN DE CAUCES Y DIRECCIÓN DE FLUJO                      ")
print("==================================================================")

if not dem_input.exists():
    raise FileNotFoundError(f"No se encontró el DEM en: {dem_input}")

# =========================================================================
# 2. PROCESAMIENTO CON SAGA / GRASS
# =========================================================================
print("\n [1] Generando Red de Cauces y Dirección de Flujo...")

try:
    # Genera los cauces y la dirección de flujo en un solo paso
    processing.run(
        "saga:catchmentarea",
        {
            "ELEVATION": str(dem_input),
            "FLOW": str(flow_dir_path),
            "VAL_INPUT": str(channel_raster),
            "METHOD": 0,
        }
    )
    print("     Procesado con SAGA.")
except Exception:
    # Alternativa si SAGA falla: usar GRASS r.watershed
    processing.run(
        "grass7:r.watershed",
        {
            "elevation": str(dem_input),
            "threshold": 200,
            "drainage": str(flow_dir_path),
            "stream": str(channel_raster),
        }
    )
    print("     Procesado con GRASS.")

# =========================================================================
# 3. ESTILO DE CAUCES
# =========================================================================
if channel_raster.exists():
    for l in QgsProject.instance().mapLayersByName("Cauces (Red de Drenaje)"):
        QgsProject.instance().removeMapLayer(l.id())

    raster_layer = QgsRasterLayer(str(channel_raster), "Cauces (Red de Drenaje)")
    if raster_layer.isValid():
        provider = raster_layer.dataProvider()
        stats = provider.bandStatistics(1, QgsRasterBandStats.All, raster_layer.extent(), 0)
        max_val = max(stats.maximumValue, 1) if stats.maximumValue is not None else 1

        shader = QgsColorRampShader()
        shader.setColorRampType(QgsColorRampShader.Interpolated)
        lst = [
            QgsColorRampShader.ColorRampItem(0, QColor(0, 0, 0, 0), "Sin cauce"),
            QgsColorRampShader.ColorRampItem(0.1, QColor(0, 120, 255, 255), "Cauce secundario"),
            QgsColorRampShader.ColorRampItem(max_val, QColor(0, 0, 255, 255), "Cauce principal")
        ]
        shader.setColorRampItemList(lst)
        raster_shader = QgsRasterShader()
        raster_shader.setRasterShaderFunction(shader)
        renderer = QgsSingleBandPseudoColorRenderer(provider, 1, raster_shader)
        raster_layer.setRenderer(renderer)

        QgsProject.instance().addMapLayer(raster_layer)
        raster_layer.triggerRepaint()
        print(" [ÉXITO] Cauces cargados y 'Flow_Direction.tif' creado exitosamente.")