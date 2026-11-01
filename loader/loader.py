import yaml
from pathlib import Path
import os
import snowflake.connector
from dotenv import load_dotenv

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
        database=os.environ["SNOWFLAKE_DATABASE"],)
    return conn

def main():

    conn = get_connection()
    print(conn.cursor().execute("SELECT CURRENT_USER(), CURRENT_ROLE()").fetchone())

    

    config = yaml.safe_load(CONFIG_PATH.read_text())

    for source in config["sources"]:
        files = find_files(config["landing_dir"], source["file_pattern"])
        print(source["name"], [str(f) for f in files])



if __name__ == "__main__":
    main()   