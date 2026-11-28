"""Phase 5 Step 3, read-only diagnostic for BACKEND_UNAVAILABLE.

Run from the directory containing phase5/: python -m phase5.step3_diagnose
No medical text, password, URI or local paths are printed or saved.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import importlib.metadata
import json
import os
from pathlib import Path

from .step1_environment_audit import CONFIG_LOCAL, _safe_config
from .step3_knowledge_integration import (
    CHROMA_COLLECTION,
    CHROMA_SNAPSHOT_SHA256,
    EXPECTED_COUNTS,
    EXPECTED_MODEL_ID,
    NEO4J_AUDIT_CYPHER,
    validate_database,
    validate_neo4j_uri,
)

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'data' / 'outputs' / 'phase5_step3' / 'step3_backend_diagnostic.json'


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description='Read-only diagnosis for Phase 5 Step 3')
    parser.add_argument('--config', type=Path, default=CONFIG_LOCAL)
    parser.add_argument('--output', type=Path, default=REPORT)
    args = parser.parse_args()
    results: dict[str, dict[str, str]] = {}

    def put(stage: str, status: str, error_type: str | None = None):
        results[stage] = {'status': status}
        if error_type:
            results[stage]['exception_type'] = error_type
        print(f'{stage}: {status}' + (f' ({error_type})' if error_type else ''))

    try:
        cfg = _safe_config(json.loads(args.config.read_text(encoding='utf-8')))
        path = cfg.get('chroma_persist_dir')
        uri = cfg.get('neo4j_uri')
        db = cfg.get('neo4j_database')
        if not path or not uri or not db:
            raise ValueError('Required connection settings are missing')
        chroma_path = Path(path).expanduser()
        if not chroma_path.is_absolute():
            chroma_path = ROOT / chroma_path
        validate_neo4j_uri(uri)
        validate_database(db)
        if cfg.get('chroma_collection') != CHROMA_COLLECTION:
            raise ValueError('Unexpected collection name in config')
        put('CONFIG', 'PASS')
    except Exception as e:
        put('CONFIG', 'FAIL', type(e).__name__)
        return 2

    chroma_files_present = chroma_path.is_dir() and (chroma_path / 'chroma.sqlite3').is_file()
    if chroma_files_present:
        put('CHROMA_FILES', 'PASS')
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(chroma_path))
            col = client.get_collection(CHROMA_COLLECTION)
            metadata = col.metadata or {}
            if col.count() != 66:
                put('CHROMA_COLLECTION', 'FAIL_COUNT_MISMATCH')
            elif metadata.get('source_snapshot') != CHROMA_SNAPSHOT_SHA256 or metadata.get('model_id') != EXPECTED_MODEL_ID:
                put('CHROMA_COLLECTION', 'FAIL_METADATA_MISMATCH')
            else:
                put('CHROMA_COLLECTION', 'PASS_66_AND_METADATA')
        except ImportError as e:
            put('CHROMA_COLLECTION', 'FAIL_MISSING_LIBRARY', type(e).__name__)
        except Exception as e:
            put('CHROMA_COLLECTION', 'FAIL_OPEN', type(e).__name__)
    else:
        put('CHROMA_FILES', 'FAIL_MISSING_DATABASE')
        put('CHROMA_COLLECTION', 'SKIPPED_MISSING_DATABASE')

    username = os.environ.get('NEO4J_USERNAME', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD') or getpass.getpass('Neo4j password (hidden): ')
    if not password:
        put('NEO4J_CONNECT', 'FAIL_MISSING_PASSWORD')
    else:
        driver = None
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(uri, auth=(username, password), connection_timeout=15)
            driver.verify_connectivity()
            put('NEO4J_CONNECT', 'PASS')
            try:
                with driver.session(database=db) as session:
                    rows = session.execute_read(lambda tx: tx.run(NEO4J_AUDIT_CYPHER).data())
                if len(rows) != 1:
                    put('NEO4J_AUDIT', 'FAIL_UNEXPECTED_ROWS')
                elif all(type(rows[0].get(k)) is int and rows[0][k] == v for k, v in EXPECTED_COUNTS.items()):
                    put('NEO4J_AUDIT', 'PASS_EXPECTED_COUNTS')
                else:
                    put('NEO4J_AUDIT', 'FAIL_GRAPH_COUNTS_CHANGED')
            except Exception as e:
                put('NEO4J_AUDIT', 'FAIL_QUERY', type(e).__name__)
        except ImportError as e:
            put('NEO4J_CONNECT', 'FAIL_MISSING_LIBRARY', type(e).__name__)
        except Exception as e:
            put('NEO4J_CONNECT', 'FAIL_CONNECT', type(e).__name__)
        finally:
            if driver:
                driver.close()

    try:
        from sentence_transformers import SentenceTransformer
        encoder = SentenceTransformer(EXPECTED_MODEL_ID, local_files_only=True)
        _ = encoder.get_sentence_embedding_dimension()
        put('EMBEDDING_LOCAL_CACHE', 'PASS')
    except ImportError as e:
        put('EMBEDDING_LOCAL_CACHE', 'FAIL_MISSING_LIBRARY', type(e).__name__)
    except Exception as e:
        put('EMBEDDING_LOCAL_CACHE', 'FAIL_LOAD', type(e).__name__)

    report = {
        'experiment': 'EXP-PHASE5-STEP3-DIAG-001',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'steps': results,
        'package_versions': {
            k: package_version(k) for k in ('chromadb', 'neo4j', 'sentence-transformers', 'transformers', 'torch')
        },
        'clinical_answers_generated': False,
        'llm_called': False,
        'model_retrained': False,
        'application_db_writes': False,
        'contains_secrets': False,
        'note': 'Read-only client calls; local libraries may create housekeeping/cache files.',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Saved diagnostic report:', args.output)
    return 0 if all(v['status'].startswith('PASS') for v in results.values()) else 2


if __name__ == '__main__':
    raise SystemExit(main())
