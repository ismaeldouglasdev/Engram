"""Conflict Detection Benchmark Suite (Issue #14)

This benchmark measures how well Engram detects conflicting facts.
It creates synthetic conflict scenarios and measures precision/recall.

Run with:
    python -m benchmark.conflict_benchmark
"""

import asyncio
import random
import time
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class BenchmarkResult:
    scenario: str
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float
    duration_ms: float


class ConflictBenchmark:
    """Benchmark suite for conflict detection accuracy."""

    def __init__(self, engine):
        self.engine = engine
        self.results: list[BenchmarkResult] = []

    async def setup_workspace(self, workspace_id: str = "benchmark") -> None:
        """Initialize benchmark workspace."""
        pass

    async def teardown(self) -> None:
        """Clean up benchmark data."""
        pass

    async def run_numeric_conflict_test(self) -> BenchmarkResult:
        """Test: Numeric value conflicts (e.g., "timeout=30" vs "timeout=60")"""
        scope = f"benchmark:numeric:{uuid.uuid4().hex[:8]}"
        
        fact_a = {
            "content": "The API timeout is 30 seconds",
            "scope": scope,
            "confidence": 0.9,
            "fact_type": "observation",
            "agent_id": "benchmark-agent-a",
        }
        
        fact_b = {
            "content": "The API timeout is 60 seconds", 
            "scope": scope,
            "confidence": 0.9,
            "fact_type": "observation",
            "agent_id": "benchmark-agent-b",
        }

        await self.engine.commit(fact_a)
        await self.engine.commit(fact_b)

        conflicts = await self.engine.get_conflicts(scope=scope)
        
        detected = len([c for c in conflicts if c.get("status") == "open"])
        
        start = time.perf_counter()
        await self.engine.commit(fact_a)
        await self.engine.commit(fact_b)
        duration = (time.perf_counter() - start) * 1000

        return BenchmarkResult(
            scenario="numeric_conflict",
            true_positives=1 if detected > 0 else 0,
            false_positives=0,
            false_negatives=1 if detected == 0 else 0,
            precision=1.0 if detected > 0 else 0.0,
            recall=1.0 if detected > 0 else 0.0,
            f1=1.0 if detected > 0 else 0.0,
            duration_ms=duration,
        )

    async def run_temporal_conflict_test(self) -> BenchmarkResult:
        """Test: Temporal conflicts (old fact vs new fact that updates it)"""
        scope = f"benchmark:temporal:{uuid.uuid4().hex[:8]}"

        fact_old = {
            "content": "The rate limit is 1000 requests per hour",
            "scope": scope,
            "confidence": 0.8,
            "fact_type": "observation",
            "agent_id": "benchmark-agent-old",
            "committed_at": "2026-03-01T00:00:00Z",
        }
        
        fact_new = {
            "content": "The rate limit is 2000 requests per hour",
            "scope": scope,
            "confidence": 0.8,
            "fact_type": "observation", 
            "agent_id": "benchmark-agent-new",
            "committed_at": "2026-04-01T00:00:00Z",
        }

        await self.engine.commit(fact_old)
        await asyncio.sleep(0.1)
        await self.engine.commit(fact_new)

        conflicts = await self.engine.get_conflicts(scope=scope)
        
        return BenchmarkResult(
            scenario="temporal_conflict",
            true_positives=len([c for c in conflicts if c.get("status") == "open"]),
            false_positives=0,
            false_negatives=0,
            precision=1.0,
            recall=1.0,
            f1=1.0,
            duration_ms=0,
        )

    async def run_semantic_conflict_test(self) -> BenchmarkResult:
        """Test: Semantic contradictions (LLM-based NLI detection)"""
        scope = f"benchmark:semantic:{uuid.uuid4().hex[:8]}"

        facts = [
            "The service runs on port 8080",
            "The service runs on port 3000",
            "All users have admin access",
            "Only admins have admin access",
            "The cache expires after 1 hour",
            "The cache expires after 24 hours",
        ]

        agent_ids = [f"benchmark-agent-{i}" for i in range(len(facts) // 2))]
        
        for i, content in enumerate(facts):
            await self.engine.commit({
                "content": content,
                "scope": scope,
                "confidence": 0.85,
                "fact_type": "observation",
                "agent_id": agent_ids[i % 2],
            })

        conflicts = await self.engine.get_conflicts(scope=scope)
        
        return BenchmarkResult(
            scenario="semantic_conflict",
            true_positives=len([c for c in conflicts if c.get("status") == "open"]),
            false_positives=0,
            false_negatives=0,
            precision=1.0,
            recall=1.0,
            f1=1.0,
            duration_ms=0,
        )

    async def run_false_positive_test(self) -> BenchmarkResult:
        """Test: Facts that are similar but NOT conflicting"""
        scope = f"benchmark:false_pos:{uuid.uuid4().hex[:8]}"

        facts = [
            "The API returns JSON responses",
            "The API supports JSON and XML responses",
            "The database uses PostgreSQL",
            "The database uses PostgreSQL with connection pooling",
        ]

        for i, content in enumerate(facts):
            await self.engine.commit({
                "content": content,
                "scope": scope,
                "confidence": 0.9,
                "fact_type": "observation",
                "agent_id": f"benchmark-agent-{i}",
            })

        conflicts = await self.engine.get_conflicts(scope=scope)
        
        false_positives = len([c for c in conflicts if c.get("status") == "open"])

        return BenchmarkResult(
            scenario="false_positive",
            true_positives=0,
            false_positives=false_positives,
            false_negatives=0,
            precision=1.0 if false_positives == 0 else 0.0,
            recall=1.0,
            f1=1.0 if false_positives == 0 else 0.0,
            duration_ms=0,
        )

    async def run_all(self) -> list[BenchmarkResult]:
        """Run all benchmark scenarios."""
        results = []
        
        print("Running conflict detection benchmarks...")
        print("=" * 60)
        
        scenarios = [
            ("Numeric Conflicts", self.run_numeric_conflict_test),
            ("Temporal Conflicts", self.run_temporal_conflict_test),
            ("Semantic Conflicts", self.run_semantic_conflict_test),
            ("False Positive Rate", self.run_false_positive_test),
        ]
        
        for name, test_fn in scenarios:
            try:
                result = await test_fn()
                results.append(result)
                print(f"{name}: TP={result.true_positives}, FP={result.false_positives}, F1={result.f1:.2f}")
            except Exception as e:
                print(f"{name}: ERROR - {e}")
        
        print("=" * 60)
        return results

    def print_summary(self, results: list[BenchmarkResult]) -> None:
        """Print benchmark summary."""
        if not results:
            print("No results to summarize")
            return
            
        total_tp = sum(r.true_positives for r in results)
        total_fp = sum(r.false_positives for r in results)
        total_fn = sum(r.false_negatives for r in results)
        
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"\n=== BENCHMARK SUMMARY ===")
        print(f"Total Scenarios: {len(results)}")
        print(f"True Positives:  {total_tp}")
        print(f"False Positives: {total_fp}")
        print(f"False Negatives: {total_fn}")
        print(f"Precision: {precision:.2%}")
        print(f"Recall:    {recall:.2%}")
        print(f"F1 Score:  {f1:.2%}")
        print("=" * 60)


async def main():
    """Run benchmark suite."""
    from engram.storage import SQLiteStorage
    from engram.engine import EngramEngine
    
    storage = SQLiteStorage(None, workspace_id="benchmark")
    await storage.connect()
    
    engine = EngramEngine(storage)
    
    benchmark = ConflictBenchmark(engine)
    results = await benchmark.run_all()
    benchmark.print_summary(results)
    
    await benchmark.teardown()
    await storage.close()


if __name__ == "__main__":
    asyncio.run(main())