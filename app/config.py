import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseModel):
    slack_token: Optional[str] = os.getenv("SLACK_TOKEN")
    self_slack_user_id: Optional[str] = os.getenv("SELF_SLACK_USER_ID")

    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")

    linear_api_key: Optional[str] = os.getenv("LINEAR_API_KEY")
    linear_team_id: Optional[str] = os.getenv("LINEAR_TEAM_ID")

    github_token: Optional[str] = os.getenv("GITHUB_TOKEN")

    state_file_path: Path = Path(
        os.getenv("STATE_FILE_PATH", "./app/jobs/workflows/ingestion/state.json")
    ).resolve()
    db_file_path: Path = Path(os.getenv("DB_FILE_PATH", "./data/messages.db")).resolve()

    daily_notification_hour: int = int(os.getenv("DAILY_NOTIFICATION_HOUR", "9"))
    timezone: str = os.getenv("TIMEZONE", "UTC")


settings = Settings()

# Ensure directories exist
settings.state_file_path.parent.mkdir(parents=True, exist_ok=True)
settings.db_file_path.parent.mkdir(parents=True, exist_ok=True)
