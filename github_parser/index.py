import os
import aiohttp
import asyncpg
from typing import List, Dict, Any, Tuple
from datetime import datetime, date


# Подключение к базе данных
async def connect_db() -> asyncpg.Connection:
    """Устанавливает асинхронное соединение с базой данных PostgreSQL."""
    try:
        connection = await asyncpg.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return connection
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        raise


# Получаем топ-100 репозиториев с GitHub
async def get_top_repos() -> List[Dict[str, Any]]:
    """Получает топ-100 репозиториев из GitHub по количеству звезд."""
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "stars:>1",
        "sort": "stars",
        "order": "desc",
        "per_page": 100
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            return data['items']


# Получаем дату последней активности для репозитория
async def get_last_activity_date(conn: asyncpg.Connection, repo: str) -> str:
    """Получает последнюю дату активности для репозитория."""
    result = await conn.fetchval("""
        SELECT MAX(date)
        FROM activity
        WHERE repo = $1
    """, repo)
    return result or '1970-01-01'  # Возвращаем минимальную дату, если записей нет


# Получаем активность репозитория по коммитам
async def fetch_activity(owner: str, repo: str, since: str) -> List[Dict[str, Any]]:
    """Получает активность коммитов репозитория с заданной даты из GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {
        "since": since,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()


# Обновляем информацию о репозиториях и их активности в базе данных
async def update_repositories_and_activity(repos: List[Dict[str, Any]]) -> None:
    """Обновляет данные о репозиториях и их активности в базе данных."""
    conn = await connect_db()

    # Очищаем таблицу перед новым импортом
    await conn.execute('TRUNCATE TABLE repositories')

    # Вставляем данные о репозиториях
    repo_inserts = []
    activity_inserts = []

    for repo in repos:
        # Вставляем данные о репозиториях
        repo_inserts.append((
            repo['full_name'].replace('/', '-'), repo['owner']['login'], repos.index(repo) + 1,
            repo['stargazers_count'],
            repo['watchers_count'], repo['forks_count'], repo['open_issues_count'], repo['language']
        ))

    # Выполняем вставку репозиториев за один раз
    await conn.executemany("""
        INSERT INTO repositories (repo, owner, position_cur, stars, watchers, forks, open_issues, language)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (repo) DO UPDATE 
        SET position_prev = repositories.position_cur,
            position_cur = EXCLUDED.position_cur,
            stars = EXCLUDED.stars,
            watchers = EXCLUDED.watchers,
            forks = EXCLUDED.forks,
            open_issues = EXCLUDED.open_issues,
            language = EXCLUDED.language
    """, repo_inserts)

    # Получаем активность для каждого репозитория
    for repo in repos:
        last_date = await get_last_activity_date(conn, repo['full_name'])

        # Если last_date строка, используем её напрямую, если это дата, преобразуем в строку
        if isinstance(last_date, date):
            last_date_str = last_date.strftime("%Y-%m-%d")
        else:
            last_date_str = last_date  # уже строка

        activity_data = await fetch_activity(repo['owner']['login'], repo['name'], last_date_str)

        # Обрабатываем и сохраняем данные активности
        activity_by_day = {}
        for commit in activity_data:
            commit_date = commit['commit']['author']['date'][:10]  # дата коммита
            author = commit['commit']['author']['name']
            if commit_date not in activity_by_day:
                activity_by_day[commit_date] = {"commits": 0, "authors": set()}

            activity_by_day[commit_date]["commits"] += 1
            activity_by_day[commit_date]["authors"].add(author)

        # Формируем данные для вставки активности
        for date_str, data in activity_by_day.items():
            # Преобразуем строку даты в объект date
            activity_inserts.append((
                datetime.strptime(date_str, "%Y-%m-%d").date(),  # Преобразование строки в объект date
                data["commits"],
                list(data["authors"]),
                repo['full_name'].replace('/', '-')
            ))

    # Вставка данных за один запрос с обновлением при конфликте по уникальному ключу
    await conn.executemany("""
        INSERT INTO activity (date, commits, authors, repo)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (date, repo) DO UPDATE
        SET commits = EXCLUDED.commits,
            authors = EXCLUDED.authors
    """, activity_inserts)

    await conn.close()


# Основная функция для Яндекс.Облака
async def handler(event, context) -> dict:
    """Основная функция, вызываемая в Яндекс.Облаке."""
    repos = await get_top_repos()
    await update_repositories_and_activity(repos)
    return {"status": "success"}

# if __name__ == "__main__":
#     asyncio.run(handler(None, None))
