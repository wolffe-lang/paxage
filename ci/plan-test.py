#!/usr/bin/env python3
"""ci/plan.py's own proof. python3 only: the REST API and git are stand-ins.

The plan hands the gate its two legs. On the runner's own push to trunk it
leaves the macOS leg when a completed, successful pull_request or
workflow_dispatch run of ci.yml at the pushed commit tested the same tree, ran
that leg once, green, on macOS, and still holds the leg's payload artifact; the
determinism job then compares this push's linux payload with that one. Anything
else runs the leg. The wiring rows hold .github/workflows/ci.yml to it."""
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'ci/plan.py'
REPO = 'wolffe-lang/paxage'
TOKEN = 'plan-test-stand-in-token-5c1e'
MAC = 'macOS arm64 (fmt, build, units, CLI e2e)'
MAC_LABEL = 'macos-latest'
LINUX = 'linux x86-64 (fmt, build, units, CLI e2e)'
DETERMINISM = 'Cross-host four-payload byte identity'
ARTIFACT = 'canonical-arm64'
LEGS = [{'name': 'linux x86-64', 'os': 'ubuntu-24.04', 'arch': 'x86_64'},
        {'name': 'macOS arm64', 'os': 'macos-latest', 'arch': 'arm64'}]
# The runner's own GITHUB_* and any token stay out of every plan this file
# runs: only the trunk push rows hand the plan a push, an API and a token.
SCRUB = ('PLAN_TOKEN', 'PLAN_API_TIMEOUT', 'GH_TOKEN', 'GITHUB_TOKEN', 'GITHUB_EVENT_NAME', 'GITHUB_REF',
         'GITHUB_SHA', 'GITHUB_REPOSITORY', 'GITHUB_API_URL', 'GITHUB_SERVER_URL', 'GITHUB_STEP_SUMMARY',
         'GITHUB_OUTPUT', 'EVENT')


def clean_env(**more):
    env = {k: v for k, v in os.environ.items() if k not in SCRUB}
    env.update(more)
    return env


class QuietServer(http.server.ThreadingHTTPServer):
    # A client that timed out leaves a handler writing to a closed socket.
    daemon_threads = True

    def handle_error(self, request, client_address):
        pass


class FakeAPI:
    """The REST API's three answers the plan reads: the runs of ci.yml at a
    commit, a run's jobs (paged) and a run's artifacts. `fault` is (path
    prefix, kind)."""

    def __init__(self, runs=(), jobs=None, artifacts=None, fault=None, page_cap=100, ignore_filter=False, totals=None):
        self.runs, self.jobs = list(runs), dict(jobs or {})
        self.artifacts = artifacts
        self.fault, self.page_cap, self.ignore_filter = fault, page_cap, ignore_filter
        self.totals = dict(totals or {})
        self.requests = []
        self.redirect_to = None
        api = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                api.requests.append((self.path, self.headers.get('Authorization')))
                status, body, extra = api.answer(self.path)
                data = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(status)
                for k, v in extra.items():
                    self.send_header(k, v)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self.server = QuietServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.05}, daemon=True).start()
        self.url = 'http://127.0.0.1:%d' % self.server.server_address[1]

    def close(self):
        self.server.shutdown()
        self.server.server_close()

    def answer(self, path):
        u = urllib.parse.urlsplit(path)
        q = dict(urllib.parse.parse_qsl(u.query))
        if self.fault and u.path.startswith(self.fault[0]):
            kind = self.fault[1]
            if kind in (500, 403, 404):
                return kind, {'message': 'stand-in error %d' % kind}, {}
            if kind == 'html':
                return 200, b'<html>not json</html>', {}
            if kind == 'keys':
                return 200, {'message': 'an answer without the expected keys'}, {}
            if kind == 'slow':
                time.sleep(4)
            if kind == 'redirect':
                return 302, {}, {'Location': self.redirect_to + path}
        if u.path == '/repos/%s/actions/workflows/ci.yml/runs' % REPO:
            rs = [r for r in self.runs if self.ignore_filter or r['head_sha'] == q.get('head_sha')]
            return 200, {'total_count': len(rs), 'workflow_runs': rs}, {}
        m = re.fullmatch(r'/repos/%s/actions/runs/(\d+)/(jobs|artifacts)' % re.escape(REPO), u.path)
        if m and m.group(2) == 'jobs':
            rid = int(m.group(1))
            js = self.jobs.get(rid, [])
            per = min(int(q.get('per_page', 30)), self.page_cap)
            page = int(q.get('page', 1))
            return 200, {'total_count': self.totals.get(rid, len(js)), 'jobs': js[(page - 1) * per:page * per]}, {}
        if m:
            rid = int(m.group(1))
            arts = self.artifacts.get(rid, []) if self.artifacts is not None else [artifact()]
            return 200, {'total_count': len(arts), 'artifacts': arts}, {}
        return 404, {'message': 'Not Found'}, {}


