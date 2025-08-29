import os
from dotenv import load_dotenv

SECRET_KEY = os.environ.get("SECRET_KEY", "supersecret")

DB_ENGINE = os.environ.get("DB_ENGINE", "mysql")
#Load environment variable

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD","Shivam@2607"),
    "database": os.environ.get("DB_NAME", "bgb_bank"),
    "port": int(os.environ.get("DB_PORT", 3306))
}

#Gateways
GATEWAY_MODE = os.environ.get("GATEWAY_MODE", "SIMULATOR")
SIMULATOR_URL = os.environ.get("SIMULATOR_URL", "http://localhost:6000")
