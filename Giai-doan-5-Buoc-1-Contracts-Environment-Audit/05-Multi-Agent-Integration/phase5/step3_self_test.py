"""Local Step 3 tests. No LangGraph, Neo4j, Chroma, network, LLM or DB needed."""
from __future__ import annotations

import unittest
from pydantic import ValidationError
from .contracts import EvidenceMetadata
from .step3_knowledge_integration import (
    EXPECTED_COUNTS, MockKnowledgeBackend, KnowledgeIntegrationFailure,
    project_evidence, validate_audit, validate_database, validate_neo4j_uri,
)


class Step3Tests(unittest.TestCase):
    def setUp(self):
        self.backend = MockKnowledgeBackend()

    def test_mock_audit(self):
        self.assertTrue(validate_audit(self.backend.audit()))

    def test_mock_three_queries(self):
        for q in ("Q01", "Q02", "Q03"):
            out = project_evidence(self.backend.retrieve(q))
            self.assertEqual(len(out), 3)
            self.assertTrue(all(not x.allowed_to_answer for x in out))

    def test_invalid_query_id(self):
        with self.assertRaises(KnowledgeIntegrationFailure):
            self.backend.retrieve("ANYTHING_ELSE")

    def test_neo4j_schemes_require_tls(self):
        for uri in ("bolt://localhost:7687", "http://console.neo4j.io/", "neo4j://db.invalid"):
            with self.assertRaises(KnowledgeIntegrationFailure):
                validate_neo4j_uri(uri)

    def test_uri_cannot_embed_credentials(self):
        with self.assertRaises(KnowledgeIntegrationFailure):
            validate_neo4j_uri("neo4j+s://alice:secret@abc.databases.neo4j.io")

    def test_valid_neo4j_uri(self):
        self.assertEqual(validate_neo4j_uri("neo4j+s://abc.databases.neo4j.io"),
                         "neo4j+s://abc.databases.neo4j.io")

    def test_database_name(self):
        self.assertEqual(validate_database("neo4j"), "neo4j")
        with self.assertRaises(KnowledgeIntegrationFailure):
            validate_database("x/../../example")

    def test_approved_claim_change_blocks(self):
        bad = dict(EXPECTED_COUNTS, approved_claims=1)
        with self.assertRaises(KnowledgeIntegrationFailure):
            validate_audit(bad)

    def test_provenance_tamper_blocks(self):
        with self.assertRaises(KnowledgeIntegrationFailure) as ctx:
            project_evidence(MockKnowledgeBackend("provenance").retrieve("Q01"))
        self.assertEqual(ctx.exception.code, "PROVENANCE_MISMATCH")

    def test_missing_hit_blocks(self):
        with self.assertRaises(KnowledgeIntegrationFailure):
            project_evidence(MockKnowledgeBackend("missing").retrieve("Q01"))

    def test_duplicate_hit_blocks(self):
        with self.assertRaises(KnowledgeIntegrationFailure):
            project_evidence(MockKnowledgeBackend("duplicate").retrieve("Q01"))

    def test_gate_cannot_be_set_true(self):
        hit = project_evidence(self.backend.retrieve("Q01"))[0]
        with self.assertRaises(ValidationError):
            EvidenceMetadata.model_validate(dict(hit.model_dump(), allowed_to_answer=True))

    def test_no_text_in_state_projection(self):
        raw = self.backend.retrieve("Q01")
        raw[0]["document_text"] = "MOCK TEXT NOT ALLOWED TO REACH AGENT"
        evidence = project_evidence(raw)
        self.assertNotIn("document_text", evidence[0].model_dump())

    def test_wrong_rank_blocks(self):
        bad = self.backend.retrieve("Q01")
        bad[0]["rank"] = 99
        with self.assertRaises(KnowledgeIntegrationFailure):
            project_evidence(bad)

    def test_incorrect_url_blocks(self):
        bad = self.backend.retrieve("Q01")
        bad[0]["source_url"] = "http://example.invalid"
        with self.assertRaises(KnowledgeIntegrationFailure):
            project_evidence(bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
