from sqlalchemy import create_engine
from urllib.parse import quote_plus


def get_engine():
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=SotexHackathon;"
        "UID=sa;"
        "PWD=SotexSolutions123!;"
        "TrustServerCertificate=yes;"
    )

    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={quote_plus(conn_str)}"
    )       