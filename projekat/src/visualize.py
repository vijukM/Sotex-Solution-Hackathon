import matplotlib.pyplot as plt
import os
import pandas as pd


def filter_bbox(df, lon_min, lon_max, lat_min, lat_max):
    return df[
        (df["Longitude"] >= lon_min) &
        (df["Longitude"] <= lon_max) &
        (df["Latitude"] >= lat_min) &
        (df["Latitude"] <= lat_max)
    ].copy()


def plot_ss_dt_only(ss_clean, dt_clean, ss_dt_edges):
    output_path = "/home/marko/Desktop/Sotex_Hackaton/hackathon_2026/projekat/outputs/ss_dt_only.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    lon_min, lon_max = 6.95, 7.7
    lat_min, lat_max = 8.8, 9.2

    ss_plot = filter_bbox(ss_clean, lon_min, lon_max, lat_min, lat_max)
    dt_plot = filter_bbox(dt_clean, lon_min, lon_max, lat_min, lat_max)

    print("SS plotted:", ss_plot.shape)
    print("DT plotted:", dt_plot.shape)

    # keep only edges whose endpoints are visible
    ss_dt_plot = ss_dt_edges[
        ss_dt_edges["SsId"].isin(ss_plot["Id"]) &
        ss_dt_edges["DtId"].isin(dt_plot["Id"])
    ].copy()

    print("SS-DT edges plotted:", ss_dt_plot.shape)

    # attach SS coordinates
    ss_dt_plot = ss_dt_plot.merge(
        ss_plot[["Id", "Longitude", "Latitude"]].rename(columns={
            "Id": "SsId",
            "Longitude": "SS_lon",
            "Latitude": "SS_lat"
        }),
        on="SsId",
        how="inner"
    )

    # attach DT coordinates
    ss_dt_plot = ss_dt_plot.merge(
        dt_plot[["Id", "Longitude", "Latitude"]].rename(columns={
            "Id": "DtId",
            "Longitude": "DT_lon",
            "Latitude": "DT_lat"
        }),
        on="DtId",
        how="inner"
    )

    plt.figure(figsize=(12, 8))

    # SS -> DT edges
    for _, row in ss_dt_plot.iterrows():
        plt.plot(
            [row["SS_lon"], row["DT_lon"]],
            [row["SS_lat"], row["DT_lat"]],
            color="black",
            alpha=0.10,
            linewidth=0.4,
            zorder=1
        )

    # DT nodes
    plt.scatter(
        dt_plot["Longitude"],
        dt_plot["Latitude"],
        label="DT",
        color="blue",
        s=20,
        alpha=0.10,
        linewidths=0,
        zorder=2
    )

    # SS nodes
    plt.scatter(
        ss_plot["Longitude"],
        ss_plot["Latitude"],
        label="SS",
        color="red",
        s=90,
        alpha=0.85,
        linewidths=0,
        zorder=3
    )

    # legend
    plt.plot([], [], color="black", label="SS-DT edge")
    plt.scatter([], [], color="red", s=90, label="SS")
    plt.scatter([], [], color="blue", s=20, label="DT")

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("SS-DT Network (Without TS)")
    plt.legend()
    plt.grid(True, alpha=0.2)

    plt.xlim(lon_min, lon_max)
    plt.ylim(lat_min, lat_max)

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Plot saved to: {output_path}")
    plt.close()

