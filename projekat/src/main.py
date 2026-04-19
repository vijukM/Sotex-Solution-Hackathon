import pandas as pd
from load_data import (
    load_transmission_stations,
    load_substations,
    load_dt,
    load_feeders33,
    load_feeders33substation,
    load_feeders11
)
from visualize import plot_station_points

from build_graph import build_power_graph

from analysis import analyze_graph

from visualize import plot_ss_dt_only

def extract_feeder33_core(feeder33: pd.DataFrame) -> pd.DataFrame:
    df = feeder33[["Id", "TsId"]].copy()
    df = df.rename(columns={
        "Id": "Feeder33Id",
        "TsId": "TsId"
    })
    df = df.dropna(subset=["Feeder33Id", "TsId"]).copy()
    df["Feeder33Id"] = df["Feeder33Id"].astype(int)
    df["TsId"] = df["TsId"].astype(int)
    return df


def extract_feeder33_substation_core(feeder33_substation: pd.DataFrame) -> pd.DataFrame:
    df = feeder33_substation[["Feeders33Id", "SubstationsId"]].copy()
    df = df.rename(columns={
        "Feeders33Id": "Feeder33Id",
        "SubstationsId": "SsId"
    })
    df = df.dropna(subset=["Feeder33Id", "SsId"]).copy()
    df["Feeder33Id"] = df["Feeder33Id"].astype(int)
    df["SsId"] = df["SsId"].astype(int)
    return df


def extract_feeder11_core(feeder11: pd.DataFrame) -> pd.DataFrame:
    df = feeder11[["SsId", "Feeder33Id"]].copy()
    df = df.rename(columns={
        "SsId": "SsId"
    })
    df = df.dropna(subset=["SsId", "Feeder33Id"]).copy()
    df["SsId"] = df["SsId"].astype(int)
    df["Feeder33Id"] = df["Feeder33Id"].astype(int)
    return df


def extract_dt_feeder33_core(dt: pd.DataFrame) -> pd.DataFrame:
    df = dt[["Id", "Feeder33Id"]].copy()
    df = df.rename(columns={
        "Id": "DtId"
    })
    df = df.dropna(subset=["Feeder33Id"]).copy()
    df["DtId"] = df["DtId"].astype(int)
    df["Feeder33Id"] = df["Feeder33Id"].astype(int)
    return df


def extract_feeder11_ss_core(feeder11: pd.DataFrame) -> pd.DataFrame:
    df = feeder11[["Id", "SsId"]].copy()
    df = df.rename(columns={
        "Id": "Feeder11Id",
        "SsId": "SsId"
    })
    df = df.dropna(subset=["Feeder11Id", "SsId"]).copy()
    df["Feeder11Id"] = df["Feeder11Id"].astype(int)
    df["SsId"] = df["SsId"].astype(int)
    return df


def extract_dt_feeder11_core(dt: pd.DataFrame) -> pd.DataFrame:
    df = dt[["Id", "Feeder11Id"]].copy()
    df = df.rename(columns={
        "Id": "DtId"
    })
    df = df.dropna(subset=["Feeder11Id"]).copy()
    df["DtId"] = df["DtId"].astype(int)
    df["Feeder11Id"] = df["Feeder11Id"].astype(int)
    return df


def build_ts_ss_edges_from_feeder33_substation(
    feeder33_core: pd.DataFrame,
    feeder33_substation_core: pd.DataFrame
) -> pd.DataFrame:
    df = feeder33_core.merge(
        feeder33_substation_core,
        on="Feeder33Id",
        how="inner"
    )
    return df[["TsId", "SsId", "Feeder33Id"]].drop_duplicates()


def build_ts_ss_edges_from_feeder11(
    feeder33_core: pd.DataFrame,
    feeder11_core: pd.DataFrame
) -> pd.DataFrame:
    df = feeder33_core.merge(
        feeder11_core,
        on="Feeder33Id",
        how="inner"
    )
    return df[["TsId", "SsId", "Feeder33Id"]].drop_duplicates()


