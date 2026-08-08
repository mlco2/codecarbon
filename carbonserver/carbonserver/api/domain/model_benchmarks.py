import abc
from typing import List, Optional
from uuid import UUID

from carbonserver.api import schemas


class ModelBenchmarks(abc.ABC):
    @abc.abstractmethod
    def add_benchmark(
        self,
        record: dict,
        extracted: schemas.ModelBenchmarkBase,
        submitted_by: Optional[UUID],
    ) -> UUID:
        raise NotImplementedError

    @abc.abstractmethod
    def get_one_benchmark(self, benchmark_id: UUID) -> schemas.ModelBenchmark:
        raise NotImplementedError

    @abc.abstractmethod
    def list_benchmarks(
        self,
        model_name: Optional[str] = None,
        concurrency: Optional[int] = None,
        gpu_model: Optional[str] = None,
        deployment_id: Optional[str] = None,
    ) -> List[schemas.ModelBenchmark]:
        raise NotImplementedError
