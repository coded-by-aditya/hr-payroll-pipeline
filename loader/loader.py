import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import snowflake.connector
import yaml
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

CONFIG_PATH = Path("loader/sources.yaml")


def find_files(landing_dir, pattern):
    return sorted(Path(landing_dir).glob(f"*/{pattern}"))


def get_connection():
    load_dotenv()
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
    )
    return conn


def ensure_audit_table(conn):
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS RAW.LOAD_AUDIT (
            source_name   STRING,
            file_name     STRING,
            rows_read     INTEGER,
            rows_loaded   INTEGER,
            rows_rejected INTEGER,
            status        STRING,
            loaded_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
    """)


def already_loaded(conn):
    rows = conn.cursor().execute(
        "SELECT file_name FROM RAW.LOAD_AUDIT WHERE status = 'SUCCESS'"
    ).fetchall()
    return {row[0] for row in rows}


def read_file(path, fmt):
    if fmt == "json":
        df = pd.read_json(path, dtype=False, convert_dates=False)
    else:
        df = pd.read_csv(path, dtype=str)
    return df.astype("string")  # RAW keeps everything as text; dbt casts types later


def split_valid(df, required_fields):
    missing = df[required_fields].isna().any(axis=1)
    return df[~missing].reset_index(drop=True), df[missing].reset_index(drop=True)


def load_file(conn, source, path):
    df = read_file(path, source["format"])
    good, bad = split_valid(df, source["required_fields"])
    loaded_at = datetime.now(timezone.utc).isoformat()

    if len(good) > 0:
        good = good.copy()
        good.columns = [c.upper() for c in good.columns]
        good["_SOURCE_FILE"] = str(path)
        good["_LOADED_AT"] = loaded_at
        write_pandas(conn, good, table_name=source["target_table"], schema="RAW",
                     auto_create_table=True, quote_identifiers=False)

    if len(bad) > 0:
        rejects = pd.DataFrame({
            "SOURCE_NAME": source["name"],
            "FILE_NAME": str(path),
            "RECORD": [row.to_json() for _, row in bad.iterrows()],
            "REASON": "missing required field",
            "LOADED_AT": loaded_at,
        })
        write_pandas(conn, rejects, table_name="REJECTS", schema="RAW",
                     auto_create_table=True, quote_identifiers=False)

    return len(df), len(good), len(bad)


def write_audit(conn, source_name, path, rows_read, rows_loaded, rows_rejected, status):
    conn.cursor().execute(
        "INSERT INTO RAW.LOAD_AUDIT "
        "(source_name, file_name, rows_read, rows_loaded, rows_rejected, status) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (source_name, str(path), rows_read, rows_loaded, rows_rejected, status),
    )


def main():
    config = yaml.safe_load(CONFIG_PATH.read_text())
    conn = get_connection()
    ensure_audit_table(conn)
    loaded = already_loaded(conn)

    failures = 0
    for source in config["sources"]:
        files = find_files(config["landing_dir"], source["file_pattern"])
        for f in files:
            if str(f) in loaded:
                print(f"skip {f} (already loaded)")
                continue
            try:
                read, ok, rejected = load_file(conn, source, f)
                write_audit(conn, source["name"], f, read, ok, rejected, "SUCCESS")
                print(f"loaded {f}: {read} read, {ok} loaded, {rejected} rejected")
            except Exception as e:
                write_audit(conn, source["name"], f, 0, 0, 0, "FAILED")
                print(f"FAILED {f}: {e}")
                failures += 1

    conn.close()
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()