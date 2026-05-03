"""Offline smoke runner for the media pipeline.

This script creates a small validated script, stubs image/audio generation, and
builds `remotion_props.json` so the architecture can be tested without external
API keys.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import director
from src.core.script_validator import dump_script


def build_sample_script() -> list[dict]:
    return [
        {
            "scene": 1,
            "narration": "First we show the problem and hook the viewer.",
            "image_prompt": "A clean cinematic startup scene with bold motion and contrast",
        },
        {
            "scene": 2,
            "narration": "Then we reveal the solution and end with a strong call to action.",
            "image_prompt": "A bright product reveal scene with modern marketing polish",
        },
    ]


def _fake_generate_images(prompt: str, out_dir: str = "outputs", **kwargs) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    prefix = kwargs.get("filename_prefix", "image")
    image_path = Path(out_dir) / f"{prefix}.png"
    image_path.write_bytes(b"fake image")
    return [str(image_path)]


def _fake_synthesize_audio(text: str, out_path: str) -> str:
    Path(out_path).write_bytes(b"fake audio")
    return out_path


def run_smoke_demo(output_dir: str | None = None) -> str:
    work_dir = Path(output_dir or tempfile.mkdtemp(prefix="agent-smoke-"))
    assets_dir = work_dir / "assets"
    script_path = work_dir / "script.json"
    remotion_props_path = work_dir / "remotion_props.json"

    dump_script(build_sample_script(), script_path)

    director.generate_images = _fake_generate_images
    director.synthesize_audio = _fake_synthesize_audio

    return director.build_remotion_props(
        script_path=str(script_path),
        assets_dir=str(assets_dir),
        remotion_props_path=str(remotion_props_path),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an offline smoke test for the pipeline")
    parser.add_argument("--output-dir", default=None, help="Optional output directory for smoke test artifacts")
    args = parser.parse_args()

    result = run_smoke_demo(output_dir=args.output_dir)
    print(result)


if __name__ == "__main__":
    main()
