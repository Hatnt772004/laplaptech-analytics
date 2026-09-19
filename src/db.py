import os
import hashlib
import pandas as pd
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CH_HOST"),
        port=int(os.getenv("CH_PORT")),
        username=os.getenv("CH_USERNAME"),
        password=os.getenv("CH_PASSWORD"),
        database=os.getenv("CH_DATABASE"),
    )

def query_cached(sql: str, cache_dir: str = "data/raw", force_refresh: bool = False) -> pd.DataFrame:
    """Chạy query, cache kết quả ra CSV theo hash của câu SQL để tránh query lại DB mỗi lần chạy notebook."""
    os.makedirs(cache_dir, exist_ok=True)
    key = hashlib.md5(sql.encode()).hexdigest()[:10]
    path = os.path.join(cache_dir, f"query_{key}.csv")

    if os.path.exists(path) and not force_refresh:
        return pd.read_csv(path)

    client = get_client()
    df = client.query_df(sql)
    df.to_csv(path, index=False)
    return df

def get_schema(database: str = "laplaptech", cache_dir: str = "../data/raw") -> pd.DataFrame:
    sql = f"""
        SELECT table, name AS column_name, type AS data_type
        FROM system.columns
        WHERE database = '{database}'
          AND table NOT LIKE '%dbt_exchange%'
        ORDER BY table, name
    """
    return query_cached(sql, cache_dir=cache_dir)

def append_note(text: str, path: str = "../docs/project_notes.md") -> None:
    """Ghi thêm 1 đoạn note vào project_notes.md. Dùng chung cho mọi notebook,
    tránh lặp lại boilerplate 'with open(...) as f: f.write(...)' ở từng cell."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)