#!/usr/bin/env python3
"""Exercise the release build argv without requiring a real compiler."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseBuild(unittest.TestCase):
    def test_release_readme_and_rename_census_agree(self):
        (ROOT / 'target').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='release census ', dir=ROOT / 'target') as tmp:
            home = Path(tmp)
            env = dict(os.environ, HOME=str(home), TMPDIR=str(home), SHELL='/bin/sh')
            result = subprocess.run([sys.executable, '-B', '-I', str(ROOT / 'tools/check-census')],
                                    cwd=ROOT, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn('PASS census-allowlist', result.stdout)
            self.assertIn('PASS census-old-names', result.stdout)

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
            (root / 'tools/check-glibc-floor').write_bytes((ROOT / 'tools/check-glibc-floor').read_bytes())
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

    def release_build(self, binary_bytes):
        """Run the release build line with a stand-in compiler that writes binary_bytes; returns the result."""
        config = json.loads((ROOT / '.github/release.json').read_text())
        (ROOT / 'target').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='release floor ', dir=ROOT / 'target') as tmp:
            root = Path(tmp)
            for name in ('tools', '.wolf-bin', 'home', 'tmp'):
                (root / name).mkdir()
            (root / 'tools/lib-toolchain.sh').write_text('WOLF="$PAXAGE_ROOT/.wolf-bin/wolf"\nexport WOLF\n')
            (root / 'tools/check-glibc-floor').write_bytes((ROOT / 'tools/check-glibc-floor').read_bytes())
            (root / 'payload.bin').write_bytes(binary_bytes)
            compiler = root / '.wolf-bin/wolf'
            compiler.write_text(
                '#!/bin/sh\nset -eu\nout=\nwhile [ "$#" -gt 0 ]; do\n'
                '  if [ "$1" = -o ]; then shift; out=$1; fi\n  shift\ndone\n'
                'cp payload.bin "$out"\nchmod 755 "$out"\n')
            compiler.chmod(0o755)
            env = dict(os.environ, HOME=str(root / 'home'), TMPDIR=str(root / 'tmp'), SHELL='/bin/sh')
            env.pop('PAXAGE_ROOT', None)
            env.pop('WOLF', None)
            return subprocess.run(config['build'], cwd=root, env=env, text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def test_release_build_checks_the_glibc_floor(self):
        elf = b'\x7fELF' + b'\0' * 12
        ok = self.release_build(elf + b'GLIBC_2.34\0')
        self.assertEqual(ok.returncode, 0, ok.stdout)
        self.assertIn('PASS glibc-floor max=2.34', ok.stdout)
        high = self.release_build(elf + b'GLIBC_2.38\0')
        self.assertNotEqual(high.returncode, 0, high.stdout)
        self.assertIn('FAIL glibc-floor GLIBC_2.38 is above the floor 2.34', high.stdout)
        other = self.release_build(b'\xcf\xfa\xed\xfe not an ELF binary')
        self.assertEqual(other.returncode, 0, other.stdout)
        self.assertIn('SKIP glibc-floor not an ELF file', other.stdout)

    def test_fetch_toolchain_runs_with_no_tmpdir_set(self):
        # The shared release workflow runs tools/fetch-toolchain with whatever
        # environment the runner has, and no TMPDIR. A stand-in curl that fails
        # at once proves the script got past its scratch directory.
        (ROOT / 'target').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='fetch no tmpdir ', dir=ROOT / 'target') as tmp:
            root = Path(tmp) / 'root'
            (root / 'tools').mkdir(parents=True)
            for name in ('fetch-toolchain', 'lib-toml.sh', 'lib-fetch.sh'):
                (root / 'tools' / name).write_bytes((ROOT / 'tools' / name).read_bytes())
            (root / 'tools/fetch-toolchain').chmod(0o755)
            (root / 'wolf-toolchain.toml').write_bytes((ROOT / 'wolf-toolchain.toml').read_bytes())
            bin_dir = Path(tmp) / 'bin'
            bin_dir.mkdir()
            curl = bin_dir / 'curl'
            curl.write_text('#!/bin/sh\necho stand-in-curl-called >&2\nexit 22\n')
            curl.chmod(0o755)
            env = {k: v for k, v in os.environ.items() if k != 'TMPDIR'}
            env.update(PATH=f'{bin_dir}:{env["PATH"]}', HOME=str(Path(tmp) / 'home'), SHELL='/bin/sh')
            result = subprocess.run(['sh', str(root / 'tools/fetch-toolchain')], cwd=root, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('TMPDIR', result.stdout)
            self.assertIn('stand-in-curl-called', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