def plot_station_points(
    ts_clean,
    ss_clean,
    dt_clean,
    ts_ss_edges,
    ts_dt_edges,
    ss_dt_edges,
    ts_dt_edges_from_feeder11
):
    output_path = "/home/marko/Desktop/Sotex_Hackaton/hackathon_2026/projekat/outputs/stations_plot_zoomed.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    lon_min, lon_max = 6.95, 7.7
    lat_min, lat_max = 8.8, 9.2

    ts_plot = filter_bbox(ts_clean, lon_min, lon_max, lat_min, lat_max)
    ss_plot = filter_bbox(ss_clean, lon_min, lon_max, lat_min, lat_max)
    dt_plot = filter_bbox(dt_clean, lon_min, lon_max, lat_min, lat_max)

    print("TS plotted:", ts_plot.shape)
    print("SS plotted:", ss_plot.shape)
    print("DT plotted:", dt_plot.shape)

    # standardize edge column names
    ts_ss_edges = ts_ss_edges.rename(columns={"SsId": "SsId"}).copy()
    ss_dt_edges = ss_dt_edges.rename(columns={"SsId": "SsId", "DtId": "DtId"}).copy()
    ts_dt_edges = ts_dt_edges.rename(columns={"TsId": "TsId", "DtId": "DtId"}).copy()
    ts_dt_edges_from_feeder11 = ts_dt_edges_from_feeder11.rename(
        columns={"TsId": "TsId", "DtId": "DtId"}
    ).copy()

    # combine both TS -> DT sources
    ts_dt_edges_all = pd.concat(
        [ts_dt_edges, ts_dt_edges_from_feeder11],
        ignore_index=True
    ).drop_duplicates()

    # -----------------------
    # TS -> SS
    # -----------------------
    ts_ss_plot = ts_ss_edges[
        ts_ss_edges["TsId"].isin(ts_plot["Id"]) &
        ts_ss_edges["SsId"].isin(ss_plot["Id"])
    ].copy()

    print("TS-SS edges plotted:", ts_ss_plot.shape)

    ts_ss_plot = ts_ss_plot.merge(
        ts_plot[["Id", "Longitude", "Latitude"]].rename(columns={
            "Id": "TsId",
            "Longitude": "TS_lon",
            "Latitude": "TS_lat"
        }),
        on="TsId",
        how="inner"
    )

    ts_ss_plot = ts_ss_plot.merge(
        ss_plot[["Id", "Longitude", "Latitude"]].rename(columns={
            "Id": "SsId",
            "Longitude": "SS_lon",
            "Latitude": "SS_lat"
        }),
        on="SsId",
        how="inner"
    )

    # -----------------------
    # TS -> DT
    # -----------------------
    ts_dt_plot = ts_dt_edges_all[
        ts_dt_edges_all["TsId"].isin(ts_plot["Id"]) &
        ts_dt_edges_all["DtId"].isin(dt_plot["Id"])
    ].copy()

    print("TS-DT edges plotted:", ts_dt_plot.shape)

    ts_dt_plot = ts_dt_plot.merge(
        ts_plot[["Id", "Longitude", "Latitude"]].rename(columns={
            "Id": "TsId",
            "Longitude": "TS_lon",
            "Latitude": "TS_lat"
        }),
        on="TsId",
        how="inner"
    )

    ts_dt_plot = ts_dt_plot.merge(
        dt_plot[["Id", "Longitude", "Latitude"]].rename(columns={
            "Id": "DtId",
            "Longitude": "DT_lon",
            "Latitude": "DT_lat"
        }),
        on="DtId",
        how="inner"
    )

    # -----------------------
    # SS -> DT
    # -----------------------
    ss_dt_plot = ss_dt_edges[
        ss_dt_edges["SsId"].isin(ss_plot["Id"]) &
        ss_dt_edges["DtId"].isin(dt_plot["Id"])
    ].copy()

    print("SS-DT edges plotted:", ss_dt_plot.shape)

    ss_dt_plot = ss_dt_plot.merge(
        ss_plot[["Id", "Longitude", "Latitude"]].rename(columns={
            "Id": "SsId",
            "Longitude": "SS_lon",
            "Latitude": "SS_lat"
        }),
        on="SsId",
        how="inner"
    )

    ss_dt_plot = ss_dt_plot.merge(
        dt_plot[["Id", "Longitude", "Latitude"]].rename(columns={
            "Id": "DtId",
            "Longitude": "DT_lon",
            "Latitude": "DT_lat"
        }),
        on="DtId",
        how="inner"
    )

    plt.figure(figsize=(12, 8))

    # TS -> SS
    for _, row in ts_ss_plot.iterrows():
        plt.plot(
            [row["TS_lon"], row["SS_lon"]],
            [row["TS_lat"], row["SS_lat"]],
            color="gray",
            alpha=0.10,
            linewidth=0.4,
            zorder=1
        )

    # TS -> DT (both sources combined)
    for _, row in ts_dt_plot.iterrows():
        plt.plot(
            [row["TS_lon"], row["DT_lon"]],
            [row["TS_lat"], row["DT_lat"]],
            color="black",
            alpha=0.09,
            linewidth=0.4,
            zorder=1
        )

    # SS -> DT
    for _, row in ss_dt_plot.iterrows():
        plt.plot(
            [row["SS_lon"], row["DT_lon"]],
            [row["SS_lat"], row["DT_lat"]],
            color="red",
            alpha=0.09,
            linewidth=0.4,
            zorder=1
        )

    plt.scatter(
        dt_plot["Longitude"],
        dt_plot["Latitude"],
        label="DT",
        color="royalblue",
        s=29,
        alpha=0.08,
        linewidths=0,
        zorder=2
    )

    plt.scatter(
        ss_plot["Longitude"],
        ss_plot["Latitude"],
        label="SS",
        color='gold',
        s=77,
        alpha=0.7,
        linewidths=0,
        zorder=3
    )

    plt.scatter(
        ts_plot["Longitude"],
        ts_plot["Latitude"],
        label="TS",
        color='forestgreen',
        s=150,
        alpha=0.95,
        linewidths=0,
        zorder=4
    )

    plt.plot([], [], color="red", label="TS-SS edge")
    plt.plot([], [], color="blue", label="TS-DT edge")
    plt.plot([], [], color="green", label="SS-DT edge")

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Station Locations with TS-SS, TS-DT and SS-DT Edges (Zoomed)")
    plt.legend()
    plt.grid(True, alpha=0.2)

    plt.xlim(lon_min, lon_max)
    plt.ylim(lat_min, lat_max)

    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Plot saved to: {output_path}")
    plt.close()