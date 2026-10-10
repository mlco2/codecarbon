from unittest import mock

from carbonserver.api.services.matomo_tracker import MatomoTracker


def test_tracker_is_disabled_without_url_and_site_id():
    assert not MatomoTracker().enabled
    assert not MatomoTracker(url="https://matomo.example.com").enabled
    assert not MatomoTracker(site_id="3").enabled


def test_tracker_sends_nothing_when_disabled():
    with mock.patch("carbonserver.api.services.matomo_tracker.httpx.get") as get:
        MatomoTracker().track_event("Activation", "account_created")
    get.assert_not_called()


def test_tracker_sends_an_anonymous_event():
    tracker = MatomoTracker(url="https://matomo.example.com/", site_id="3")
    with mock.patch("carbonserver.api.services.matomo_tracker.threading.Thread") as t:
        tracker.track_event("Activation", "account_created")
    params = t.call_args.kwargs["args"][0]
    assert params["idsite"] == "3"
    assert (params["e_c"], params["e_a"]) == ("Activation", "account_created")
    assert set(params) <= {"idsite", "rec", "apiv", "e_c", "e_a", "e_n", "_id", "rand"}
