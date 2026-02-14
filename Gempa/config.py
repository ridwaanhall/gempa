from decouple import config

# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# BMKG API base
BMKG_API_BASE = config('BMKG_API')

BMKG_ALERT_URL = config('BMKG_ALERT_URL', default=f"{BMKG_API_BASE}/datagempa.json")
BMKG_CATALOG_URL = config('BMKG_CATALOG_URL', default=f"{BMKG_API_BASE}/katalog_gempa.json")
BMKG_REALTIME_URL = config('BMKG_REALTIME_URL', default=f"{BMKG_API_BASE}/live30event.xml")
BMKG_TSUNAMI_URL = config('BMKG_TSUNAMI_URL', default=f"{BMKG_API_BASE}/last30tsunamievent.xml")
BMKG_FELT_URL = config('BMKG_FELT_URL', default=f"{BMKG_API_BASE}/last30feltevent.xml")
BMKG_M5_URL = config('BMKG_M5_URL', default=f"{BMKG_API_BASE}/last30event.xml")
BMKG_MON3_URL = config('BMKG_MON3_URL', default=f"{BMKG_API_BASE}/3mgempaQL.json")
BMKG_YR5_URL = config('BMKG_YR5_URL', default=f"{BMKG_API_BASE}/histori.json")
BMKG_SEISMIC_URL = config('BMKG_SEISMIC_URL', default=f"{BMKG_API_BASE}/sensor_seismic.json")
BMKG_GLOBAL_URL = config('BMKG_GLOBAL_URL', default=f"{BMKG_API_BASE}/sensor_global.json")
BMKG_FAULTS_GLOBAL_URL = config('BMKG_FAULTS_GLOBAL_URL', default=f"{BMKG_API_BASE}/fault_indo_world.geojson")
BMKG_FAULTS_INDO_URL = config('BMKG_FAULTS_INDO_URL', default=f"{BMKG_API_BASE}/indo_faults_lines.geojson")
BMKG_HISTORY_URL_TEMPLATE = config('BMKG_HISTORY_URL_TEMPLATE', default=f"{BMKG_API_BASE}/history.{{eventid}}.txt")

# Allowed hosts
if DEBUG:
    ALLOWED_HOSTS = []
else:
    ALLOWED_HOSTS = [
        '.vercel.app',
        '.rone.dev',
    ]
