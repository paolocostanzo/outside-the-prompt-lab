#!/usr/bin/env python3
"""Verify the RQ1 sample (D44) from a release archive, without git history: the frame file in this folder must have the SHA-256
recorded in the manifest; the seed must follow from that hash and the manifest's drand value; the round must be the first
20:00:00 UTC at least one hour after the recorded push; the sample must be the one sample_frame.py computes. With `online`,
the drand value is read again from the relays. In a clone, `sample_frame.py verify` does the same from the frame commit.

    python3 preregistration/rq1/verify_archive.py [online]
"""
import csv, hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sample_frame as sf  # noqa: E402


def main(online=False, folder=HERE):
    folder = pathlib.Path(folder)
    m = json.loads((folder / "rq1-sample-manifest.json").read_text())
    raw = (folder / "rq1-frame.csv").read_bytes()
    if hashlib.sha256(raw).hexdigest() != m["frame_sha256"]:
        sys.exit("rq1-frame.csv differs from the frame recorded in the manifest")
    if sf.seed_of(m["frame_sha256"], m["drand_randomness"]) != m["seed"]:
        sys.exit("seed does not follow from the frame and the beacon")
    rnd = sf.first_round_after(sf.ts(m["push_event"]["created_at"]))
    if (m["drand_chain"], m["drand_round"]) != (sf.DRAND_CHAIN, rnd):
        sys.exit("the round does not follow from the push time")
    if online:
        import draw_gzip_safe  # noqa: F401  (user agent for the relays, as in the draw)
        if sf.fetch_round(rnd) != m["drand_randomness"]:
            sys.exit("the beacon value differs from drand")
    _, _, out = sf.sample(sf.read_frame(raw), m["seed"])
    with open(folder / "rq1-sample.csv", newline="") as f:
        if [dict(r) for r in csv.DictReader(f)] != [{k: str(v) for k, v in r.items()} for r in out]:
            sys.exit("the published sample differs from the recomputed one")
    if not sf.independently_verifiable(m["capture"]):
        print("note: round not independently verifiable (no timely Internet Archive capture)")
    print("sample verified from the archive" + (" (beacon checked online)" if online else " (beacon value from the manifest)"))


if __name__ == "__main__":
    main(online=sys.argv[1:] == ["online"])
