"""Full routing flow: hand-routed power skeleton -> negotiated routing of all other
nets (with wire jumpers where needed) -> GND through the pour -> routes.json

    python autoroute.py [--iters N] [--seed S] [--out file]
"""
import json
import os
import sys
import time

import design
import negotiate
import route as R_

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    iters = int(sys.argv[sys.argv.index("--iters") + 1]) if "--iters" in sys.argv else 30
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 0
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(HERE, "routes.json")
    b = design.build()
    t0 = time.time()
    r, best, hand = negotiate.negotiate(b, iters=iters, seed=seed)
    nj, ntr, njs = best
    # finalise into a plain Router state for the GND phase
    r.tracks = []
    for net, ts in hand.items():
        r.tracks += [t for t in ts if not t.get("seed")]   # already painted into occ
    for net, ts in ntr.items():
        for t in ts:
            r.add_track(t)
    r.jumpers = list(getattr(r, "hand_jumpers", []))
    for net, js in njs.items():
        for j in js:
            r.add_jumper(j)
    gfail = R_.gnd_phase(b, r)
    data = dict(tracks=r.tracks, jumpers=r.jumpers, failures=gfail, seed=seed,
                converged=nj is not None)
    with open(out, "w") as fh:
        json.dump(data, fh, indent=0)
    print("RESULT seed=%d converged=%s tracks=%d jumpers=%d gnd_failures=%d time=%.0fs" % (
        seed, nj is not None, len(r.tracks), len(r.jumpers), len(gfail), time.time() - t0))


if __name__ == "__main__":
    main()
