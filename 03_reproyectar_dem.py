import processing
from pathlib import Path
from qgis.core import QgsProject, QgsRasterLayer
from qgis.utils import iface

# =========================================================================
# 1. RUTAS Y CONFIGURACIÓN DEL PROYECTO
# =========================================================================
variables = QgsProject.instance().customVariables()
ruta_base_str = variables.get('ruta_base_hidrologia', None)

if not ruta_base_str:
    RUTA_BASE = Path.home() / "Desktop" / "Proyecto_Hidrologico"
else:
    RUTA_BASE = Path(ruta_base_str)

DIR_BRUTOS = RUTA_BASE / "datos/brutos"
DIR_PROCESADOS = RUTA_BASE / "datos/procesados"
DIR_PROCESADOS.mkdir(parents=True, exist_ok=True)

# Archivos de entrada y salida estandarizados
dem_entrada_path = DIR_BRUTOS / "DEM_cuenca.tif"
dem_reproyectado_path = DIR_PROCESADOS / "DEM_UTM16N.tif"

CRS_DESTINO = "EPSG:32616"  # UTM Zona 16N (Metros)

print("==================================================================")
print("  REPROYECCIÓN AUTOMÁTICA DEL DEM A COORDENADAS PLANAS (METROS)  ")
print("==================================================================")

# =========================================================================
# 2. VALIDACIÓN DEL INSUMO TOPOGRÁFICO
# =========================================================================
if not dem_entrada_path.exists():
    print(f" [ERROR] No se encontró el archivo: {dem_entrada_path}")
    print("         Verifica que 'DEM_cuenca.tif' esté guardado en datos/brutos/")
    raise FileNotFoundError("Insumo DEM no localizado.")

print(f" [ENTRADA] Procesando raster: {dem_entrada_path.name}")

# =========================================================================
# 3. EJECUCIÓN DEL ALGORITMO GDAL WARP (REPROYECTAR)
# =========================================================================
# Resampling: 1 = Bilineal | Target Resolution: 30 metros
parametros_gdal = {
    'INPUT': str(dem_entrada_path),
    'SOURCE_CRS': None, 
    'TARGET_CRS': CRS_DESTINO,
    'RESAMPLING': 1,     
    'NODATA': None,
    'TARGET_RESOLUTION': 30, 
    'OPTIONS': '',
    'DATA_TYPE': 0,      
    'TARGET_EXTENT': None,
    'MULTITHREADING': True,
    'OUTPUT': str(dem_reproyectado_path)
}

print(" [PROCESANDO] Reproyectando datos angulares a metros (UTM 16N)...")

processing.run("gdal:warpreproject", parametros_gdal)

# =========================================================================
# 4. CARGA AL LIENZO Y ZOOM AUTOMÁTICO
# =========================================================================
capa_dem_utm = QgsRasterLayer(str(dem_reproyectado_path), "DEM Reproyectado (UTM 16N)")

if capa_dem_utm.isValid():
    QgsProject.instance().addMapLayer(capa_dem_utm)
    iface.mapCanvas().setExtent(capa_dem_utm.extent())
    iface.mapCanvas().refresh()
    print("------------------------------------------------------------------")
    print(f" [ÉXITO] DEM reproyectado a UTM 16N en formato raster continuo:")
    print(f"         {dem_reproyectado_path}")
    print("------------------------------------------------------------------")
else:
    print(" [ERROR] El archivo se creó en disco pero no pudo visualizarse en QGIS.")