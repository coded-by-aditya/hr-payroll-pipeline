import os
from dotenv import load_dotenv
import snowflake.connector

load_dotenv()
conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=os.environ["SNOWFLAKE_PASSWORD"],
    role=os.environ["SNOWFLAKE_ROLE"],
    warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
    database=os.environ["SNOWFLAKE_DATABASE"],
)
print(conn.cursor().execute("SELECT CURRENT_USER(), CURRENT_ROLE()").fetchone())
conn.close()