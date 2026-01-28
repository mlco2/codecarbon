from typing import List
from uuid import UUID
import os
import json
import subprocess

from carbonserver.api.infra.repositories.repository_runs import SqlAlchemyRepository
from carbonserver.api.schemas import Run, RunCreate, User
from carbonserver.api.services.auth_context import AuthContext
from carbonserver.api.services.injector_service import Injector
from carbonserver.kaggle_template import KaggleScriptTemplate

class RunService:
    def __init__(
        self,
        run_repository: SqlAlchemyRepository,
        auth_context: AuthContext,
    ):
        self._repository = run_repository
        self._auth_context = auth_context

    def add_run(self, run: RunCreate, user: User = None) -> Run:
        created_run = self._repository.add_run(run)
        return created_run

    def read_run(self, run_id: UUID, user: User = None) -> Run:
        return self._repository.get_one_run(run_id)

    def list_runs(self, user: User = None) -> List[Run]:
        return self._repository.list_runs()

    def list_runs_from_experiment(self, experiment_id: str, user: User = None):
        return self._repository.get_runs_from_experiment(experiment_id)

    def read_project_last_run(
        self, project_id: str, start_date, end_date, user: User = None
    ) -> Run:
        return self._repository.get_project_last_run(project_id, start_date, end_date)

    def run_remote(self,codecarbon_api_key: str, experiment_id: str, injected_code: str, kaggle_api_key: str, kaggle_username: str, notebook_title: str, api_endpoint: str = 'https://api.codecarbon.io') -> dict:
        template_module = KaggleScriptTemplate.get_template()
        injector = Injector(module=template_module, filename="test.py")
        variables = {
            'api_endpoint': api_endpoint,
            'api_key': codecarbon_api_key,
            'experiment_id': experiment_id
        }
        injector.inject_variables(variables)

        # injected_code is already clean Python code (no quote handling needed)
        injector.inject_function(injected_code, func_name='injected_kernel')
        metadata_config = KaggleScriptTemplate.get_metadata()
        metadata_config['id'] = f"{kaggle_username}/{notebook_title}"
        metadata_config['title'] = notebook_title
        metadata_config['code_file'] = "test.py"
        temp_dir = injector.get_temp_dir()
        temp_metadata_path = os.path.join(temp_dir, "kernel-metadata.json")
        with open(temp_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_config, f, indent=2, ensure_ascii=False)

        env = os.environ.copy()
        env["KAGGLE_API_TOKEN"] = kaggle_api_key
        subprocess.run(
            ["kaggle", "kernels", "push", "-p", temp_dir],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        return {
            "status": "success",
            "message": f"Kaggle kernel '{notebook_title}' has been launched",
            "kaggle_url": f"https://www.kaggle.com/{kaggle_username}/{notebook_title}"
        }