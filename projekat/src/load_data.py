import pandas as pd
from db import get_engine


def load_table(table_name: str):
    engine = get_engine()
    query = f"SELECT * FROM dbo.{table_name}"
    return pd.read_sql(query, engine)


def load_transmission_stations():
    return load_table("TransmissionStations")


def load_substations():
    return load_table("Substations")


def load_dt():
    return load_table("DistributionSubstation")


def load_feeders33():
    return load_table("Feeders33")


def load_feeders33substation():
    return load_table("Feeder33Substation")


def load_feeders11():
    return load_table("Feeders11")


def build_feeders33_core(feeders33: pd.DataFrame) -> pd.DataFrame:
    feeders33_core = feeders33[["Id", "TsId"]].copy()
    feeders33_core = feeders33_core.rename(columns={
        "Id": "Feeder33id",
        "TsId": "TSid"
    })
    return feeders33_core


if __name__ == "__main__":
    ts = load_transmission_stations()
    ss = load_substations()
    dt = load_dt()
    feeders33 = load_feeders33()
    feeders33substation = load_feeders33substation()
    feeders11 = load_feeders11()

    feeders33_core = build_feeders33_core(feeders33)

    print("TransmissionStations:", ts.shape)
    print("Substations:", ss.shape)
    print("Dt:", dt.shape)
    print("Feeders33:", feeders33.shape)
    print("Feeders33Substation:", feeders33substation.shape)
    print("Feeders11:", feeders11.shape)

    print("\nFeeders33 columns:", feeders33.columns.tolist())
    print("Feeders33Substation columns:", feeders33substation.columns.tolist())
    print("Feeders11 columns:", feeders11.columns.tolist())

    print("\nFeeders33 core preview:")
    print(feeders33_core.head())