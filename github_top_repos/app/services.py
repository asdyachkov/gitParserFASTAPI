from .repositories import get_top_100_repos, get_repo_activity


# Бизнес-логика для получения топа репозиториев
async def fetch_top_100_repos(order_by: str):
    return await get_top_100_repos(order_by)


# Бизнес-логика для получения активности репозитория
async def fetch_repo_activity(owner: str, repo: str, since: str, until: str):
    return await get_repo_activity(owner, repo, since, until)
