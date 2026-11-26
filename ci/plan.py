#!/usr/bin/env python3
"""ci/plan.py — the gate's legs, and the macOS leg a trunk push may leave.

    python3 -I ci/plan.py [--github-output FILE]

Writes `matrix_gate=` (the gate job's `include`, a JSON list), `macos_run=`
(the run whose macOS leg this push relies on, or empty) and `covered=` (that
leg with the run, event, commit and tree it relied on; `{}` otherwise), to
--github-output (appended) and to standard output. The reason goes to standard
error, and to the step summary when there is one. Exit 0.

Every run gets both legs but one: the runner's own push to trunk
(GITHUB_EVENT_NAME push, GITHUB_REF refs/heads/trunk) whose commit already has
the macOS leg green. Merges are fast-forwards, so a push to trunk runs the
commit its pull request's run has just passed. On such a push the plan asks the
REST API, with the workflow's own read-only token (PLAN_TOKEN), for this
workflow's runs at GITHUB_SHA, and leaves the macOS leg only when a completed,
successful pull_request or workflow_dispatch run there

  - tested the same tree: its `plan` job has the step `the tree under test is
    <tree>` (a pull request's run tests its merge with the base, which is this
    tree only when the base is already in the commit);
  - has, at its latest attempt, the macOS leg once, green, on its macOS runner;
  - still holds that leg's payload artifact, which this push's determinism job
    downloads and compares with its own linux payload.

Anything else runs the leg: no such run, a lookup that fails, times out,
redirects or answers oddly, a jobs listing short of its count, no token, a
checkout that is not the pushed commit. ci/plan-test.py is this file's proof.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

# The gate's matrix, as ci.yml held it before the plan did.
LEGS = [{'name': 'linux x86-64', 'os': 'ubuntu-24.04', 'arch': 'x86_64'},
        {'name': 'macOS arm64', 'os': 'macos-latest', 'arch': 'arm64'}]
MAC_LEG = LEGS[1]
# The macOS job a trunk push may leave, by the name GitHub gives it, with its runner's label.
MACOS = {'%s (fmt, build, units, CLI e2e)' % MAC_LEG['name']: MAC_LEG['os']}
PAYLOAD = 'canonical-%s' % MAC_LEG['arch']
WORKFLOW = '.github/workflows/ci.yml'
EVIDENCE_EVENTS = ('pull_request', 'workflow_dispatch')
TREE_STEP = re.compile(r'^the tree under test is ([0-9a-f]{40}|[0-9a-f]{64})$')
HEX = re.compile(r'[0-9a-f]{40}|[0-9a-f]{64}')
MAX_RUNS = 10
MAX_PAGES = 5


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """The plan follows no redirect: the token goes to the API alone."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'a redirect, not followed', headers, fp)


class Api:
    def __init__(self, base, repo, token, timeout):
        self.base, self.repo, self.token, self.timeout = base.rstrip('/'), repo, token, timeout
        self.opener = urllib.request.build_opener(NoRedirect)

    def get(self, path, **query):
        url = '%s/repos/%s/%s?%s' % (self.base, self.repo, path, urllib.parse.urlencode(query))
        req = urllib.request.Request(url, headers={
            'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'User-Agent': 'paxage-ci-plan',
        })
        with self.opener.open(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode('utf-8'))


def run_jobs(api, run_id):
    """A run's jobs at its latest attempt, every page; None when the listing
    falls short of its own count."""
    jobs = []
    for page in range(1, MAX_PAGES + 1):
        d = api.get('actions/runs/%d/jobs' % run_id, filter='latest', per_page=100, page=page)
        got, total = d['jobs'], int(d['total_count'])
        jobs += got
        if len(jobs) >= total:
            return jobs if len(jobs) == total else None
        if not got:
            return None
    return None


def tested_tree(jobs):
    """The tree a run's `plan` job named, or None."""
    plan = [j for j in jobs if j.get('name') == 'plan']
    if len(plan) != 1 or plan[0].get('conclusion') != 'success':
        return None
    trees = [m.group(1) for s in (plan[0].get('steps') or []) if s.get('conclusion') == 'success'
             for m in [TREE_STEP.match(s.get('name') or '')] if m]
    return trees[0] if len(trees) == 1 else None


def green_leg(jobs, name, label):
    """Whether the job is in the run once, green, on its macOS runner."""
    found = [j for j in jobs if j.get('name') == name]
    return len(found) == 1 and found[0].get('conclusion') == 'success' and label in (found[0].get('labels') or [])


def holds_payload(api, run_id):
    """Whether the run still holds the macOS leg's payload, unexpired."""
    d = api.get('actions/runs/%d/artifacts' % run_id, per_page=100)
    return any(a.get('name') == PAYLOAD and a.get('expired') is False for a in d['artifacts'])


def git(*args):
    return subprocess.run(['git'] + list(args), capture_output=True, text=True, check=True).stdout.strip()


def trunk_push(env):
    """Whether this is the runner's own push to trunk."""
    return env.get('GITHUB_EVENT_NAME') == 'push' and env.get('GITHUB_REF') == 'refs/heads/trunk'


