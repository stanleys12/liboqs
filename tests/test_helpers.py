# SPDX-License-Identifier: MIT

import pytest
import requests
import unittest.mock

import helpers

def test_cached_download_retries_and_caches(tmp_path, monkeypatch):
    monkeypatch.setattr(helpers, 'TEST_VECTOR_CACHE_DIR', str(tmp_path))
    monkeypatch.setattr(helpers.time, 'sleep', lambda s: None)
    ok = unittest.mock.Mock(status_code=200, content=b'{}')
    unavailable = unittest.mock.Mock(status_code=503)
    get = unittest.mock.Mock(side_effect=[requests.ConnectionError(), unavailable, ok])
    monkeypatch.setattr(helpers.requests, 'get', get)

    assert helpers.cached_download('https://example.com/vectors.json') == b'{}'
    assert helpers.cached_download('https://example.com/vectors.json') == b'{}'
    assert get.call_count == 3

def test_cached_download_does_not_retry_client_error(tmp_path, monkeypatch):
    monkeypatch.setattr(helpers, 'TEST_VECTOR_CACHE_DIR', str(tmp_path))
    monkeypatch.setattr(helpers.time, 'sleep', lambda s: None)
    not_found = unittest.mock.Mock(status_code=404)
    not_found.raise_for_status.side_effect = requests.HTTPError()
    get = unittest.mock.Mock(return_value=not_found)
    monkeypatch.setattr(helpers.requests, 'get', get)

    with pytest.raises(requests.HTTPError):
        helpers.cached_download('https://example.com/missing.json')
    assert get.call_count == 1

def test_cached_download_fails_when_retries_are_exhausted(tmp_path, monkeypatch):
    monkeypatch.setattr(helpers, 'TEST_VECTOR_CACHE_DIR', str(tmp_path))
    monkeypatch.setattr(helpers.time, 'sleep', lambda s: None)
    get = unittest.mock.Mock(side_effect=requests.Timeout())
    monkeypatch.setattr(helpers.requests, 'get', get)

    with pytest.raises(requests.Timeout):
        helpers.cached_download('https://example.com/vectors.json')
    assert get.call_count == 4
