from datetime import datetime

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from ..services import fetch_top_100_repos, fetch_repo_activity

router = APIRouter()


@router.get("/top100")
async def get_top_100_repos(order_by: Optional[str] = Query("stars")):
    """Возвращает топ 100 репозиториев по количеству звезд или другим параметрам."""

    order_by = order_by if order_by in ['repo', 'owner', 'position_cur', 'position_prev', 'stars', 'watchers', 'forks',
                                        'open_issues', 'language'] else 'stars'

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

    # Задаем максимальные и минимальные длины для owner и repo
    MIN_LENGTH = 1
    MAX_LENGTH_OWNER = 39  # Максимальная длина имени пользователя GitHub
    MAX_LENGTH_REPO = 100  # Максимальная длина имени репозитория GitHub

    # Проверка длины owner
    if not (MIN_LENGTH <= len(owner) <= MAX_LENGTH_OWNER):
        raise HTTPException(status_code=400, detail="Длина имени пользователя GitHub должна быть от 1 до 39 символов.")

    # Проверка длины repo
    if not (MIN_LENGTH <= len(repo) <= MAX_LENGTH_REPO):
        raise HTTPException(status_code=400, detail="Длина имени репозитория GitHub должна быть от 1 до 100 символов.")

    # Проверка разрешенных символов в owner и repo
    if not owner.replace('-', '').replace('_', '').isalnum():
        raise HTTPException(status_code=400, detail="Неверное имя пользователя GitHub.")
    if not repo.replace('-', '').isalnum():
        raise HTTPException(status_code=400, detail="Неверное имя репозитория GitHub.")

    # Проверка формата дат
    try:
        since_date = datetime.strptime(since, '%Y-%m-%d')
        until_date = datetime.strptime(until, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Ожидается YYYY-MM-DD.")

    # Дополнительная проверка: дата 'since' должна быть раньше даты 'until'
    if since_date > until_date:
        raise HTTPException(status_code=400, detail="Дата 'since' должна быть раньше даты 'until'.")

    activity = await fetch_repo_activity(owner, repo, since, until)
    return {"activity": activity}
