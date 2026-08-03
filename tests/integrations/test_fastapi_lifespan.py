import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

import codecarbon.integrations.fastapi.lifespan as cc_fastapi_lifespan
from codecarbon.integrations.fastapi.lifespan import create_codecarbon_lifespan


@pytest.fixture
def app():
    return FastAPI()


@patch.object(cc_fastapi_lifespan, "EmissionsTracker")
def test_lifespan_stops_tracker_on_shutdown(MockTracker, app):
    tracker = MagicMock()
    MockTracker.return_value = tracker

    async def run():
        async with create_codecarbon_lifespan(app, project_name="api"):
            assert app.state.codecarbon_tracker is tracker
            tracker.start.assert_called_once()

    asyncio.run(run())

    tracker.stop.assert_called_once()
    assert app.state.codecarbon_tracker is None