def cover(env, say):
    """-> {macOS job: the run, event, commit and tree it is green in}; {} on any doubt."""
    token = env.get('PLAN_TOKEN') or ''
    hide = lambda s: s.replace(token, '<token>') if token else s
    sha, repo = env.get('GITHUB_SHA') or '', env.get('GITHUB_REPOSITORY') or ''
    if not token:
        say('no token for the lookup: the macOS leg runs')
        return {}
    if not HEX.fullmatch(sha) or not repo:
        say('no pushed commit or repository named: the macOS leg runs')
        return {}
    try:
        head, tree = git('rev-parse', 'HEAD'), git('rev-parse', 'HEAD^{tree}')
    except (OSError, subprocess.CalledProcessError) as e:
        say('git could not name the checkout (%s): the macOS leg runs' % type(e).__name__)
        return {}
    if head != sha:
        say('the checkout %s is not the pushed commit %s: the macOS leg runs' % (head, sha))
        return {}
    say('the pushed commit %s, tree %s' % (sha, tree))
    try:
        api = Api(env.get('GITHUB_API_URL') or 'https://api.github.com', repo, token,
                  float(env.get('PLAN_API_TIMEOUT') or 20))
        listing = api.get('actions/workflows/%s/runs' % os.path.basename(WORKFLOW), head_sha=sha, per_page=100)
        runs = [r for r in listing['workflow_runs']
                if r.get('head_sha') == sha and r.get('path') == WORKFLOW and r.get('status') == 'completed'
                and r.get('conclusion') == 'success' and r.get('event') in EVIDENCE_EVENTS]
        runs.sort(key=lambda r: -int(r['id']))
        for r in runs[:MAX_RUNS]:
            rid = int(r['id'])
            jobs = run_jobs(api, rid)
            if jobs is None:
                say('%s run %d: its jobs listing falls short of its count, not relied on' % (r['event'], rid))
                continue
            t = tested_tree(jobs)
            if t != tree:
                say('%s run %d tested tree %s, not %s: not relied on' % (r['event'], rid, t or '(not named)', tree))
                continue
            for job, label in MACOS.items():
                if not green_leg(jobs, job, label):
                    continue
                if not holds_payload(api, rid):
                    say('%s run %d holds no unexpired %s: not relied on' % (r['event'], rid, PAYLOAD))
                    continue
                return {job: {'run': rid, 'event': r['event'], 'sha': sha, 'tree': tree}}
        return {}
    except Exception as e:  # any failure of the lookup runs the macOS leg
        say('the lookup failed (%s: %s): the macOS leg runs' % (type(e).__name__, hide(str(e))))
        return {}


def verdict_lines(covered, server, repo):
    lines = []
    for job, label in MACOS.items():
        c = covered.get(job)
        if c:
            lines.append('skip %s: green in %s run %d at %s, tree %s (%s/%s/actions/runs/%d)' % (
                job, c['event'], c['run'], c['sha'], c['tree'], server, repo, c['run']))
        else:
            lines.append('keep %s: no completed, successful pull_request or workflow_dispatch run of %s at this '
                         'commit tested this tree with it green on %s and its payload held' % (
                             job, os.path.basename(WORKFLOW), label))
    return lines


def main():
    ap = argparse.ArgumentParser(prog='ci/plan.py')
    ap.add_argument('--github-output')
    a = ap.parse_args()
    env = os.environ
    say = lambda s: print('plan: ' + s, file=sys.stderr)
    covered = {}
    if trunk_push(env):
        covered = cover(env, say)
        server, repo = env.get('GITHUB_SERVER_URL') or 'https://github.com', env.get('GITHUB_REPOSITORY') or ''
        lines = verdict_lines(covered, server, repo)
        for line in lines:
            say(line)
        summary = env.get('GITHUB_STEP_SUMMARY')
        if summary:
            try:
                with open(summary, 'a', encoding='utf-8') as f:
                    f.write("### The trunk push's macOS leg\n\n" + ''.join('- %s\n' % l for l in lines) + '\n')
            except OSError as e:
                say('the step summary could not be written (%s)' % e)
    else:
        say('%s %s: both legs (only a push to trunk asks whether its macOS leg is green already)' % (
            env.get('GITHUB_EVENT_NAME') or 'no event', env.get('GITHUB_REF') or 'no ref'))
    legs = [l for l in LEGS if not ('%s (fmt, build, units, CLI e2e)' % l['name']) in covered]
    run = next(iter(covered.values()))['run'] if covered else ''
    out = {'matrix_gate': json.dumps(legs, separators=(',', ':')), 'macos_run': str(run),
           'covered': json.dumps(covered, separators=(',', ':'), sort_keys=True)}
    text = ''.join('%s=%s\n' % kv for kv in out.items())
    sys.stdout.write(text)
    if a.github_output:
        with open(a.github_output, 'a', encoding='utf-8') as f:
            f.write(text)


if __name__ == '__main__':
    main()
