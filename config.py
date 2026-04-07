import tomllib
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.toml"

with open(CONFIG_PATH, "rb") as f:
    _config = tomllib.load(f)

# App
APP_HOST = _config["app"]["host"]
APP_PORT = _config["app"]["port"]

# Tokens
TOKENS = _config["tokens"]

# Schedule
S3_RELOAD_AFTER = _config["schedule"]["s3_reload_after"]
REALTIME_RELOAD_AFTER = _config["schedule"]["realtime_reload_after"]

# Email
SMTP_HOST = _config["email"]["smtp_host"]
SMTP_PORT = _config["email"]["smtp_port"]
FROM_ADDRESS = _config["email"]["from_address"]
EMAIL_SUBJECTS = _config["email"]["subjects"]
EMAIL_RECIPIENTS = _config["email"]["recipients"]

# Setup
SETUP_PASSWORD = _config["setup"]["password"]

# Output
PORTFOLIO_METRICS_PATH = Path(_config["output"]["portfolio_metrics_path"])