def build_ts_dt_edges_from_dt(
    feeder33_core: pd.DataFrame,
    dt_feeder33_core: pd.DataFrame
) -> pd.DataFrame:
    df = feeder33_core.merge(
        dt_feeder33_core,
        on="Feeder33Id",
        how="inner"
    )
    return df[["TsId", "DtId", "Feeder33Id"]].drop_duplicates()


def build_ss_dt_edges_from_feeder11(
    feeder11_ss_core: pd.DataFrame,
    dt_feeder11_core: pd.DataFrame
) -> pd.DataFrame:
    df = feeder11_ss_core.merge(
        dt_feeder11_core,
        on="Feeder11Id",
        how="inner"
    )
    return df[["SsId", "DtId", "Feeder11Id"]].drop_duplicates()

def extract_feeder11_ts_core(feeder11: pd.DataFrame) -> pd.DataFrame:
    df = feeder11[["Id", "TsId"]].copy()
    df = df.rename(columns={
        "Id": "Feeder11Id",
        "TsId": "TsId"
    })
    df = df.dropna(subset=["Feeder11Id", "TsId"]).copy()
    df["Feeder11Id"] = df["Feeder11Id"].astype(int)
    df["TsId"] = df["TsId"].astype(int)
    return df





def build_ts_dt_edges_from_feeder11(
    feeder11_ts_core: pd.DataFrame,
    dt_feeder11_core: pd.DataFrame
) -> pd.DataFrame:
    df = feeder11_ts_core.merge(
        dt_feeder11_core,
        on="Feeder11Id",
        how="inner"
    )
    return df[["TsId", "DtId", "Feeder11Id"]].drop_duplicates()


