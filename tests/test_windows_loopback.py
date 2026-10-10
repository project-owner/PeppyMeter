"""Windows 系统回环采集的数据源回归测试。"""

import logging
import sys
from threading import Event
from types import SimpleNamespace

import pytest

from configfileparser import (
    DATA_SOURCE,
    MONO_ALGORITHM,
    POLLING_INTERVAL,
    PIPE_NAME,
    SMOOTH_BUFFER_SIZE,
    TYPE,
    STEP,
    STEREO_ALGORITHM,
    VOLUME_CONSTANT,
    VOLUME_GAIN_DB,
    VOLUME_GAIN_DB_SOURCE,
    VOLUME_MAX,
    VOLUME_MAX_IN_PIPE,
    VOLUME_MIN,
)
from datasource import (
    DataSource,
    MONO_ALGORITHM_AVERAGE,
    SOURCE_LOOPBACK,
    SOURCE_PIPE,
    STEREO_ALGORITHM_NEW,
    get_platform_data_source_type,
)


def make_config(data_source_type=SOURCE_LOOPBACK):
    """构造只包含数据源所需字段的最小配置。"""
    return {
        DATA_SOURCE: {
            TYPE: data_source_type,
            MONO_ALGORITHM: MONO_ALGORITHM_AVERAGE,
            STEREO_ALGORITHM: STEREO_ALGORITHM_NEW,
            VOLUME_CONSTANT: 0.0,
            PIPE_NAME: "unused",
            VOLUME_MIN: 0.0,
            VOLUME_MAX: 100.0,
            VOLUME_MAX_IN_PIPE: 100.0,
            VOLUME_GAIN_DB: 0.0,
            VOLUME_GAIN_DB_SOURCE: "",
            STEP: 1,
            POLLING_INTERVAL: 0.04,
            SMOOTH_BUFFER_SIZE: 0,
        }
    }


def test_pipe_is_loopback_only_on_windows():
    assert get_platform_data_source_type(SOURCE_PIPE, "win32") == SOURCE_LOOPBACK
    assert get_platform_data_source_type(SOURCE_PIPE, "linux") == SOURCE_PIPE


def test_loopback_recorder_uses_default_playback_device(monkeypatch):
    calls = {}
    recorder = object()
    def create_recorder(**kwargs):
        calls["recorder_options"] = kwargs
        return recorder

    microphone = SimpleNamespace(recorder=create_recorder)

    def get_microphone(**kwargs):
        calls["microphone_options"] = kwargs
        return microphone

    fake_soundcard = SimpleNamespace(
        default_speaker=lambda: SimpleNamespace(name="默认扬声器"),
        get_microphone=get_microphone,
    )
    monkeypatch.setitem(sys.modules, "soundcard", fake_soundcard)
    source = DataSource(make_config())

    assert source.create_loopback_recorder() is recorder
    assert calls["microphone_options"] == {
        "id": "默认扬声器",
        "include_loopback": True,
    }
    assert calls["recorder_options"]["channels"] == 2


def test_loopback_converts_stereo_rms_to_meter_scale():
    source = DataSource(make_config())
    samples = [[0.1, 0.01] for _ in range(100)]

    left, right, mono = source.get_loopback_value(samples)

    assert left == pytest.approx(200.0 / 3.0)
    assert right == pytest.approx(100.0 / 3.0)
    assert mono == pytest.approx(50.0)


def test_silence_and_invalid_levels_map_to_minimum():
    source = DataSource(make_config())

    assert source.get_loopback_level(0.0) == source.min
    assert source.get_loopback_level(float("nan")) == source.min


def test_missing_loopback_backend_keeps_source_silent(monkeypatch, caplog):
    monkeypatch.setitem(sys.modules, "soundcard", None)
    source = DataSource(make_config())

    with caplog.at_level(logging.ERROR):
        source.get_loopback_data()

    assert source.get_current_data() == (0, 0, 0)
    assert "soundcard" in caplog.text.lower()


def test_loopback_worker_reads_blocks_and_updates_meter_data(monkeypatch):
    class FakeRecorder:
        def __enter__(self):
            return self

        def __exit__(self, exception_type, exception, traceback):
            return False

        def record(self, numframes):
            assert numframes == 1920
            source.run_flag = False
            return [[0.1, 0.01] for _ in range(numframes)]

    recorder = FakeRecorder()
    microphone = SimpleNamespace(recorder=lambda **kwargs: recorder)
    fake_soundcard = SimpleNamespace(
        default_speaker=lambda: SimpleNamespace(name="Default Speaker"),
        get_microphone=lambda **kwargs: microphone,
    )
    monkeypatch.setitem(sys.modules, "soundcard", fake_soundcard)
    source = DataSource(make_config())
    source.get_loopback_data()

    assert source.get_current_data() == pytest.approx((200.0 / 3.0, 100.0 / 3.0, 50.0))


def test_loopback_does_not_start_duplicate_capture_threads():
    source = DataSource(make_config())
    entered = Event()
    release = Event()
    calls = []

    def wait_for_stop():
        calls.append(True)
        entered.set()
        while source.run_flag and not release.wait(0.01):
            pass

    source.get_loopback_data = wait_for_stop
    try:
        source.start_data_source()
        assert entered.wait(1.0)
        first_thread = source.data_thread
        source.start_data_source()
        assert source.data_thread is first_thread
        assert calls == [True]
    finally:
        source.stop_data_source()
        release.set()
        source.data_thread.join(1.0)
