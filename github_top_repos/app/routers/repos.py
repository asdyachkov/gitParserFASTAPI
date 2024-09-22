from fastapi import APIRouter, Query
from typing import Optional
from ..services import fetch_top_100_repos, fetch_repo_activity

router = APIRouter()


@router.get("/top100")
async def get_top_100_repos(order_by: Optional[str] = Query("stars")):
    """Возвращает топ 100 репозиториев по количеству звезд или другим параметрам."""
    repos = await fetch_top_100_repos(order_by)
    return {"repos": repos}


@router.get("/{owner}/{repo}/activity")
async def get_repo_activity(
        owner: str,
        repo: str,
        since: str,
        until: str
):
    """Возвращает активность по коммитам за выбранный промежуток времени."""
    activity = await fetch_repo_activity(owner, repo, since, until)
    return {"activity": activity}
