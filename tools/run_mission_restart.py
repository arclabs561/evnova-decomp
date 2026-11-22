"""Run the save and resume mission scenarios in two Linux game processes."""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

TOOLS = Path(__file__).resolve().parent


def run_pair(binary, install, output, *, tools=TOOLS, timeout=600):
    binary, install, output = (Path(p).resolve() for p in (binary, install, output))
    if sys.platform != "linux" or not binary.is_file() or not (install / "Nova.rez").is_file():
        raise ValueError("requires Linux, an executable and an installation containing Nova.rez")
    output.mkdir(parents=True, exist_ok=False)
    (output / "EV Nova").symlink_to(install, target_is_directory=True)
    env = dict(os.environ, HOME=str(output), XDG_DATA_HOME=str(output / "profile"),
               EVN_PROBE="1", SDL_VIDEO_DRIVER="dummy", SDL_AUDIO_DRIVER="dummy",
               SDL_RENDER_DRIVER="software")
    for phase in ("mission_save", "mission_resume"):
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        with (output / f"{phase}.log").open("w") as log:
            game = subprocess.Popen([binary], cwd=output, env=dict(env, EVN_PROBE_PORT=str(port)),
                                    stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + min(timeout, 45)
                while time.monotonic() < deadline:
                    if game.poll() is not None:
                        raise RuntimeError(f"{phase}: game exited before startup ({game.returncode})")
                    try:
                        with socket.create_connection(("127.0.0.1", port), timeout=.3):
                            break
                    except OSError:
                        time.sleep(.1)
                else:
                    raise TimeoutError(f"{phase}: game did not open its probe port")
                subprocess.run([sys.executable, tools / "scenario_runner.py",
                                tools.parent / "tests/scenarios" / f"{phase}.toml",
                                "--base-url", f"http://127.0.0.1:{port}",
                                "--artifacts", output / "artifacts"],
                               check=True, timeout=timeout, stdout=log, stderr=subprocess.STDOUT)
                if game.wait(timeout=30):
                    raise RuntimeError(f"{phase}: game exited with status {game.returncode}")
            finally:
                if game.poll() is None:
                    game.kill()
                    game.wait()
        if phase == "mission_save" and not any((output / "profile").rglob("*.plt")):
            raise RuntimeError("save scenario exited without writing a pilot")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("install", type=Path)
    parser.add_argument("output", type=Path, help="new diagnostics and profile directory")
    args = parser.parse_args()
    run_pair(args.binary, args.install, args.output)