def main():
    ts = load_transmission_stations()
    ss = load_substations()
    dt = load_dt()

    feeder33 = load_feeders33()
    feeder33_substation = load_feeders33substation()
    feeder11 = load_feeders11()

    feeder33_core = extract_feeder33_core(feeder33)
    feeder33_substation_core = extract_feeder33_substation_core(feeder33_substation)
    feeder11_core = extract_feeder11_core(feeder11)

    cleaned_data = {}

    for name, df in [("TS", ts), ("SS", ss), ("DT", dt)]:
        lat_num = pd.to_numeric(df["Latitude"], errors="coerce")
        lon_num = pd.to_numeric(df["Longitude"], errors="coerce")

        invalid_lat = df[lat_num.isna() & df["Latitude"].notna()]
        invalid_lon = df[lon_num.isna() & df["Longitude"].notna()]

        print(f"\n{name}")
        print("Missing Latitude:", df["Latitude"].isna().sum())
        print("Missing Longitude:", df["Longitude"].isna().sum())
        print("Non-numeric Latitude:", len(invalid_lat))
        print("Non-numeric Longitude:", len(invalid_lon))

        if len(invalid_lat) > 0:
            print("\nInvalid Latitude rows:")
            print(invalid_lat[["Id", "Name", "Latitude"]].head())

        if len(invalid_lon) > 0:
            print("\nInvalid Longitude rows:")
            print(invalid_lon[["Id", "Name", "Longitude"]].head())

        df = df.copy()
        df["Latitude"] = lat_num
        df["Longitude"] = lon_num

        df_clean = df.dropna(subset=["Latitude", "Longitude"]).copy()
        removed = len(df) - len(df_clean)
        print(f"Removed {name} rows due to missing coordinates:", removed)

        cleaned_data[name] = df_clean

    ts_clean = cleaned_data["TS"]
    ss_clean = cleaned_data["SS"]
    dt_clean = cleaned_data["DT"]

    print("\nClean shapes:")
    print("TS:", ts_clean.shape)
    print("SS:", ss_clean.shape)
    print("DT:", dt_clean.shape)

    print("\nFeeder core shapes:")
    print("Feeder33 core:", feeder33_core.shape)
    print("Feeder33Substation core:", feeder33_substation_core.shape)
    print("Feeder11 core:", feeder11_core.shape)

    print("\nFeeder33 core preview:")
    print(feeder33_core.head())

    print("\nFeeder33Substation core preview:")
    print(feeder33_substation_core.head())

    print("\nFeeder11 core preview:")
    print(feeder11_core.head())

    ts_ss_from_substation = build_ts_ss_edges_from_feeder33_substation(
        feeder33_core,
        feeder33_substation_core
    )

    ts_ss_from_feeder11 = build_ts_ss_edges_from_feeder11(
        feeder33_core,
        feeder11_core
    )

    print("\nTS-SS edges from Feeder33Substation:", ts_ss_from_substation.shape)
    print("TS-SS edges from Feeder11:", ts_ss_from_feeder11.shape)

    print("\nTS-SS from Feeder33Substation preview:")
    print(ts_ss_from_substation.head())

    print("\nTS-SS from Feeder11 preview:")
    print(ts_ss_from_feeder11.head())

    ts_ss_edges = pd.concat(
        [ts_ss_from_substation, ts_ss_from_feeder11],
        ignore_index=True
    ).drop_duplicates()

    print("\nUnified TS-SS edges:", ts_ss_edges.shape)
    print(ts_ss_edges.head())

    dt_feeder33_core = extract_dt_feeder33_core(dt)
    ts_dt_edges = build_ts_dt_edges_from_dt(
        feeder33_core,
        dt_feeder33_core
    )

    print("\nDT-Feeder33 core shape:", dt_feeder33_core.shape)
    print("TS-DT edges:", ts_dt_edges.shape)

    print("\nDT-Feeder33 core preview:")
    print(dt_feeder33_core.head())

    print("\nTS-DT edges preview:")
    print(ts_dt_edges.head())

    print("DT missing Feeder33Id in raw dt:", dt["Feeder33Id"].isna().sum())
    print("DT non-missing Feeder33Id in raw dt:", dt["Feeder33Id"].notna().sum())

    feeder11_ss_core = extract_feeder11_ss_core(feeder11)
    dt_feeder11_core = extract_dt_feeder11_core(dt)

    ss_dt_edges = build_ss_dt_edges_from_feeder11(
        feeder11_ss_core,
        dt_feeder11_core
    )

    feeder11_ts_core = extract_feeder11_ts_core(feeder11)
    dt_feeder11_core = extract_dt_feeder11_core(dt)

    ts_dt_edges_from_feeder11 = build_ts_dt_edges_from_feeder11(
        feeder11_ts_core,
        dt_feeder11_core
    )

    print("\nFeeder11-TS core shape:", feeder11_ts_core.shape)
    print("DT-Feeder11 core shape:", dt_feeder11_core.shape)
    print("TS-DT edges from Feeder11:", ts_dt_edges_from_feeder11.shape)

    print("\nTS-DT edges from Feeder11 preview:")
    print(ts_dt_edges_from_feeder11.head())


    print("\nFeeder11-SS core shape:", feeder11_ss_core.shape)
    print("DT-Feeder11 core shape:", dt_feeder11_core.shape)
    print("SS-DT edges:", ss_dt_edges.shape)

    print("\nSS-DT edges preview:")
    print(ss_dt_edges.head())

    plot_station_points(
        ts_clean,
        ss_clean,
        dt_clean,
        ts_ss_edges,
        ts_dt_edges,
        ss_dt_edges
    ,ts_dt_edges_from_feeder11)



    G = build_power_graph(
    ts_clean,
    ss_clean,
    dt_clean,
    ts_ss_edges,
    ts_dt_edges,
    ss_dt_edges,
    ts_dt_edges_from_feeder11
    )



    print("Number of nodes:", G.number_of_nodes())
    print("Number of edges:", G.number_of_edges())

    results = analyze_graph(G)

    ranked_art_points = sorted(
        results["non_ts_articulation_points"],
        key=lambda n: G.degree(n),
        reverse=True
    )

    print("\nTop 20 non-TS articulation points:")
    print(ranked_art_points[:20])

    top_5_dangerous = ranked_art_points[:5]

    coordinates = {}

    for node in top_5_dangerous:
        node_data = G.nodes[node]

        coordinates[node] = {
            "name": node_data["name"],
            "latitude": node_data["latitude"],
            "longitude": node_data["longitude"],
            "node_type": node_data["node_type"],
            "original_id": node_data["original_id"],
        }

    print("\nTop 5 dangerous nodes with metadata:")
    print(coordinates)

    plot_ss_dt_only(ss_clean, dt_clean, ss_dt_edges)



if __name__ == "__main__":
    main()