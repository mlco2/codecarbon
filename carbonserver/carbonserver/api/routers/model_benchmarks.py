"""
Endpoints for published LLM energy benchmarks.

Separate from ``/emissions`` on purpose. Emissions are private telemetry scoped
to an organization; a benchmark is a claim about a *model*, meant to be read
publicly once approved. They have different lifecycles, different audiences and
different authorization, so they get different endpoints.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi_pagination import Page, paginate
from fastapi_pagination.default import Params
from starlette import status as http_status

from carbonserver.api.schemas import ModelBenchmark, ModelBenchmarkReference
from carbonserver.api.services.auth_service import (
    MandatoryUserWithAuthDependency,
    UserWithAuthDependency,
)
from carbonserver.api.services.model_benchmark_service import (
    BenchmarkValidationError,
    ModelBenchmarkService,
)
from carbonserver.container import ServerContainer

MODEL_BENCHMARKS_ROUTER_TAGS = ["Model benchmarks"]

router = APIRouter()


@router.post(
    "/model-benchmarks",
    tags=MODEL_BENCHMARKS_ROUTER_TAGS,
    status_code=http_status.HTTP_201_CREATED,
    response_model=UUID,
    summary="Submit a benchmark record",
    description=(
        "Accepts a BoAmps report conforming to the LLM energy benchmark "
        "profile. The record is checked against the spec's validity rules and "
        "stored."
    ),
)
@inject
def add_model_benchmark(
    record: Dict[str, Any] = Body(...),
    auth_user: UserWithAuthDependency = Depends(MandatoryUserWithAuthDependency),
    service: ModelBenchmarkService = Depends(
        Provide[ServerContainer.model_benchmark_service]
    ),
) -> UUID:
    try:
        return service.add_benchmark(record, user=auth_user.db_user)
    except BenchmarkValidationError as exc:
        # 422 with every failure, not just the first: a submitter re-running a
        # benchmark to fix one rule at a time would waste hours of GPU time.
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Record does not satisfy the benchmark spec",
                "failures": exc.failures,
            },
        )


@router.get(
    "/model-benchmarks",
    tags=MODEL_BENCHMARKS_ROUTER_TAGS,
    response_model=Page[ModelBenchmark],
    summary="List benchmarks",
)
@inject
def list_model_benchmarks(
    model_name: Optional[str] = Query(None),
    concurrency: Optional[int] = Query(None),
    gpu_model: Optional[str] = Query(None),
    deployment_id: Optional[str] = Query(None),
    service: ModelBenchmarkService = Depends(
        Provide[ServerContainer.model_benchmark_service]
    ),
    params: Params = Depends(),
) -> Page[ModelBenchmark]:
    return paginate(
        service.list_benchmarks(
            model_name=model_name,
            concurrency=concurrency,
            gpu_model=gpu_model,
            deployment_id=deployment_id,
        ),
        params,
    )


@router.get(
    "/model-benchmarks/export",
    tags=MODEL_BENCHMARKS_ROUTER_TAGS,
    response_model=List[ModelBenchmarkReference],
    summary="Curated reference snapshot",
    description=(
        "Every stored record, reduced to the reference quantity and the "
        "context needed to judge whether it applies. Meant to be fetched once "
        "and cached, never per request."
    ),
)
@inject
def export_reference_snapshot(
    model_name: Optional[str] = Query(None),
    deployment_id: Optional[str] = Query(None),
    service: ModelBenchmarkService = Depends(
        Provide[ServerContainer.model_benchmark_service]
    ),
) -> List[ModelBenchmarkReference]:
    return service.export_reference_snapshot(
        model_name=model_name, deployment_id=deployment_id
    )


@router.get(
    "/model-benchmarks/{benchmark_id}",
    tags=MODEL_BENCHMARKS_ROUTER_TAGS,
    response_model=ModelBenchmark,
    summary="Read one benchmark, including its full BoAmps record",
)
@inject
def read_model_benchmark(
    benchmark_id: UUID,
    service: ModelBenchmarkService = Depends(
        Provide[ServerContainer.model_benchmark_service]
    ),
) -> ModelBenchmark:
    return service.get_one_benchmark(benchmark_id)
