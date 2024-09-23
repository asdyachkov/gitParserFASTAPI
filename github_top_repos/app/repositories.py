from datetime import datetime

from fastapi import Depends

from .database import get_db_connection


# Функция для получения топ 100 репозиториев
async def get_top_100_repos(order_by: str = 'stars', db_connection: Depends = Depends(get_db_connection)):
    query = f'''
        SELECT repo, owner, position_cur, position_prev, stars, watchers, forks, open_issues, language
        FROM repositories
        ORDER BY {order_by} DESC
        LIMIT 100;
    '''
    async with db_connection as conn:
        rows = await conn.fetch(query)
    return rows


# Функция для получения активности репозитория
async def get_repo_activity(owner: str, repo: str, since: str, until: str,
                            db_connection: Depends = Depends(get_db_connection)):
    query = '''
        SELECT a.date, a.commits, a.authors
        FROM activity a
        JOIN repositories r ON a.repo = r.repo
        WHERE r.owner = $1
        AND a.repo = $2
        AND a.date BETWEEN $3 AND $4
        ORDER BY a.date;
    '''

    # Преобразуем строки в формат, который принимает PostgreSQL
    since_date = datetime.strptime(since, "%Y-%m-%d").date()
    until_date = datetime.strptime(until, "%Y-%m-%d").date()

    async with db_connection as conn:
        rows = await conn.fetch(query, owner, repo, since_date, until_date)
    return rows
