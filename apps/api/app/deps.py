from fastapi import Depends

from app.config import Settings, get_settings
from app.creem_client import CreemClient
from app.repo import Repo, SupabaseRepo


def get_repo(settings: Settings = Depends(get_settings)) -> Repo:
    return SupabaseRepo(settings)


def get_creem_client(settings: Settings = Depends(get_settings)) -> CreemClient:
    return CreemClient(api_key=settings.creem_api_key, base_url=settings.creem_api_base)
