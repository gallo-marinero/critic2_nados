#!/usr/bin/env python3
# Convert a NAdO "_phase.cube" (atan2(Im,Re), wrapped to [-pi,pi]) produced by
# `trick nados` into a coloring field that is safe for an ordinary (non-cyclic)
# colormap: cos(phase), continuous everywhere, in [-1,1]. Fixes the "speckled
# lobe" artifact that comes from coloring raw phase directly, which happens
# because +pi and -pi are the same physical phase but sit at opposite ends of
# a linear colormap, so floating-point noise that flips the sign of a
# near-zero residual imaginary part paints adjacent voxels in opposite
# extreme colors.
#
# cos(phase) = Re/|NAdO| has no such discontinuity (cos(+pi) == cos(-pi)), so
# any standard diverging colormap (e.g. red-white-blue) renders each lobe as
# one uniform color for near-real NAdOs, matching the sign-based lobe
# coloring convention, while still shading continuously for genuinely complex
# regions. Pass --sin to also write sin(phase) = Im/|NAdO| (needed together
# with cos if you want to reconstruct the full phase downstream).
#
# Usage: phase2cos.py foo_phase.cube [--sin]
#   writes foo_phasecos.cube (and foo_phasesin.cube with --sin)

import sys
import argparse
import re


def read_cube_header_and_data(path):
    with open(path) as f:
        lines = f.readlines()
    natm = int(lines[2].split()[0])
    nhead = 6 + natm
    header = lines[:nhead]
    n = [int(lines[3 + i].split()[0]) for i in range(3)]
    ntot = n[0] * n[1] * n[2]
    data = []
    for line in lines[nhead:]:
        data.extend(float(x) for x in line.split())
    if len(data) != ntot:
        raise ValueError(f"{path}: expected {ntot} values, found {len(data)}")
    return header, n, data


def write_cube(path, header, n, data):
    with open(path, "w") as f:
        f.writelines(header)
        ntot = n[0] * n[1] * n[2]
        i = 0
        while i < ntot:
            i_end = min(i + 6, ntot)
            chunk = data[i:i_end]
            f.write(" " + " ".join(f"{v: .5E}" for v in chunk) + "\n")
            i = i_end


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("phase_cube", help="a *_phase.cube file written by trick nados")
    ap.add_argument("--sin", action="store_true", help="also write the sin(phase) companion")
    ap.add_argument("--shift", action="store_true",
                    help="write the phase folded into [-pi/2, 3pi/2) so the branch cut "
                         "falls on the imaginary axis and each real lobe is one value")
    ap.add_argument("--norm", action="store_true",
                    help="write (phase+pi/2)/(2pi) in [0,1), the default range of VESTA's "
                         "texture colouring, so no range needs to be set in the viewer")
    args = ap.parse_args()

    if not re.search(r"_phase\.cube$", args.phase_cube):
        print("warning: input file name does not end in _phase.cube", file=sys.stderr)

    header, n, phase = read_cube_header_and_data(args.phase_cube)
    stem = args.phase_cube[:-len("_phase.cube")]

    import math
    cos_out = stem + "_phasecos.cube"
    write_cube(cos_out, header, n, [math.cos(p) for p in phase])
    print("wrote", cos_out)

    if args.sin:
        sin_out = stem + "_phasesin.cube"
        write_cube(sin_out, header, n, [math.sin(p) for p in phase])
        print("wrote", sin_out)

    if args.shift:
        shift_out = stem + "_phaseshift.cube"
        folded = [p + 2 * math.pi if p < -math.pi / 2 else p for p in phase]
        write_cube(shift_out, header, n, folded)
        print("wrote", shift_out)

    if args.norm:
        norm_out = stem + "_phasenorm.cube"
        normed = [(p + math.pi / 2) / (2 * math.pi) for p in phase]
        write_cube(norm_out, header, n, normed)
        print("wrote", norm_out)


if __name__ == "__main__":
    main()
