from datetime import datetime

from .database import get_db_connection


# Функция для получения топ 100 репозиториев
async def get_top_100_repos(order_by: str = 'stars'):
    query = f'''
        SELECT repo, owner, position_cur, position_prev, stars, watchers, forks, open_issues, language
        FROM repositories
        ORDER BY {order_by} DESC
        LIMIT 100;
    '''
    conn = await get_db_connection()
    rows = await conn.fetch(query)
    await conn.close()
    return rows


# Функция для получения активности репозитория
async def get_repo_activity(owner: str, repo: str, since: str, until: str):
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

    conn = await get_db_connection()
    rows = await conn.fetch(query, owner, repo, since_date, until_date)
    await conn.close()
    return rows
