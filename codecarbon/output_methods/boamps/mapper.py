"""
Maps CodeCarbon EmissionsData to BoAmps report format.
"""

import warnings
from dataclasses import fields as dataclass_fields
from dataclasses import replace
from typing import Optional

from codecarbon.output_methods.boamps.models import (
    BoAmpsEnvironment,
    BoAmpsHardware,
    BoAmpsHeader,
    BoAmpsInfrastructure,
    BoAmpsMeasure,
    BoAmpsReport,
    BoAmpsSoftware,
    BoAmpsSystem,
    BoAmpsTask,
)
from codecarbon.output_methods.emissions_data import EmissionsData

BOAMPS_FORMAT_VERSION = "0.1"
BOAMPS_FORMAT_SPEC_URI = "https://github.com/Boavizta/BoAmps/tree/main/model"


def _to_boamps_datetime(timestamp: str) -> str:
    """Normalize a timestamp to BoAmps format (YYYY-MM-DD HH:MM:SS)."""
    return timestamp.replace("T", " ") if timestamp else timestamp


def map_emissions_to_boamps(
    emissions: EmissionsData,
    task: Optional[BoAmpsTask] = None,
    header: Optional[BoAmpsHeader] = None,
    quality: Optional[str] = None,
    infra_overrides: Optional[dict] = None,
    environment_overrides: Optional[dict] = None,
) -> BoAmpsReport:
    """
    Map CodeCarbon EmissionsData to a BoAmps report.

    Auto-fills fields from EmissionsData and merges with user-provided context.
    User-provided values take precedence over auto-detected values.

    Args:
        emissions: CodeCarbon emissions data from a completed run.
        task: User-provided task context (required for schema-valid BoAmps).
        header: User-provided header overrides.
        quality: Quality assessment ("high", "medium", "low").
        infra_overrides: Additional infrastructure fields (cloud_instance, cloud_service).
        environment_overrides: Additional environment fields (power_source, etc.).

    Returns:
        A BoAmpsReport populated with auto-detected and user-provided data.
    """
    report_header = _build_header(emissions, header)
    measures = [_build_measure(emissions)]
    system = _build_system(emissions)
    software = _build_software(emissions)
    infrastructure = _build_infrastructure(emissions, infra_overrides)
    environment = _build_environment(emissions, environment_overrides)

    if task is None:
        warnings.warn(
            "No BoAmps task context provided. The output will be missing required "
            "fields (taskStage, taskFamily, algorithms, dataset) and will not "
            "validate against the BoAmps schema.",
            UserWarning,
            stacklevel=2,
        )

    return BoAmpsReport(
        header=report_header,
        task=task,
        measures=measures,
        system=system,
        software=software,
        infrastructure=infrastructure,
        environment=environment,
        quality=quality,
    )


def _build_header(
    emissions: EmissionsData, user_header: Optional[BoAmpsHeader]
) -> BoAmpsHeader:
    """Build header from EmissionsData, merging with user overrides."""
    auto_header = BoAmpsHeader(
        format_version=BOAMPS_FORMAT_VERSION,
        format_version_specification_uri=BOAMPS_FORMAT_SPEC_URI,
        report_id=emissions.run_id,
        report_datetime=_to_boamps_datetime(emissions.timestamp),
    )

    if user_header is None:
        return auto_header

    # User values override auto-detected values
    return BoAmpsHeader(
        licensing=user_header.licensing or auto_header.licensing,
        format_version=user_header.format_version or auto_header.format_version,
        format_version_specification_uri=(
            user_header.format_version_specification_uri
            or auto_header.format_version_specification_uri
        ),
        report_id=user_header.report_id or auto_header.report_id,
        report_datetime=user_header.report_datetime or auto_header.report_datetime,
        report_status=user_header.report_status or auto_header.report_status,
        publisher=user_header.publisher or auto_header.publisher,
    )


def _build_measure(emissions: EmissionsData) -> BoAmpsMeasure:
    """Build a BoAmps measure from EmissionsData."""
    # Note: emissions.tracking_mode is "process"/"machine" (CodeCarbon's scope),
    # not the CPU/GPU power tracking method (rapl, nvml, etc.) that BoAmps expects
    # for cpuTrackingMode/gpuTrackingMode. We omit these fields since we don't
    # have the actual tracker implementation details in EmissionsData.
    measure = BoAmpsMeasure(
        measurement_method="codecarbon",
        version=emissions.codecarbon_version,
        power_consumption=emissions.energy_consumed,
        measurement_duration=emissions.duration,
        measurement_date_time=_to_boamps_datetime(emissions.timestamp),
    )

    # CPU utilization as fraction (0-1)
    if emissions.cpu_utilization_percent > 0:
        measure.average_utilization_cpu = round(
            emissions.cpu_utilization_percent / 100.0, 4
        )

    # GPU fields only if GPU is present
    if emissions.gpu_count and emissions.gpu_count > 0:
        if emissions.gpu_utilization_percent > 0:
            measure.average_utilization_gpu = round(
                emissions.gpu_utilization_percent / 100.0, 4
            )

    return measure


