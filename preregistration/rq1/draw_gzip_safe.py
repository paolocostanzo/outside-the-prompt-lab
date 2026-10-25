#!/usr/bin/env python3
"""Runs `sample_frame.py draw COMMIT` (or `verify`) unchanged, with one tooling fix allowed by D44 point 4 ("a tooling failure
is fixed in the tooling and the same round is used"). Two failures found before the draw, on 25 Oct 2026: the Internet
Archive serves archived copies of the GitHub events page gzip-compressed, which `archived_event` reads as plain JSON and
crashes; and the drand relay drand.cloudflare.com answers 403 to Python's default user agent. This wrapper only makes network
reads send a user agent and transparently decompress gzip bodies; sample_frame.py itself is the copy in the frame commit (it
checks that) and no rule changes.

    python3 preregistration/rq1/draw_gzip_safe.py draw COMMIT
"""
import gzip, io, pathlib, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sample_frame as sf  # noqa: E402

_urlopen = urllib.request.urlopen


class _Body(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


def urlopen(url, *a, **k):
    if isinstance(url, str):
        url = urllib.request.Request(url, headers={"User-Agent": "otp-lab-sample-frame/1.0"})
    with _urlopen(url, *a, **k) as resp:
        data = resp.read()
    return _Body(gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data)


sf.urllib.request.urlopen = urlopen

if __name__ == "__main__":
    if sys.argv[1:2] == ["draw"] and len(sys.argv) == 3:
        sf.main(sys.argv[2])
    elif sys.argv[1:] in (["verify"], ["verify", "online"]):
        sf.verify(online=len(sys.argv) == 3)
    else:
        sys.exit(__doc__)
