"""
BoAmps data models for standardized AI/ML energy consumption reporting.

These dataclasses map to the BoAmps JSON schemas defined at:
https://github.com/Boavizta/BoAmps/tree/main/model

All fields use snake_case internally and are converted to camelCase on serialization.
"""

import re
from dataclasses import dataclass, fields, is_dataclass
from typing import List, Optional


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _to_dict(obj) -> dict:
    """Recursively convert a dataclass to a camelCase dict, stripping None values."""
    result = {}
    for f in fields(obj):
        value = getattr(obj, f.name)
        if value is None:
            continue
        key = snake_to_camel(f.name)
        if isinstance(value, list):
            result[key] = [
                _to_dict(item) if is_dataclass(item) else item for item in value
            ]
        elif is_dataclass(value):
            result[key] = _to_dict(value)
        else:
            result[key] = value
    return result


@dataclass
class BoAmpsPublisher:
    name: Optional[str] = None
    division: Optional[str] = None
    project_name: Optional[str] = None
    confidentiality_level: Optional[str] = None
    public_key: Optional[str] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsPublisher":
        return cls(**{camel_to_snake(k): v for k, v in d.items()})


@dataclass
class BoAmpsHeader:
    licensing: Optional[str] = None
    format_version: Optional[str] = None
    format_version_specification_uri: Optional[str] = None
    report_id: Optional[str] = None
    report_datetime: Optional[str] = None
    report_status: Optional[str] = None
    publisher: Optional[BoAmpsPublisher] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsHeader":
        kwargs = {}
        for k, v in d.items():
            snake_key = camel_to_snake(k)
            if snake_key == "publisher" and isinstance(v, dict):
                kwargs[snake_key] = BoAmpsPublisher.from_dict(v)
            else:
                kwargs[snake_key] = v
        return cls(**kwargs)


@dataclass
class BoAmpsAlgorithm:
    training_type: Optional[str] = None
    algorithm_type: Optional[str] = None
    algorithm_name: Optional[str] = None
    algorithm_uri: Optional[str] = None
    foundation_model_name: Optional[str] = None
    foundation_model_uri: Optional[str] = None
    parameters_number: Optional[float] = None
    framework: Optional[str] = None
    framework_version: Optional[str] = None
    class_path: Optional[str] = None
    layers_number: Optional[float] = None
    epochs_number: Optional[float] = None
    optimizer: Optional[str] = None
    quantization: Optional[str] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsAlgorithm":
        return cls(**{camel_to_snake(k): v for k, v in d.items()})


@dataclass
class BoAmpsDataset:
    data_usage: Optional[str] = None
    data_type: Optional[str] = None
    data_format: Optional[str] = None
    data_size: Optional[float] = None
    data_quantity: Optional[float] = None
    shape: Optional[str] = None
    source: Optional[str] = None
    source_uri: Optional[str] = None
    owner: Optional[str] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsDataset":
        return cls(**{camel_to_snake(k): v for k, v in d.items()})


@dataclass
class BoAmpsTask:
    task_stage: Optional[str] = None
    task_family: Optional[str] = None
    nb_request: Optional[float] = None
    algorithms: Optional[List[BoAmpsAlgorithm]] = None
    dataset: Optional[List[BoAmpsDataset]] = None
    measured_accuracy: Optional[float] = None
    estimated_accuracy: Optional[str] = None
    task_description: Optional[str] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsTask":
        kwargs = {}
        for k, v in d.items():
            snake_key = camel_to_snake(k)
            if snake_key == "algorithms" and isinstance(v, list):
                kwargs[snake_key] = [BoAmpsAlgorithm.from_dict(a) for a in v]
            elif snake_key == "dataset" and isinstance(v, list):
                kwargs[snake_key] = [BoAmpsDataset.from_dict(ds) for ds in v]
            else:
                kwargs[snake_key] = v
        return cls(**kwargs)


@dataclass
class BoAmpsMeasure:
    measurement_method: Optional[str] = None
    manufacturer: Optional[str] = None
    version: Optional[str] = None
    cpu_tracking_mode: Optional[str] = None
    gpu_tracking_mode: Optional[str] = None
    average_utilization_cpu: Optional[float] = None
    average_utilization_gpu: Optional[float] = None
    power_calibration_measurement: Optional[float] = None
    duration_calibration_measurement: Optional[float] = None
    power_consumption: Optional[float] = None
    measurement_duration: Optional[float] = None
    measurement_date_time: Optional[str] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsMeasure":
        return cls(**{camel_to_snake(k): v for k, v in d.items()})


@dataclass
class BoAmpsSystem:
    os: Optional[str] = None
    distribution: Optional[str] = None
    distribution_version: Optional[str] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsSystem":
        return cls(**{camel_to_snake(k): v for k, v in d.items()})


@dataclass
class BoAmpsSoftware:
    language: Optional[str] = None
    version: Optional[str] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsSoftware":
        return cls(**{camel_to_snake(k): v for k, v in d.items()})


@dataclass
class BoAmpsHardware:
    component_name: Optional[str] = None
    component_type: Optional[str] = None
    nb_component: Optional[int] = None
    memory_size: Optional[float] = None
    manufacturer: Optional[str] = None
    family: Optional[str] = None
    series: Optional[str] = None
    share: Optional[float] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsHardware":
        return cls(**{camel_to_snake(k): v for k, v in d.items()})


@dataclass
class BoAmpsInfrastructure:
    infra_type: Optional[str] = None
    cloud_provider: Optional[str] = None
    cloud_instance: Optional[str] = None
    cloud_service: Optional[str] = None
    components: Optional[List[BoAmpsHardware]] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsInfrastructure":
        kwargs = {}
        for k, v in d.items():
            snake_key = camel_to_snake(k)
            if snake_key == "components" and isinstance(v, list):
                kwargs[snake_key] = [BoAmpsHardware.from_dict(c) for c in v]
            else:
                kwargs[snake_key] = v
        return cls(**kwargs)


@dataclass
class BoAmpsEnvironment:
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None
    power_supplier_type: Optional[str] = None
    power_source: Optional[str] = None
    power_source_carbon_intensity: Optional[float] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsEnvironment":
        return cls(**{camel_to_snake(k): v for k, v in d.items()})


@dataclass
class BoAmpsReport:
    header: Optional[BoAmpsHeader] = None
    task: Optional[BoAmpsTask] = None
    measures: Optional[List[BoAmpsMeasure]] = None
    system: Optional[BoAmpsSystem] = None
    software: Optional[BoAmpsSoftware] = None
    infrastructure: Optional[BoAmpsInfrastructure] = None
    environment: Optional[BoAmpsEnvironment] = None
    quality: Optional[str] = None

    def to_dict(self) -> dict:
        return _to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BoAmpsReport":
        kwargs = {}
        nested_types = {
            "header": BoAmpsHeader,
            "task": BoAmpsTask,
            "system": BoAmpsSystem,
            "software": BoAmpsSoftware,
            "infrastructure": BoAmpsInfrastructure,
            "environment": BoAmpsEnvironment,
        }
        for k, v in d.items():
            snake_key = camel_to_snake(k)
            if snake_key == "measures" and isinstance(v, list):
                kwargs[snake_key] = [BoAmpsMeasure.from_dict(m) for m in v]
            elif snake_key in nested_types and isinstance(v, dict):
                kwargs[snake_key] = nested_types[snake_key].from_dict(v)
            else:
                kwargs[snake_key] = v
        return cls(**kwargs)
