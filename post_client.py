import requests

from fastapi import HTTPException

from config import settings


class PostClient:
    def __init__(self, url):
        self.url = url

    async def get_posts(self, token, user_id):
        result = requests.get(
            f'{self.url}/posts/user/{user_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        if result.status_code != 200:
            raise HTTPException(status_code=405, detail="Method not allowed")
        return result.json()


def get_post_client():
    yield PostClient(settings.POST_CLIENT_URL)
