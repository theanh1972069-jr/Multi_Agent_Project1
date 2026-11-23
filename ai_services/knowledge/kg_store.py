from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from ai_services.knowledge.kg_seed import write_curated_kg
from ai_services.knowledge.rag_store import extract_content_tokens, fold_text

_WORD_BOUNDARY_CACHE: dict[str, re.Pattern[str]] = {}


class KGRelation(BaseModel):
    """Typed medical relation returned from Neo4j or local Diabetes KG mirror."""

    source_node: str
    source_type: str
    relation: str
    target_node: str
    target_type: str
    source_ids: list[str]
    description: str


def _contains_phrase(folded_text: str, phrase: str) -> bool:
    pattern = _WORD_BOUNDARY_CACHE.get(phrase)
    if pattern is None:
        escaped = re.escape(phrase)
        pattern = re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")
        _WORD_BOUNDARY_CACHE[phrase] = pattern
    return bool(pattern.search(folded_text))


class DiabetesKGStore:
    """Resilient Knowledge Graph store with optional Neo4j read-only query and JSON mirror fallback."""

    def __init__(
        self,
        kg_mirror_path: Path,
        *,
        neo4j_uri: str | None = None,
        neo4j_username: str | None = None,
        neo4j_password: str | None = None,
        neo4j_database: str | None = None,
    ) -> None:
        self.kg_mirror_path = Path(kg_mirror_path)
        self.neo4j_uri = (neo4j_uri or "").strip() or None
        self.neo4j_username = (neo4j_username or "").strip() or None
        self.neo4j_password = (neo4j_password or "").strip() or None
        self.neo4j_database = (neo4j_database or "").strip() or None

        if not self.kg_mirror_path.exists():
            self._mirror_data = write_curated_kg(self.kg_mirror_path)
        else:
            self._mirror_data = json.loads(self.kg_mirror_path.read_text(encoding="utf-8"))

    def known_source_ids(self) -> set[str]:
        return {str(s["source_id"]) for s in self._mirror_data.get("sources", [])}

    def _create_neo4j_driver(self) -> Any | None:
        if not (self.neo4j_uri and self.neo4j_username and self.neo4j_password):
            return None
        try:
            from neo4j import GraphDatabase
        except ImportError:
            return None

        return GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_username, self.neo4j_password),
            connection_timeout=2.0,
            max_transaction_retry_time=2.0,
        )

    def _read_from_neo4j(self) -> dict | None:
        driver = self._create_neo4j_driver()
        if driver is None:
            return None

        def _fetch_graph(tx: Any) -> dict:
            node_rows = list(
                tx.run(
                    "MATCH (n:DiabetesEntity) "
                    "RETURN n.id AS id, n.label AS label, n.type AS type, "
                    "coalesce(n.source_ids, []) AS source_ids, "
                    "coalesce(n.keywords, []) AS keywords, "
                    "coalesce(n.description, '') AS description"
                )
            )
            edge_rows = list(
                tx.run(
                    "MATCH (a:DiabetesEntity)-[r]->(b:DiabetesEntity) "
                    "RETURN a.id AS source, b.id AS target, type(r) AS relation, "
                    "coalesce(r.source_ids, []) AS source_ids, "
                    "coalesce(r.description, '') AS description"
                )
            )
            return {
                "nodes": [dict(row) for row in node_rows],
                "edges": [dict(row) for row in edge_rows],
            }

        try:
            session_kwargs: dict[str, Any] = {}
            if self.neo4j_database:
                session_kwargs["database"] = self.neo4j_database
            with driver.session(**session_kwargs) as session:
                graph = session.execute_read(_fetch_graph)
            if not graph.get("nodes"):
                return None
            return graph
        except Exception:
            return None
        finally:
            try:
                driver.close()
            except Exception:
                pass

    def sync_to_neo4j(self) -> bool:
        """Optionally push the curated local mirror graph into Neo4j."""
        driver = self._create_neo4j_driver()
        if driver is None:
            return False

        def _merge_graph(tx: Any, nodes: list[dict], edges: list[dict]) -> None:
            for node in nodes:
                tx.run(
                    "MERGE (n:DiabetesEntity {id: $id}) "
                    "SET n.label = $label, n.type = $type, n.source_ids = $source_ids, "
                    "n.keywords = $keywords, n.description = $description",
                    id=node["id"],
                    label=node["label"],
                    type=node["type"],
                    source_ids=node.get("source_ids", []),
                    keywords=node.get("keywords", []),
                    description=node.get("description", ""),
                )
            for edge in edges:
                rel_type = re.sub(r"[^A-Z0-9_]", "_", str(edge["relation"]).upper())
                tx.run(
                    f"MATCH (a:DiabetesEntity {{id: $source}}), (b:DiabetesEntity {{id: $target}}) "
                    f"MERGE (a)-[r:{rel_type}]->(b) "
                    "SET r.source_ids = $source_ids, r.description = $description",
                    source=edge["source"],
                    target=edge["target"],
                    source_ids=edge.get("source_ids", []),
                    description=edge.get("description", ""),
                )

        try:
            session_kwargs: dict[str, Any] = {}
            if self.neo4j_database:
                session_kwargs["database"] = self.neo4j_database
            with driver.session(**session_kwargs) as session:
                session.execute_write(
                    _merge_graph,
                    self._mirror_data.get("nodes", []),
                    self._mirror_data.get("edges", []),
                )
            return True
        except Exception:
            return False
        finally:
            try:
                driver.close()
            except Exception:
                pass

    def health_check(self) -> dict[str, Any]:
        configured = bool(self.neo4j_uri and self.neo4j_username and self.neo4j_password)
        neo_reachable = False
        if configured:
            driver = self._create_neo4j_driver()
            if driver is not None:
                try:
                    driver.verify_connectivity()
                    neo_reachable = True
                except Exception:
                    neo_reachable = False
                finally:
                    try:
                        driver.close()
                    except Exception:
                        pass
        return {
            "neo4j_configured": configured,
            "neo4j_reachable": neo_reachable,
            "kg_source": "neo4j" if neo_reachable else "local_mirror",
            "node_count": len(self._mirror_data.get("nodes", [])),
            "edge_count": len(self._mirror_data.get("edges", [])),
        }

    def _filter_graph(
        self,
        raw_graph: dict,
        active_source_ids: set[str] | None,
    ) -> tuple[list[dict], list[dict]]:
        nodes: list[dict] = []
        active_node_ids: set[str] = set()

        for node in raw_graph.get("nodes", []):
            node_sids = list(node.get("source_ids") or [])
            if active_source_ids is not None:
                filtered_sids = [sid for sid in node_sids if sid in active_source_ids]
                if not filtered_sids:
                    continue
            else:
                filtered_sids = node_sids

            node_copy = dict(node)
            node_copy["source_ids"] = filtered_sids
            nodes.append(node_copy)
            active_node_ids.add(str(node_copy["id"]))

        edges: list[dict] = []
        for edge in raw_graph.get("edges", []):
            if str(edge.get("source")) not in active_node_ids or str(edge.get("target")) not in active_node_ids:
                continue
            edge_sids = list(edge.get("source_ids") or [])
            if active_source_ids is not None:
                filtered_sids = [sid for sid in edge_sids if sid in active_source_ids]
                if not filtered_sids:
                    continue
            else:
                filtered_sids = edge_sids

            edge_copy = dict(edge)
            edge_copy["source_ids"] = filtered_sids
            edges.append(edge_copy)

        return nodes, edges

    def get_graph_payload(self, active_source_ids: set[str] | None = None) -> dict:
        """Return filtered KG nodes and edges from Neo4j (read-only) or local mirror."""
        neo_graph = self._read_from_neo4j()
        if neo_graph is not None:
            kg_source: Literal["neo4j", "local_mirror"] = "neo4j"
            raw_graph = neo_graph
        else:
            kg_source = "local_mirror"
            raw_graph = self._mirror_data

        nodes, edges = self._filter_graph(raw_graph, active_source_ids)
        return {
            "nodes": nodes,
            "edges": edges,
            "kg_source": kg_source,
        }

    def _score_node(self, node: dict, folded_query: str, query_tokens: set[str]) -> float:
        score = 0.0
        for kw in node.get("keywords") or []:
            folded_kw = fold_text(str(kw))
            if not folded_kw:
                continue
            if _contains_phrase(folded_query, folded_kw):
                score += 3.0 if " " in folded_kw else 2.0

        label_tokens = set(extract_content_tokens(str(node.get("label", ""))))
        overlap = query_tokens & label_tokens
        if overlap:
            score += 1.5 * len(overlap)
        return score

    def query_relations(
        self,
        query: str,
        *,
        active_source_ids: set[str] | None = None,
        limit: int = 8,
    ) -> tuple[list[KGRelation], Literal["neo4j", "local_mirror"]]:
        """Match relevant KG relations for a query, respecting `active_source_ids`."""
        payload = self.get_graph_payload(active_source_ids=active_source_ids)
        kg_source: Literal["neo4j", "local_mirror"] = payload["kg_source"]
        nodes_by_id = {str(n["id"]): n for n in payload["nodes"]}
        edges = payload["edges"]

        folded_query = fold_text(query)
        query_tokens = set(extract_content_tokens(query))
        if not query_tokens:
            return [], kg_source

        node_scores = {
            nid: self._score_node(node, folded_query, query_tokens)
            for nid, node in nodes_by_id.items()
        }

        scored_edges: list[tuple[float, dict]] = []
        for edge in edges:
            if edge.get("relation") == "SUPPORTED_BY":
                continue
            src_id = str(edge["source"])
            tgt_id = str(edge["target"])
            edge_tokens = set(extract_content_tokens(str(edge.get("description", ""))))
            desc_overlap = len(query_tokens & edge_tokens)
            total_score = node_scores.get(src_id, 0.0) + node_scores.get(tgt_id, 0.0) + 0.5 * desc_overlap
            if total_score >= 1.5:
                scored_edges.append((total_score, edge))

        scored_edges.sort(key=lambda item: item[0], reverse=True)
        relations: list[KGRelation] = []
        for _, edge in scored_edges[:limit]:
            src_node = nodes_by_id[str(edge["source"])]
            tgt_node = nodes_by_id[str(edge["target"])]
            relations.append(
                KGRelation(
                    source_node=str(src_node["label"]),
                    source_type=str(src_node["type"]),
                    relation=str(edge["relation"]),
                    target_node=str(tgt_node["label"]),
                    target_type=str(tgt_node["type"]),
                    source_ids=list(edge.get("source_ids") or []),
                    description=str(edge.get("description") or ""),
                )
            )
        return relations, kg_source
