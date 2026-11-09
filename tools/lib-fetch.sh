# lib-fetch.sh — sourced by tools/fetch-toolchain; not executable on its own.
#
# fetch_release URL OUT: one release archive, with curl's growing backoff. A
# GitHub release origin can answer 504 for minutes at a time (paxage#9's
# labelled run died on seven attempts of a 20-second retry span). curl retries
# its transient errors (a timeout, 408, 429, 500, 502, 503, 504) up to 10 times,
# waiting 1 s and then doubling, and gives up once 600 s have passed. The digest
# check stays with the caller: where an archive came from never makes it
# acceptable. PAXAGE_FETCH_RETRY_DELAY fixes the delay and
# PAXAGE_FETCH_RETRY_MAX_TIME bounds the span, for tools/check-fetch-retry.
fetch_release() {
    if [ -n "${PAXAGE_FETCH_RETRY_DELAY:-}" ]; then
        set -- "$1" "$2" --retry-delay "$PAXAGE_FETCH_RETRY_DELAY"
    else
        set -- "$1" "$2"
    fi
    url=$1 out=$2
    shift 2
    if ! curl -sSfL --retry 10 --retry-max-time "${PAXAGE_FETCH_RETRY_MAX_TIME:-600}" "$@" -o "$out" "$url"; then
        echo "fetch-toolchain: gave up on $url after curl's retries" >&2
        return 1
    fi
}
