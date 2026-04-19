# service.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import networkx as nx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from load_data import (
    load_transmission_stations,
    load_substations,
    load_dt,
    load_feeders33,
    load_feeders33substation,
    load_feeders11,
)

from build_graph import build_power_graph
from analysis import (
    analyze_graph,
    shortlist_non_ts_articulation_points,
    rank_shortlisted_nodes_by_damage,
)
from visualize import plot_station_points, plot_ss_dt_only


app = FastAPI(title="Power Graph Service")


# Pošto ti visualize.py trenutno koristi hardkodirane putanje,
# ovde stavljamo iste te putanje da service zna gde da traži fajlove.
STATIONS_PLOT_PATH = Path(
    "/home/marko/Desktop/Sotex_Hackaton/hackathon_2026/projekat/outputs/stations_plot_zoomed.png"
)
SS_DT_PLOT_PATH = Path(
    "/home/marko/Desktop/Sotex_Hackaton/hackathon_2026/projekat/outputs/ss_dt_only.png"
)


def clean_station_dataframe(
    df: pd.DataFrame,
    name: str
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    lat_num = pd.to_numeric(df["Latitude"], errors="coerce")
    lon_num = pd.to_numeric(df["Longitude"], errors="coerce")

    invalid_lat = df[lat_num.isna() & df["Latitude"].notna()]
    invalid_lon = df[lon_num.isna() & df["Longitude"].notna()]

    df = df.copy()
    df["Latitude"] = lat_num
    df["Longitude"] = lon_num

    df_clean = df.dropna(subset=["Latitude", "Longitude"]).copy()

    stats = {
        "dataset": name,
        "input_rows": int(len(df)),
        "output_rows": int(len(df_clean)),
        "removed_rows": int(len(df) - len(df_clean)),
        "missing_latitude": int(df["Latitude"].isna().sum()),
        "missing_longitude": int(df["Longitude"].isna().sum()),
        "invalid_latitude_rows": int(len(invalid_lat)),
        "invalid_longitude_rows": int(len(invalid_lon)),
    }

    return df_clean, stats


def extract_feeder33_core(feeder33: pd.DataFrame) -> pd.DataFrame:
    df = feeder33[["Id", "TsId"]].copy()
    df = df.rename(columns={"Id": "Feeder33Id", "TsId": "TsId"})
    df = df.dropna(subset=["Feeder33Id", "TsId"]).copy()
    df["Feeder33Id"] = df["Feeder33Id"].astype(int)
    df["TsId"] = df["TsId"].astype(int)
    return df


def extract_feeder33_substation_core(feeder33_substation: pd.DataFrame) -> pd.DataFrame:
    df = feeder33_substation[["Feeders33Id", "SubstationsId"]].copy()
    df = df.rename(columns={"Feeders33Id": "Feeder33Id", "SubstationsId": "SsId"})
    df = df.dropna(subset=["Feeder33Id", "SsId"]).copy()
    df["Feeder33Id"] = df["Feeder33Id"].astype(int)
    df["SsId"] = df["SsId"].astype(int)
    return df


def extract_feeder11_core(feeder11: pd.DataFrame) -> pd.DataFrame:
    df = feeder11[["SsId", "Feeder33Id"]].copy()
    df = df.dropna(subset=["SsId", "Feeder33Id"]).copy()
    df["SsId"] = df["SsId"].astype(int)
    df["Feeder33Id"] = df["Feeder33Id"].astype(int)
    return df


def extract_dt_feeder33_core(dt: pd.DataFrame) -> pd.DataFrame:
    df = dt[["Id", "Feeder33Id"]].copy()
    df = df.rename(columns={"Id": "DtId"})
    df = df.dropna(subset=["Feeder33Id"]).copy()
    df["DtId"] = df["DtId"].astype(int)
    df["Feeder33Id"] = df["Feeder33Id"].astype(int)
    return df


def extract_feeder11_ss_core(feeder11: pd.DataFrame) -> pd.DataFrame:
    df = feeder11[["Id", "SsId"]].copy()
    df = df.rename(columns={"Id": "Feeder11Id"})
    df = df.dropna(subset=["Feeder11Id", "SsId"]).copy()
    df["Feeder11Id"] = df["Feeder11Id"].astype(int)
    df["SsId"] = df["SsId"].astype(int)
    return df


def extract_dt_feeder11_core(dt: pd.DataFrame) -> pd.DataFrame:
    df = dt[["Id", "Feeder11Id"]].copy()
    df = df.rename(columns={"Id": "DtId"})
    df = df.dropna(subset=["Feeder11Id"]).copy()
    df["DtId"] = df["DtId"].astype(int)
    df["Feeder11Id"] = df["Feeder11Id"].astype(int)
    return df


def extract_feeder11_ts_core(feeder11: pd.DataFrame) -> pd.DataFrame:
    df = feeder11[["Id", "TsId"]].copy()
    df = df.rename(columns={"Id": "Feeder11Id"})
    df = df.dropna(subset=["Feeder11Id", "TsId"]).copy()
    df["Feeder11Id"] = df["Feeder11Id"].astype(int)
    df["TsId"] = df["TsId"].astype(int)
    return df


def build_ts_ss_edges_from_feeder33_substation(
    feeder33_core: pd.DataFrame,
    feeder33_substation_core: pd.DataFrame,
) -> pd.DataFrame:
    df = feeder33_core.merge(feeder33_substation_core, on="Feeder33Id", how="inner")
    return df[["TsId", "SsId", "Feeder33Id"]].drop_duplicates()


def build_ts_ss_edges_from_feeder11(
    feeder33_core: pd.DataFrame,
    feeder11_core: pd.DataFrame,
) -> pd.DataFrame:
    df = feeder33_core.merge(feeder11_core, on="Feeder33Id", how="inner")
    return df[["TsId", "SsId", "Feeder33Id"]].drop_duplicates()


def build_ts_dt_edges_from_dt(
    feeder33_core: pd.DataFrame,
    dt_feeder33_core: pd.DataFrame,
) -> pd.DataFrame:
    df = feeder33_core.merge(dt_feeder33_core, on="Feeder33Id", how="inner")
    return df[["TsId", "DtId", "Feeder33Id"]].drop_duplicates()


def build_ss_dt_edges_from_feeder11(
    feeder11_ss_core: pd.DataFrame,
    dt_feeder11_core: pd.DataFrame,
) -> pd.DataFrame:
    df = feeder11_ss_core.merge(dt_feeder11_core, on="Feeder11Id", how="inner")
    return df[["SsId", "DtId", "Feeder11Id"]].drop_duplicates()


def build_ts_dt_edges_from_feeder11(
    feeder11_ts_core: pd.DataFrame,
    dt_feeder11_core: pd.DataFrame,
) -> pd.DataFrame:
    df = feeder11_ts_core.merge(dt_feeder11_core, on="Feeder11Id", how="inner")
    return df[["TsId", "DtId", "Feeder11Id"]].drop_duplicates()


def load_and_prepare_graph_data() -> Dict[str, Any]:
    ts = load_transmission_stations()
    ss = load_substations()
    dt = load_dt()
    feeder33 = load_feeders33()
    feeder33_substation = load_feeders33substation()
    feeder11 = load_feeders11()

    ts_clean, ts_stats = clean_station_dataframe(ts, "TS")
    ss_clean, ss_stats = clean_station_dataframe(ss, "SS")
    dt_clean, dt_stats = clean_station_dataframe(dt, "DT")

    feeder33_core = extract_feeder33_core(feeder33)
    feeder33_substation_core = extract_feeder33_substation_core(feeder33_substation)
    feeder11_core = extract_feeder11_core(feeder11)

    ts_ss_from_substation = build_ts_ss_edges_from_feeder33_substation(
        feeder33_core, feeder33_substation_core
    )
    ts_ss_from_feeder11 = build_ts_ss_edges_from_feeder11(
        feeder33_core, feeder11_core
    )
    ts_ss_edges = pd.concat(
        [ts_ss_from_substation, ts_ss_from_feeder11],
        ignore_index=True
    ).drop_duplicates()

    dt_feeder33_core = extract_dt_feeder33_core(dt)
    ts_dt_edges = build_ts_dt_edges_from_dt(feeder33_core, dt_feeder33_core)

    feeder11_ss_core = extract_feeder11_ss_core(feeder11)
    dt_feeder11_core = extract_dt_feeder11_core(dt_clean)
    ss_dt_edges = build_ss_dt_edges_from_feeder11(feeder11_ss_core, dt_feeder11_core)

    feeder11_ts_core = extract_feeder11_ts_core(feeder11)
    ts_dt_edges_from_feeder11 = build_ts_dt_edges_from_feeder11(
        feeder11_ts_core, dt_feeder11_core
    )

    G = build_power_graph(
        ts_clean=ts_clean,
        ss_clean=ss_clean,
        dt_clean=dt_clean,
        ts_ss_edges=ts_ss_edges,
        ts_dt_edges=ts_dt_edges,
        ss_dt_edges=ss_dt_edges,
        ts_dt_edges_from_feeder11=ts_dt_edges_from_feeder11,
    )

    return {
        "graph": G,
        "ts_clean": ts_clean,
        "ss_clean": ss_clean,
        "dt_clean": dt_clean,
        "ts_ss_edges": ts_ss_edges,
        "ts_dt_edges": ts_dt_edges,
        "ss_dt_edges": ss_dt_edges,
        "ts_dt_edges_from_feeder11": ts_dt_edges_from_feeder11,
        "cleaning_stats": [ts_stats, ss_stats, dt_stats],
    }


def get_graph_summary() -> Dict[str, Any]:
    data = load_and_prepare_graph_data()
    G = data["graph"]

    node_type_counts: Dict[str, int] = {}
    for _, attrs in G.nodes(data=True):
        node_type = attrs.get("node_type", "UNKNOWN")
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1

    edge_type_counts: Dict[str, int] = {}
    for _, _, attrs in G.edges(data=True):
        edge_type = attrs.get("edge_type", "UNKNOWN")
        edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1

    return {
        "num_nodes": int(G.number_of_nodes()),
        "num_edges": int(G.number_of_edges()),
        "node_type_counts": node_type_counts,
        "edge_type_counts": edge_type_counts,
        "cleaning_stats": data["cleaning_stats"],
    }


def get_vulnerable_nodes(top_k: int = 5) -> Dict[str, Any]:
    data = load_and_prepare_graph_data()
    G = data["graph"]
    results = analyze_graph(G)
    G_und = results["G_und"]

    shortlisted = shortlist_non_ts_articulation_points(G_und, top_k=max(top_k * 3, 20))
    ranked = rank_shortlisted_nodes_by_damage(G_und, shortlisted)

    nodes: List[Dict[str, Any]] = []

    for rank_idx, item in enumerate(ranked[:top_k], start=1):
        node = item["node"]
        node_data = G.nodes[node]

        nodes.append({
            "rank": rank_idx,
            "node": [node[0], int(node[1])],
            "name": node_data.get("name"),
            "node_type": node_data.get("node_type"),
            "original_id": int(node_data.get("original_id")) if node_data.get("original_id") is not None else None,
            "latitude": float(node_data.get("latitude")) if node_data.get("latitude") is not None else None,
            "longitude": float(node_data.get("longitude")) if node_data.get("longitude") is not None else None,
            "degree": int(G.degree(node)),
            "damage_score": int(item["damage_score"]),
            "largest_component_drop": int(item["largest_component_drop"]),
        })

    return {
        "top_k": int(top_k),
        "nodes": nodes,
    }


def ensure_visualizations_exist() -> Dict[str, str]:
    data = load_and_prepare_graph_data()

    plot_station_points(
        data["ts_clean"],
        data["ss_clean"],
        data["dt_clean"],
        data["ts_ss_edges"],
        data["ts_dt_edges"],
        data["ss_dt_edges"],
        data["ts_dt_edges_from_feeder11"],
    )

    plot_ss_dt_only(
        data["ss_clean"],
        data["dt_clean"],
        data["ss_dt_edges"],
    )

    if not STATIONS_PLOT_PATH.exists():
        raise FileNotFoundError(f"Stations plot nije pronađen: {STATIONS_PLOT_PATH}")

    if not SS_DT_PLOT_PATH.exists():
        raise FileNotFoundError(f"SS-DT plot nije pronađen: {SS_DT_PLOT_PATH}")

    return {
        "stations_plot_path": str(STATIONS_PLOT_PATH),
        "ss_dt_plot_path": str(SS_DT_PLOT_PATH),
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/summary")
def summary() -> Dict[str, Any]:
    try:
        return get_graph_summary()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Greška pri summary obradi: {exc}") from exc


@app.get("/analysis/vulnerable-nodes")
def vulnerable_nodes(
    top_k: int = Query(default=5, ge=1, le=100)
) -> Dict[str, Any]:
    try:
        return get_vulnerable_nodes(top_k=top_k)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Greška pri računanju najranjivijih čvorova: {exc}"
        ) from exc


@app.get("/visualizations")
def visualizations() -> Dict[str, str]:
    try:
        paths = ensure_visualizations_exist()
        return {
            "stations_plot_url": "/visualizations/stations-plot",
            "ss_dt_plot_url": "/visualizations/ss-dt-plot",
            "stations_plot_path": paths["stations_plot_path"],
            "ss_dt_plot_path": paths["ss_dt_plot_path"],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Greška pri generisanju vizuelizacija: {exc}"
        ) from exc


@app.get("/visualizations/stations-plot")
def stations_plot() -> FileResponse:
    try:
        ensure_visualizations_exist()

        if not STATIONS_PLOT_PATH.exists():
            raise HTTPException(status_code=404, detail="Stations plot nije pronađen.")

        return FileResponse(
            path=str(STATIONS_PLOT_PATH),
            media_type="image/png",
            filename="stations_plot.png",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Greška pri slanju stations plot slike: {exc}"
        ) from exc


@app.get("/visualizations/ss-dt-plot")
def ss_dt_plot() -> FileResponse:
    try:
        ensure_visualizations_exist()

        if not SS_DT_PLOT_PATH.exists():
            raise HTTPException(status_code=404, detail="SS-DT plot nije pronađen.")

        return FileResponse(
            path=str(SS_DT_PLOT_PATH),
            media_type="image/png",
            filename="ss_dt_plot.png",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Greška pri slanju SS-DT plot slike: {exc}"
        ) from exc