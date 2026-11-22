from pathlib import Path
import tempfile
import unittest

from run_mission_restart import run_pair


class MissionRestartTest(unittest.TestCase):
    def test_real_processes_share_profile_and_first_failure_stops_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Nova.rez").touch()
            game = root / "game"
            game.write_text("""#!/usr/bin/env python3
import os, socket
from pathlib import Path
p = Path(os.environ['XDG_DATA_HOME'])
p.mkdir(exist_ok=True)
pilot = p / 'pilot.plt'
with socket.socket() as s:
    s.bind(('127.0.0.1', int(os.environ['EVN_PROBE_PORT'])))
    s.listen()
    for _ in range(2):
        conn, _ = s.accept()
        conn.close()
with (p / 'events').open('a') as log:
    print(os.getpid(), pilot.exists(), file=log)
pilot.touch()
""")
            game.chmod(0o755)
            runner = root / "scenario_runner.py"
            runner.write_text("""import socket, sys
from urllib.parse import urlsplit
port = urlsplit(sys.argv[sys.argv.index('--base-url') + 1]).port
socket.create_connection(('127.0.0.1', port)).close()
""")
            run_pair(game, root, root / "passed", tools=root, timeout=5)
            events = (root / "passed/profile/events").read_text().splitlines()
            first, second = [e.split() for e in events]
            self.assertNotEqual(first[0], second[0])
            self.assertEqual([first[1], second[1]], ["False", "True"])
            runner.write_text("raise SystemExit(7)")
            from subprocess import CalledProcessError
            with self.assertRaises(CalledProcessError):
                run_pair(game, root, root / "failed", tools=root, timeout=5)
            self.assertFalse((root / "failed/mission_resume.log").exists())