STAND_IN_GIT = '''#!/bin/sh
# A stand-in for git: the plan's two questions, the pushed commit and its tree,
# and nothing else (any other call fails, so a plan that asks another fails too).
if [ "$*" = "rev-parse HEAD" ]; then echo "$STAND_IN_HEAD"; exit 0; fi
if [ "$*" = "rev-parse HEAD^{tree}" ]; then echo "$STAND_IN_TREE"; exit 0; fi
echo "stand-in git: not answered: $*" >&2
exit 1
'''


def scratch_repo():
    """A directory whose `git` answers for a pushed commit and its tree, so the
    rows need no git of their own."""
    d = tempfile.mkdtemp(prefix='plan-test-git-')
    Path(d, 'git').write_text(STAND_IN_GIT)
    os.chmod(Path(d, 'git'), 0o755)
    return d, 'a1' * 20, 'b2' * 20


def wrun(rid, sha, event='pull_request', conclusion='success', status='completed', path='.github/workflows/ci.yml'):
    return {'id': rid, 'event': event, 'status': status, 'conclusion': conclusion, 'head_sha': sha, 'path': path,
            'run_attempt': 1, 'html_url': 'https://github.com/%s/actions/runs/%d' % (REPO, rid)}


def wjob(name, conclusion='success', labels=None, steps=None):
    if labels is None:
        labels = [MAC_LABEL] if name == MAC else ['ubuntu-24.04']
    return {'name': name, 'status': 'completed', 'conclusion': conclusion, 'labels': labels, 'steps': steps or []}


def artifact(name=ARTIFACT, expired=False):
    return {'id': 1, 'name': name, 'expired': expired, 'size_in_bytes': 1024}


def plan_job(tree, step=True):
    steps = [{'name': 'Set up job', 'conclusion': 'success'}]
    if step:
        steps.append({'name': 'the tree under test is %s' % tree, 'conclusion': 'success'})
    return wjob('plan', steps=steps)


class Legs(unittest.TestCase):
    """Every event but a covered trunk push gets both legs; the plan asks
    nothing anywhere but on the runner's own push to trunk."""

    def plan(self, **env):
        out = Path(tempfile.mkdtemp(prefix='plan-test-out-')) / 'output'
        out.write_text('')
        p = subprocess.run([sys.executable, '-I', str(PLAN), '--github-output', str(out)],
                           capture_output=True, text=True, env=clean_env(**env), timeout=120)
        outputs = dict(l.split('=', 1) for l in out.read_text().splitlines() if '=' in l)
        shutil.rmtree(out.parent, ignore_errors=True)
        return p, outputs

    def test_every_event_gets_both_legs(self):
        for event, ref in (('pull_request', 'refs/pull/9/merge'), ('schedule', 'refs/heads/trunk'),
                           ('workflow_dispatch', 'refs/heads/trunk'), ('push', 'refs/tags/v0.1.0'), ('', '')):
            with self.subTest(event=event, ref=ref):
                p, out = self.plan(GITHUB_EVENT_NAME=event, GITHUB_REF=ref)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(json.loads(out['matrix_gate']), LEGS, p.stderr)
                self.assertEqual(out.get('macos_run'), '', p.stderr)
                self.assertEqual(json.loads(out['covered']), {}, p.stderr)

    def test_the_legs_are_the_gate_matrix_before_the_plan(self):
        # The gate's include before the plan held it: these two, in this order.
        sys.path.insert(0, str(ROOT / 'ci'))
        try:
            import importlib
            plan = importlib.import_module('plan')
        finally:
            sys.path.pop(0)
        self.assertEqual(plan.LEGS, LEGS)
        self.assertEqual(plan.MACOS, {MAC: MAC_LABEL})


