#!/usr/bin/env python3
"""Exercise the release build argv without requiring a real compiler."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseBuild(unittest.TestCase):
    def test_build_bootstraps_its_root_and_preserves_alias_bytes(self):
        config = json.loads((ROOT / '.github/release.json').read_text())
        (ROOT / 'target').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='release command ', dir=ROOT / 'target') as tmp:
            root = Path(tmp)
            (root / 'tools').mkdir()
            (root / '.wolf-bin').mkdir()
            (root / 'home').mkdir()
            (root / 'tmp').mkdir()
            (root / 'tools/lib-toolchain.sh').write_text(
                ': "${PAXAGE_ROOT:?release command must set PAXAGE_ROOT}"\n'
                '[ "$PAXAGE_ROOT" = "$PWD" ]\n'
                'WOLF="$PAXAGE_ROOT/.wolf-bin/wolf"\nexport WOLF\n')
            compiler = root / '.wolf-bin/wolf'
            compiler.write_text(
                '#!/bin/sh\nset -eu\nprintf "%s\\n" "$@" > compiler.argv\n'
                'out=\nwhile [ "$#" -gt 0 ]; do\n'
                '  if [ "$1" = -o ]; then shift; out=$1; fi\n  shift\ndone\n'
                '[ -n "$out" ]\nprintf "#!/bin/sh\\nexit 0\\n" > "$out"\nchmod 755 "$out"\n')
            compiler.chmod(0o755)
            env = dict(os.environ, HOME=str(root / 'home'), TMPDIR=str(root / 'tmp'), SHELL='/bin/sh')
            env.pop('PAXAGE_ROOT', None)
            env.pop('WOLF', None)
            result = subprocess.run(config['build'], cwd=root, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertEqual(result.returncode, 0, result.stdout)
            primary = root / config['binaries']['paxage']
            alias = root / config['binaries']['pxg']
            self.assertTrue(os.access(primary, os.X_OK))
            self.assertEqual(primary.read_bytes(), alias.read_bytes())
            argv = (root / 'compiler.argv').read_text().splitlines()
            self.assertEqual(argv, ['build', '--release', '--deny-warnings', 'src/paxage.lu', '-o', 'target/release/paxage'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
