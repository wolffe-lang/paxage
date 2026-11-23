# Publishing a paxage repository

These scripts run on the machine that serves a repository's files. They are written to be read and then run by the person who owns that machine; paxage itself signs nothing here.

- `install` sets the machine up: a publish user, its directories, the scripts, two systemd timers and, if asked, one restricted ssh key. Run `install --check` first. It changes nothing and says what it would do and what already exists. The top of the script lists, step by step, everything it changes on the system.
- `pxg-publish` is the one command that ssh key may run. It takes a signed batch (`metadata/N.targets.json` and the objects it names) as a tar stream on standard input, checks what the archive holds before it extracts anything, places the objects create-only, commits the targets file, signs and commits the next snapshot and timestamp with the online keys, and verifies the whole repository as a client would.
- `pxg-resign timestamp` and `pxg-resign snapshot` write the next timestamp (daily) or snapshot (weekly, followed by the timestamp that names it). The two timers in `pxg-resign-*.timer` call them.
- `pxg-settings` holds the names every script reads (the repository directory, the key directory, the scratch directory, the paxage and OpenSSL commands); `/etc/pxg-publish.env` overrides them.

The online keys (snapshot and timestamp) are files the machine's administrator places in the key directory; no script here makes, reads for any other purpose, or moves a key. The targets key and the root keys stay offline and sign through `repo draft-targets`, `repo draft-root` and `repo attach`.
