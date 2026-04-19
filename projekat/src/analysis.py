import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

import networkx as nx


def analyze_graph(G: nx.DiGraph):
    G_und = G.to_undirected()

    components = list(nx.connected_components(G_und))
    print("Broj komponenti:", len(components))
    print("Veličine komponenti:", sorted([len(c) for c in components], reverse=True)[:10])

    art_points = list(nx.articulation_points(G_und))
    print("Articulation points:", len(art_points))
    print(art_points[:20])

    non_ts_art_points = [
        node for node in art_points
        if G_und.nodes[node].get("node_type") != "TS"
    ]

    print("Non-TS articulation points:", len(non_ts_art_points))
    print(non_ts_art_points[:20])

    return {
        "G_und": G_und,
        "components": components,
        "articulation_points": art_points,
        "non_ts_articulation_points": non_ts_art_points,
    }


def damage_score_by_removal_fast(G_und: nx.Graph):
    base_num_components = nx.number_connected_components(G_und)

    articulation_points = [
        node for node in nx.articulation_points(G_und)
        if G_und.nodes[node].get("node_type") != "TS"
    ]

    scores = []

    for node in articulation_points:
        H_tmp = G_und.copy()
        H_tmp.remove_node(node)
        new_num_components = nx.number_connected_components(H_tmp)
        increase = new_num_components - base_num_components
        scores.append((node, increase))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def shortlist_non_ts_articulation_points(G_und: nx.Graph, top_k: int = 30):
    art_points = list(nx.articulation_points(G_und))
    non_ts_art_points = [
        n for n in art_points
        if G_und.nodes[n].get("node_type") != "TS"
    ]

    bc = nx.betweenness_centrality(G_und)
    ranked = sorted(non_ts_art_points, key=lambda n: bc[n], reverse=True)
    return ranked[:top_k]


def rank_shortlisted_nodes_by_damage(G_und: nx.Graph, candidate_nodes):
    base_components = list(nx.connected_components(G_und))
    base_num_components = len(base_components)
    base_largest_component = max(len(c) for c in base_components)

    results = []

    for node in candidate_nodes:
        H_tmp = G_und.copy()
        H_tmp.remove_node(node)

        new_components = list(nx.connected_components(H_tmp))
        new_num_components = len(new_components)
        new_largest_component = max(len(c) for c in new_components) if new_components else 0

        results.append({
            "node": node,
            "node_type": G_und.nodes[node].get("node_type"),
            "damage_score": new_num_components - base_num_components,
            "largest_component_drop": base_largest_component - new_largest_component,
        })

    results.sort(
        key=lambda x: (x["largest_component_drop"], x["damage_score"]),
        reverse=True
    )
    return results