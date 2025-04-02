import requests

from fastapi import HTTPException

from config import settings


class AuthClient:
    def __init__(self, url):
        self.url = url

    def validate_token(self, token):
        result = requests.get(
            f'{self.url}/check_token',
            headers={'Authorization': f'Bearer {token}'}
        )
        if result.status_code != 200:
            raise HTTPException(status_code=405, detail="Method not allowed")
        return None

    def validate_token_admin(self, token):
        result = requests.get(
            f'{self.url}/check_token_admin',
            headers={'Authorization': f'Bearer {token}'}
        )
        if result.status_code != 200:
            raise HTTPException(status_code=405, detail="Method not allowed")
        return None


def get_auth_client():
    yield AuthClient(settings.AUTH_CLIENT_URL)
