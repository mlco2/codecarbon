from contextlib import AbstractContextManager
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from dependency_injector.providers import Callable
from fastapi import HTTPException

from carbonserver.api.domain.model_benchmarks import ModelBenchmarks
from carbonserver.api.infra.database import sql_models
from carbonserver.api.schemas import ModelBenchmark, ModelBenchmarkBase

"""
Storage for published LLM energy benchmarks.

The table is standalone rather than hanging off a run — see the docstring on
``sql_models.ModelBenchmark`` for why.
"""


class SqlAlchemyRepository(ModelBenchmarks):
    def __init__(self, session_factory) -> Callable[..., AbstractContextManager]:
        self.session_factory = session_factory

    def add_benchmark(
        self,
        record: dict,
        extracted: ModelBenchmarkBase,
        submitted_by: Optional[UUID],
    ) -> UUID:
        """Store a submitted record."""
        with self.session_factory() as session:
            db_benchmark = sql_models.ModelBenchmark(
                id=uuid4(),
                submitted_at=datetime.now(timezone.utc),
                submitted_by=submitted_by,
                record=record,
                **extracted.model_dump(),
            )
            session.add(db_benchmark)
            session.commit()
            return db_benchmark.id

    def get_one_benchmark(self, benchmark_id: UUID) -> ModelBenchmark:
        with self.session_factory() as session:
            benchmark = (
                session.query(sql_models.ModelBenchmark)
                .filter(sql_models.ModelBenchmark.id == benchmark_id)
                .first()
            )
            if benchmark is None:
                raise HTTPException(
                    status_code=404, detail=f"Benchmark {benchmark_id} not found"
                )
            return self.map_sql_to_schema(benchmark)

    def list_benchmarks(
        self,
        model_name: Optional[str] = None,
        concurrency: Optional[int] = None,
        gpu_model: Optional[str] = None,
        deployment_id: Optional[str] = None,
    ) -> List[ModelBenchmark]:
        with self.session_factory() as session:
            query = session.query(sql_models.ModelBenchmark)
            if model_name is not None:
                query = query.filter(sql_models.ModelBenchmark.model_name == model_name)
            if concurrency is not None:
                query = query.filter(
                    sql_models.ModelBenchmark.concurrency == concurrency
                )
            if gpu_model is not None:
                query = query.filter(sql_models.ModelBenchmark.gpu_model == gpu_model)
            if deployment_id is not None:
                query = query.filter(
                    sql_models.ModelBenchmark.deployment_id == deployment_id
                )
            query = query.order_by(sql_models.ModelBenchmark.submitted_at.desc())
            return [self.map_sql_to_schema(b) for b in query]

    @staticmethod
    def map_sql_to_schema(benchmark: sql_models.ModelBenchmark) -> ModelBenchmark:
        return ModelBenchmark(
            id=benchmark.id,
            submitted_at=benchmark.submitted_at,
            submitted_by=benchmark.submitted_by,
            spec_version=benchmark.spec_version,
            model_name=benchmark.model_name,
            model_revision=benchmark.model_revision,
            quantization=benchmark.quantization,
            engine=benchmark.engine,
            engine_version=benchmark.engine_version,
            deployment_id=benchmark.deployment_id,
            deployment_label=benchmark.deployment_label,
            concurrency=benchmark.concurrency,
            input_token_bucket=benchmark.input_token_bucket,
            gpu_model=benchmark.gpu_model,
            gpu_count=benchmark.gpu_count,
            infra_type=benchmark.infra_type,
            duration=benchmark.duration,
            it_energy_kwh=benchmark.it_energy_kwh,
            input_tokens=benchmark.input_tokens,
            output_tokens=benchmark.output_tokens,
            it_energy_per_token=benchmark.it_energy_per_token,
            latency_per_token_s=benchmark.latency_per_token_s,
            record=benchmark.record,
        )
