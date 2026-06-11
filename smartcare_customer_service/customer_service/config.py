from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
EVALUATION_DIR = DATA_DIR / "evaluation"
RUNTIME_DIR = BASE_DIR / "runtime"
STATIC_DIR = BASE_DIR / "static"
REPORTS_DIR = BASE_DIR / "reports"

DEFAULT_DB_PATH = RUNTIME_DIR / "chat_history.db"
DEFAULT_ORDER_PATH = DATA_DIR / "orders.json"