class TrunkPushCover(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir, cls.sha, cls.tree = scratch_repo()
        cls.seen = []

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def green(self, tree=None, step=True, mac=True, swap=None, extra=()):
        js = [plan_job(tree or self.tree, step), wjob(LINUX), wjob(DETERMINISM)]
        if mac:
            js.append(swap or wjob(MAC))
        return js + list(extra)

    def run_plan(self, api, event_name='push', ref='refs/heads/trunk', sha=None, token=TOKEN, timeout=None, summary=None):
        out = Path(tempfile.mkdtemp(prefix='plan-test-out-')) / 'output'
        out.write_text('')
        env = clean_env(GITHUB_EVENT_NAME=event_name, GITHUB_REF=ref, GITHUB_SHA=sha or self.sha,
                        GITHUB_REPOSITORY=REPO, GITHUB_API_URL=api.url, GITHUB_SERVER_URL='https://github.com',
                        STAND_IN_HEAD=self.sha, STAND_IN_TREE=self.tree)
        env['PATH'] = self.dir + os.pathsep + env.get('PATH', '')
        if token:
            env['PLAN_TOKEN'] = token
        if timeout:
            env['PLAN_API_TIMEOUT'] = str(timeout)
        if summary:
            env['GITHUB_STEP_SUMMARY'] = summary
        p = subprocess.run([sys.executable, '-I', str(PLAN), '--github-output', str(out)],
                           capture_output=True, text=True, env=env, cwd=self.dir, timeout=120)
        self.seen.append(p.stdout + p.stderr + out.read_text())
        self.assertEqual(p.returncode, 0, p.stderr)
        outputs = dict(l.split('=', 1) for l in out.read_text().splitlines() if '=' in l)
        shutil.rmtree(out.parent, ignore_errors=True)
        return (json.loads(outputs.get('matrix_gate', 'null')), outputs.get('macos_run'),
                json.loads(outputs.get('covered', 'null')), p.stdout + p.stderr)

    def assert_runs_macos(self, api, **kw):
        legs, run, covered, text = self.run_plan(api, **kw)
        self.assertEqual(legs, LEGS, text)
        self.assertEqual((run, covered), ('', {}), text)
        self.assertRegex(text, r'(?m)^plan: keep %s: ' % re.escape(MAC), text)
        return text

    def assert_leaves_macos(self, api, rid, event='pull_request', **kw):
        legs, run, covered, text = self.run_plan(api, **kw)
        self.assertEqual(legs, LEGS[:1], text)
        self.assertEqual(run, str(rid), text)
        self.assertEqual(sorted(covered), [MAC], text)
        self.assertEqual((covered[MAC]['run'], covered[MAC]['event'], covered[MAC]['sha'], covered[MAC]['tree']),
                         (rid, event, self.sha, self.tree), text)
        self.assertRegex(text, r'(?m)^plan: skip %s: green in %s run %d at %s, tree %s' % (
            re.escape(MAC), event, rid, self.sha, self.tree))
        return text

    def test_green_pull_request_run_leaves_macos(self):
        summary = Path(tempfile.mkdtemp(prefix='plan-test-sum-')) / 'summary.md'
        api = FakeAPI([wrun(7001, self.sha)], {7001: self.green()})
        try:
            self.assert_leaves_macos(api, 7001, summary=str(summary))
            self.assertIn('7001', summary.read_text())
            jobs_q = [urllib.parse.parse_qs(urllib.parse.urlsplit(p).query) for p, _ in api.requests if '/jobs' in p]
            self.assertTrue(jobs_q and all(q.get('filter') == ['latest'] for q in jobs_q), api.requests)
            self.assertTrue(api.requests and all(a == 'Bearer ' + TOKEN for _, a in api.requests), api.requests)
        finally:
            api.close()
            shutil.rmtree(summary.parent, ignore_errors=True)

    def test_green_dispatch_run_counts(self):
        api = FakeAPI([wrun(7002, self.sha, event='workflow_dispatch')], {7002: self.green()})
        try:
            self.assert_leaves_macos(api, 7002, event='workflow_dispatch')
        finally:
            api.close()

    def test_other_events_and_unfinished_runs_do_not_count(self):
        runs = [wrun(7003, self.sha, event='schedule'), wrun(7004, self.sha, event='push'),
                wrun(7005, self.sha, conclusion='failure'), wrun(7006, self.sha, conclusion='cancelled'),
                wrun(7007, self.sha, status='in_progress', conclusion=None)]
        api = FakeAPI(runs, {r['id']: self.green() for r in runs})
        try:
            self.assert_runs_macos(api)
        finally:
            api.close()

    def test_another_tree_or_no_tree_does_not_count(self):
        for jobs in (self.green(tree='0' * 40), self.green(step=False)):
            api = FakeAPI([wrun(7008, self.sha)], {7008: jobs})
            try:
                self.assert_runs_macos(api)
            finally:
                api.close()

    def test_no_green_macos_leg_runs_it(self):
        # The plant's target: a green run at the commit with no macOS leg at all.
        for jobs in (self.green(mac=False), self.green(swap=wjob(MAC, conclusion='skipped')),
                     self.green(swap=wjob(MAC, conclusion='cancelled')), self.green(swap=wjob(MAC, labels=['ubuntu-24.04'])),
                     self.green(extra=[wjob(MAC, conclusion='failure')])):
            api = FakeAPI([wrun(7009, self.sha)], {7009: jobs})
            try:
                self.assert_runs_macos(api)
            finally:
                api.close()

    def test_no_macos_payload_runs_it(self):
        # determinism needs the leg's payload: a run without it, or with it
        # expired, is no evidence.
        for arts in ([], [artifact(expired=True)], [artifact(name='canonical-x86_64')]):
            api = FakeAPI([wrun(7022, self.sha)], {7022: self.green()}, artifacts={7022: arts})
            try:
                self.assert_runs_macos(api)
            finally:
                api.close()

    def test_the_green_run_among_red_ones_counts(self):
        api = FakeAPI([wrun(7010, self.sha, conclusion='failure'), wrun(7011, self.sha), wrun(7012, self.sha)],
                      {7010: self.green(), 7011: self.green(), 7012: self.green(mac=False)})
        try:
            self.assert_leaves_macos(api, 7011)
        finally:
            api.close()

    def test_paged_and_short_listings(self):
        api = FakeAPI([wrun(7013, self.sha)], {7013: self.green()}, page_cap=2)
        try:
            self.assert_leaves_macos(api, 7013)
            self.assertGreaterEqual(len([p for p, _ in api.requests if '/jobs' in p]), 2)
        finally:
            api.close()
        api = FakeAPI([wrun(7014, self.sha)], {7014: self.green()}, totals={7014: 99})
        try:
            self.assert_runs_macos(api)
        finally:
            api.close()

    def test_runs_of_another_commit_or_workflow_do_not_count(self):
        api = FakeAPI([wrun(7015, '1' * 40), wrun(7016, self.sha, path='.github/workflows/other.yml')],
                      {7015: self.green(), 7016: self.green()}, ignore_filter=True)
        try:
            self.assert_runs_macos(api)
        finally:
            api.close()

    def test_a_failed_lookup_runs_macos(self):
        for where, kind in (('/repos/%s/actions/workflows' % REPO, 500), ('/repos/%s/actions/runs' % REPO, 403),
                            ('/repos/%s/actions/workflows' % REPO, 'html'), ('/repos/%s/actions/runs' % REPO, 'keys'),
                            ('/repos/%s/actions/workflows' % REPO, 404)):
            with self.subTest(kind=kind):
                api = FakeAPI([wrun(7017, self.sha)], {7017: self.green()}, fault=(where, kind))
                try:
                    self.assert_runs_macos(api)
                finally:
                    api.close()

    def test_a_slow_lookup_runs_macos(self):
        api = FakeAPI([wrun(7018, self.sha)], {7018: self.green()}, fault=('/repos/%s/actions/workflows' % REPO, 'slow'))
        try:
            t0 = time.time()
            self.assert_runs_macos(api, timeout=1)
            self.assertLess(time.time() - t0, 30)
        finally:
            api.close()

    def test_a_redirect_is_not_followed(self):
        elsewhere = FakeAPI([wrun(7019, self.sha)], {7019: self.green()})
        api = FakeAPI([wrun(7019, self.sha)], {7019: self.green()}, fault=('/repos/%s/actions/workflows' % REPO, 'redirect'))
        api.redirect_to = elsewhere.url
        try:
            self.assert_runs_macos(api)
            self.assertEqual(elsewhere.requests, [])
        finally:
            api.close()
            elsewhere.close()

    def test_nothing_is_asked_without_a_trunk_push(self):
        cases = [dict(token=None), dict(sha='2' * 40), dict(event_name='pull_request'),
                 dict(ref='refs/heads/a-lane'), dict(ref='refs/tags/v0.1.0'),
                 dict(event_name='schedule'), dict(event_name='workflow_dispatch')]
        for kw in cases:
            with self.subTest(**{k: str(v) for k, v in kw.items()}):
                api = FakeAPI([wrun(7020, self.sha)], {7020: self.green()})
                try:
                    legs, run, covered, text = self.run_plan(api, **kw)
                    self.assertEqual(api.requests, [], text)
                    self.assertEqual((legs, run, covered), (LEGS, '', {}), text)
                finally:
                    api.close()

    def test_the_token_is_never_printed(self):
        api = FakeAPI([wrun(7021, self.sha)], {7021: self.green()}, fault=('/repos/%s/actions/runs' % REPO, 403))
        try:
            self.run_plan(api)
        finally:
            api.close()
        self.assertTrue(self.seen)
        self.assertFalse([s for s in self.seen if TOKEN in s])


class Wiring(unittest.TestCase):
    def text(self):
        return (ROOT / '.github/workflows/ci.yml').read_text()

    def block(self, job):
        return re.search(r'^  %s:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)' % re.escape(job), self.text(), re.M | re.S).group(1)

    def test_the_workflow_reads_runs_and_artifacts(self):
        # Workflow level: the release gate is generated from these job blocks
        # and its caller grants contents: read alone.
        self.assertRegex(self.text(), r'(?m)^permissions:\n  contents: read\n  actions: read\n(?!  \S)')

    def test_the_plan_job_tests_itself_names_its_tree_and_plans(self):
        plan = self.block('plan')
        self.assertRegex(plan, r'(?m)^      - uses: actions/checkout@v4\n        id: checkout\n')
        after = "        if: ${{ steps.checkout.outcome == 'success' }}\n"
        test = '      - name: the planner can say no (ci/plan-test.py)\n' + after + '        run: python3 -I ci/plan-test.py\n'
        tree = '      - name: the tree under test is ${{ steps.tree.outputs.tree }}\n' + after
        self.assertIn(test, plan)
        self.assertIn('        id: tree\n', plan)
        self.assertIn(tree, plan)
        self.assertIn("test \"$(git rev-parse 'HEAD^{tree}')\" = \"${{ steps.tree.outputs.tree }}\"", plan)
        self.assertIn('      - id: plan\n' + after, plan)
        order = [plan.index(s) for s in (test, '        id: tree\n', tree, '      - id: plan\n')]
        self.assertEqual(order, sorted(order))
        self.assertIn('        run: python3 -I ci/plan.py --github-output "$GITHUB_OUTPUT"\n', plan)
        for out in ('matrix_gate', 'macos_run', 'covered'):
            self.assertIn('      %s: ${{ steps.plan.outputs.%s }}\n' % (out, out), plan)

    def test_only_the_plan_and_the_payload_download_get_the_token(self):
        text = self.text()
        self.assertEqual(text.count('github.token'), 2)
        self.assertEqual(text.count('PLAN_TOKEN'), 1)
        self.assertRegex(self.block('plan'),
                         r'(?m)^      - id: plan\n(        .*\n)*        env:\n          PLAN_TOKEN: \$\{\{ github\.token \}\}\n')
        self.assertIn('          github-token: ${{ github.token }}\n', self.block('determinism'))

    def test_the_gate_takes_its_legs_from_the_plan(self):
        gate = self.block('gate')
        self.assertIn('    needs: plan\n', gate)
        self.assertIn("        include: ${{ fromJSON(needs.plan.outputs.matrix_gate || '[]') }}\n", gate)
        self.assertIn('    name: ${{ matrix.name }} (fmt, build, units, CLI e2e)\n', gate)
        self.assertEqual(['%s (fmt, build, units, CLI e2e)' % l['name'] for l in LEGS], [LINUX, MAC])
        self.assertNotIn('macos-latest', gate)

    def test_determinism_compares_against_the_run_relied_on(self):
        d = self.block('determinism')
        self.assertIn('    needs: [plan, gate]\n', d)
        get = ("      - name: the macOS payload of the run this push relied on\n"
               "        if: ${{ needs.plan.outputs.macos_run != '' }}\n"
               "        uses: actions/download-artifact@v4\n"
               "        with:\n"
               "          name: canonical-arm64\n"
               "          path: canonical-arm64\n"
               "          run-id: ${{ needs.plan.outputs.macos_run }}\n"
               "          github-token: ${{ github.token }}\n")
        self.assertIn(get, d)
        self.assertLess(d.index('          pattern: canonical-*\n'), d.index(get))
        self.assertLess(d.index(get), d.index('cmp canonical-arm64/canonical.payload.tar canonical-x86_64/canonical.payload.tar'))
        self.assertIn("echo 'skip %s: green in run ${{ needs.plan.outputs.macos_run }}" % MAC, d)


if __name__ == '__main__':
    unittest.main(verbosity=2)
