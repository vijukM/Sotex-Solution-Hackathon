# client.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import requests


class PowerGraphClientError(Exception):
    """Greška pri komunikaciji sa power-graph servisom."""


class PowerGraphClient:
    """
    Klijent koji backend koristi da komunicira sa Python servisom.

    Očekivani endpointi na servisu:
    - GET  /health
    - GET  /summary
    - GET  /analysis/vulnerable-nodes?top_k=5
    - GET  /visualizations
    - GET  /visualizations/stations-plot
    - GET  /visualizations/ss-dt-plot

    Ako odlučiš drugačije da nazoveš endpoint-e u service.py,
    samo promeni putanje u ovom client-u.
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> Any:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise PowerGraphClientError(
                f"HTTP {response.status_code} greška za {response.request.method} "
                f"{response.url}: {response.text[:500]}"
            ) from exc

        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            try:
                return response.json()
            except ValueError as exc:
                raise PowerGraphClientError(
                    f"Servis nije vratio validan JSON za {response.url}"
                ) from exc

        return response

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = self.session.get(
                self._url(path),
                params=params,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise PowerGraphClientError(
                f"Nije moguće povezati se sa servisom na {self._url(path)}"
            ) from exc

        return self._handle_response(response)

    # ---------------------------------------------------------
    # Osnovne informacije
    # ---------------------------------------------------------

    def health(self) -> Dict[str, Any]:
        """
        Provera da li je servis dostupan.
        """
        result = self._get("/health")
        if not isinstance(result, dict):
            raise PowerGraphClientError("Neočekivan odgovor sa /health")
        return result

    def summary(self) -> Dict[str, Any]:
        """
        Opšti summary grafa:
        broj čvorova, broj grana, count po tipovima...
        """
        result = self._get("/summary")
        if not isinstance(result, dict):
            raise PowerGraphClientError("Neočekivan odgovor sa /summary")
        return result

    # ---------------------------------------------------------
    # Najranjiviji čvorovi
    # ---------------------------------------------------------

    def vulnerable_nodes(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Vraća najranjivije čvorove sa koordinatama i metapodacima.

        Očekivani JSON format od servisa:
        {
            "top_k": 5,
            "nodes": [
                {
                    "rank": 1,
                    "node": ["SS", 123],
                    "name": "...",
                    "node_type": "SS",
                    "original_id": 123,
                    "latitude": ...,
                    "longitude": ...,
                    "degree": ...,
                    "damage_score": ...,
                    "largest_component_drop": ...
                }
            ]
        }
        """
        result = self._get("/analysis/vulnerable-nodes", params={"top_k": top_k})

        if not isinstance(result, dict):
            raise PowerGraphClientError("Neočekivan odgovor sa /analysis/vulnerable-nodes")

        nodes = result.get("nodes")
        if not isinstance(nodes, list):
            raise PowerGraphClientError("Polje 'nodes' nedostaje ili nije lista")

        return nodes

    def vulnerable_nodes_coordinates(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Pogodno za backend/frontend ako trebaju samo podaci za mapu.
        """
        nodes = self.vulnerable_nodes(top_k=top_k)

        simplified: List[Dict[str, Any]] = []
        for item in nodes:
            simplified.append(
                {
                    "rank": item.get("rank"),
                    "name": item.get("name"),
                    "node_type": item.get("node_type"),
                    "original_id": item.get("original_id"),
                    "latitude": item.get("latitude"),
                    "longitude": item.get("longitude"),
                }
            )

        return simplified

    # ---------------------------------------------------------
    # Vizuelizacije
    # ---------------------------------------------------------

    def visualizations(self) -> Dict[str, Any]:
        """
        Očekivani JSON od servisa:
        {
            "stations_plot_url": "http://localhost:8000/visualizations/stations-plot",
            "ss_dt_plot_url": "http://localhost:8000/visualizations/ss-dt-plot",
            "stations_plot_path": "...",
            "ss_dt_plot_path": "..."
        }
        """
        result = self._get("/visualizations")
        if not isinstance(result, dict):
            raise PowerGraphClientError("Neočekivan odgovor sa /visualizations")
        return result

    def download_stations_plot(self, save_to: str | Path) -> Path:
        """
        Skida glavnu vizualizaciju sa TS/SS/DT.
        """
        path = Path(save_to)
        response = self._get("/visualizations/stations-plot")

        if not isinstance(response, requests.Response):
            raise PowerGraphClientError("Očekivan binarni odgovor za stations plot")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
        return path

    def download_ss_dt_plot(self, save_to: str | Path) -> Path:
        """
        Skida SS-DT vizualizaciju bez TS.
        """
        path = Path(save_to)
        response = self._get("/visualizations/ss-dt-plot")

        if not isinstance(response, requests.Response):
            raise PowerGraphClientError("Očekivan binarni odgovor za ss-dt plot")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response.content)
        return path


if __name__ == "__main__":
    client = PowerGraphClient(base_url="http://localhost:8000")

    try:
        print("=== HEALTH ===")
        print(client.health())

        print("\n=== SUMMARY ===")
        print(client.summary())

        print("\n=== TOP 5 VULNERABLE NODES ===")
        vulnerable = client.vulnerable_nodes(top_k=5)
        for node in vulnerable:
            print(node)

        print("\n=== ONLY COORDINATES FOR MAP ===")
        print(client.vulnerable_nodes_coordinates(top_k=5))

        print("\n=== VISUALIZATION INFO ===")
        print(client.visualizations())

        stations_file = client.download_stations_plot("downloads/stations_plot.png")
        ss_dt_file = client.download_ss_dt_plot("downloads/ss_dt_plot.png")

        print("\nDownloaded:")
        print(stations_file.resolve())
        print(ss_dt_file.resolve())

    except PowerGraphClientError as exc:
        print(f"Greška: {exc}")