def _build_system(emissions: EmissionsData) -> BoAmpsSystem:
    """Build system info from EmissionsData."""
    return BoAmpsSystem(os=emissions.os)


def _build_software(emissions: EmissionsData) -> BoAmpsSoftware:
    """Build software info from EmissionsData."""
    return BoAmpsSoftware(
        language="python",
        version=emissions.python_version,
    )


def _build_infrastructure(
    emissions: EmissionsData, overrides: Optional[dict] = None
) -> BoAmpsInfrastructure:
    """Build infrastructure from EmissionsData hardware fields."""
    components = []

    # CPU component (always present)
    # emissions.cpu_count is logical thread count. BoAmps nbComponent expects
    # physical cores. Standard SMT/HT uses 2 threads per core.
    cpu_cores = max(1, int(emissions.cpu_count) // 2) if emissions.cpu_count else 1
    cpu_component = BoAmpsHardware(
        component_type="cpu",
        component_name=emissions.cpu_model,
        nb_component=cpu_cores,
    )
    components.append(cpu_component)

    # GPU component (only if present)
    if emissions.gpu_count and emissions.gpu_count > 0:
        gpu_component = BoAmpsHardware(
            component_type="gpu",
            component_name=emissions.gpu_model if emissions.gpu_model else None,
            nb_component=int(emissions.gpu_count),
        )
        components.append(gpu_component)

    # RAM component (always present)
    ram_component = BoAmpsHardware(
        component_type="ram",
        nb_component=1,
        memory_size=emissions.ram_total_size,
    )
    components.append(ram_component)

    # emissions.on_cloud can be "N" even on public cloud (the tracker clears
    # cloud_provider/region for some providers). Use cloud_provider as a
    # secondary signal to avoid misreporting cloud runs as on-premise.
    is_cloud = emissions.on_cloud == "Y" or bool(emissions.cloud_provider)
    infra = BoAmpsInfrastructure(
        infra_type="publicCloud" if is_cloud else "onPremise",
        cloud_provider=(
            emissions.cloud_provider if is_cloud and emissions.cloud_provider else None
        ),
        components=components,
    )

    # Apply overrides from context file
    if overrides:
        for attr in ("cloud_instance", "cloud_service", "infra_type"):
            if attr in overrides:
                setattr(infra, attr, overrides[attr])

        # Merge user-provided components: enrich auto-detected components
        # with user-supplied details (manufacturer, family, series, share, etc.)
        # by matching on component_type. Extra user components are appended.
        if "components" in overrides:
            user_components = overrides["components"]
            auto_by_type = {c.component_type: c for c in infra.components}
            merged = []
            used_types = set()
            for user_comp in user_components:
                if user_comp.component_type in auto_by_type:
                    auto = auto_by_type[user_comp.component_type]
                    # Build a merged copy: user values take precedence,
                    # auto-detected fill blanks. Avoids mutating the originals.
                    fill = {
                        f.name: getattr(auto, f.name)
                        for f in dataclass_fields(user_comp)
                        if f.name != "component_type"
                        and getattr(user_comp, f.name) is None
                    }
                    user_comp = replace(user_comp, **fill) if fill else user_comp
                    used_types.add(user_comp.component_type)
                merged.append(user_comp)
            # Keep auto-detected components that the user didn't override
            for auto in infra.components:
                if auto.component_type not in used_types:
                    merged.append(auto)
            infra.components = merged

    return infra


def _build_environment(
    emissions: EmissionsData, overrides: Optional[dict] = None
) -> BoAmpsEnvironment:
    """Build environment from EmissionsData location fields."""
    env = BoAmpsEnvironment(
        country=emissions.country_name,
        latitude=emissions.latitude,
        longitude=emissions.longitude,
    )

    if overrides:
        for attr in (
            "location",
            "power_supplier_type",
            "power_source",
            "power_source_carbon_intensity",
        ):
            if attr in overrides:
                setattr(env, attr, overrides[attr])

    return env
