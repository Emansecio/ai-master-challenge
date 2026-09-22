"""Baixa os artefatos do Router publico, fixados por revisao, sem credenciais."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
REPO = "kucukkanat/LFM2.5-Encoder-350M-Prompt-Router-ONNX"
REVISION = "d5f69da4b475ee0edcba2caf12f5a724aa8cab5a"


def main():
    output = ROOT / "router-assets"
    output.mkdir(exist_ok=True)
    manifest = {"repo": REPO, "revision": REVISION, "files": {}}
    for name in ["config.json", "tokenizer.json", "onnx/model_quantized.onnx"]:
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{name}"
        if not destination.exists():
            partial = destination.with_suffix(destination.suffix + ".partial")
            with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as target:
                size = 0
                checkpoint = 0
                expected = response.headers.get("Content-Length")
                while block := response.read(1024 * 1024):
                    target.write(block)
                    size += len(block)
                    if size - checkpoint >= 64 * 1024 * 1024:
                        print(f"{name}: {size / 1024**2:.0f} MiB", flush=True)
                        checkpoint = size
                if expected is not None and size != int(expected):
                    raise RuntimeError(f"Download incompleto: {name}")
            partial.replace(destination)
        with destination.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        manifest["files"][name] = {"url": url, "bytes": destination.stat().st_size, "sha256": digest}
        print(f"Pronto: {name} ({destination.stat().st_size} bytes)", flush=True)
    (output / "manifesto.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
