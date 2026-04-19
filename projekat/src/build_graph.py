import networkx as nx
import pandas as pd


def build_power_graph(
    ts_clean: pd.DataFrame,
    ss_clean: pd.DataFrame,
    dt_clean: pd.DataFrame,
    ts_ss_edges: pd.DataFrame,
    ts_dt_edges: pd.DataFrame,
    ss_dt_edges: pd.DataFrame,
    ts_dt_edges_from_feeder11: pd.DataFrame
) -> nx.DiGraph:
    G = nx.DiGraph()

    # standardize edge column names just in case
    ts_ss_edges = ts_ss_edges.rename(columns={
        "TSid": "TsId",
        "SSid": "SsId",
        "DTid": "DtId"
    }).copy()

    ts_dt_edges = ts_dt_edges.rename(columns={
        "TSid": "TsId",
        "SSid": "SsId",
        "DTid": "DtId"
    }).copy()

    ss_dt_edges = ss_dt_edges.rename(columns={
        "TSid": "TsId",
        "SSid": "SsId",
        "DTid": "DtId"
    }).copy()

    ts_dt_edges_from_feeder11 = ts_dt_edges_from_feeder11.rename(columns={
        "TSid": "TsId",
        "SSid": "SsId",
        "DTid": "DtId"
    }).copy()

    # combine both TS -> DT sources
    ts_dt_edges_all = pd.concat(
        [ts_dt_edges, ts_dt_edges_from_feeder11],
        ignore_index=True
    ).drop_duplicates()

    # add TS nodes
    for _, row in ts_clean.iterrows():
        node_id = ("TS", int(row["Id"]))
        G.add_node(
            node_id,
            node_type="TS",
            original_id=int(row["Id"]),
            name=row["Name"] if "Name" in row else None,
            longitude=float(row["Longitude"]),
            latitude=float(row["Latitude"])
        )

    # add SS nodes
    for _, row in ss_clean.iterrows():
        node_id = ("SS", int(row["Id"]))
        G.add_node(
            node_id,
            node_type="SS",
            original_id=int(row["Id"]),
            name=row["Name"] if "Name" in row else None,
            longitude=float(row["Longitude"]),
            latitude=float(row["Latitude"])
        )

    # add DT nodes
    for _, row in dt_clean.iterrows():
        node_id = ("DT", int(row["Id"]))
        G.add_node(
            node_id,
            node_type="DT",
            original_id=int(row["Id"]),
            name=row["Name"] if "Name" in row else None,
            longitude=float(row["Longitude"]),
            latitude=float(row["Latitude"])
        )

    # add TS -> SS edges
    for _, row in ts_ss_edges.iterrows():
        source = ("TS", int(row["TsId"]))
        target = ("SS", int(row["SsId"]))

        if source in G and target in G:
            G.add_edge(source, target, edge_type="TS-SS")

    # add TS -> DT edges from both sources
    for _, row in ts_dt_edges_all.iterrows():
        source = ("TS", int(row["TsId"]))
        target = ("DT", int(row["DtId"]))

        if source in G and target in G:
            G.add_edge(source, target, edge_type="TS-DT")

    # add SS -> DT edges
    for _, row in ss_dt_edges.iterrows():
        source = ("SS", int(row["SsId"]))
        target = ("DT", int(row["DtId"]))

        if source in G and target in G:
            G.add_edge(source, target, edge_type="SS-DT")

    return G

