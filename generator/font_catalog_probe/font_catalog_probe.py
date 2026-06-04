"""Run the host-side font catalog probe.

This file is a generator runner, not a normal regression test. It uses the
pytest-embedded Arduino fixtures because lang-ship:host sketches expose a serial
socket instead of running setup() from a plain process invocation.
"""
from pathlib import Path
import shutil


def test_font_catalog_probe(dut):
    out = Path(__file__).resolve().parent / "output"
    if out.exists():
        shutil.rmtree(out)

    dut.expect("TEST start font_catalog_probe", timeout=30)
    dut.expect("PROGRESS 1/", timeout=120)
    dut.expect(r"DONE fonts=(\d+)", timeout=7200)
    dut.expect("TEST done", timeout=30)
