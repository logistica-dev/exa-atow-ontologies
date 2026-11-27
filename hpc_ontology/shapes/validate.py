#!/usr/bin/env python3
"""SHACL validator for the HPC ontology.

Loads:
  * shapes  : hpc-shapes.ttl                (this folder)
  -> To be doneL add the fixed URIs
  * TBox    : ../hpc-core.ttl + ../hpc.ttl  (only the current versions!)
  * data    : the ABox file(s) passed with --data

Usage:
    python3 validate.py                              # shapes self-check (no data)
    python3 validate.py --data a.ttl b.ttl            # validate ABoxes
    python3 validate.py --data a.ttl --out report.txt
"""
import argparse, os, sys
from collections import Counter, defaultdict

import rdflib
from rdflib import Graph, Namespace, RDF
from rdflib.namespace import RDFS

SH = Namespace("http://www.w3.org/ns/shacl#")
HERE = os.path.dirname(os.path.abspath(__file__))

try:
    import pyshacl
except ImportError:
    sys.exit("pyshacl is required: pip install pyshacl")


def default_ont():
    cands = [os.path.join(HERE, "..", "hpc-core.ttl"),
             os.path.join(HERE, "..", "hpc.ttl")]
    return [os.path.normpath(p) for p in cands if os.path.exists(p)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shapes", default=os.path.join(HERE, "hpc-shapes.ttl"))
    ap.add_argument("--ont", nargs="*", default=None,
                    help="TBox files (default: ../hpc-core.ttl ../hpc.ttl)")
    ap.add_argument("--data", nargs="*", default=[],
                    help="ABox files to validate")
    ap.add_argument("--format", default="turtle")
    ap.add_argument("--inference", default="rdfs", choices=["none", "rdfs", "owlrl", "both"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--keep-domain-range", action="store_true",
                    help="keep rdfs:domain/range in the inference graph (default: strip them, "
                         "otherwise rdfs:range infers the very type that sh:class is meant to check)")
    args = ap.parse_args()

    shapes = Graph().parse(args.shapes, format="turtle")
    ont_files = args.ont if args.ont is not None else default_ont()

    data = Graph()
    loaded = []
    for f in args.data:
        try:
            data.parse(f, format=args.format)
            loaded.append(f)
        except Exception as e:
            print(f"!! cannot parse data file {f}: {e}")

    ont = Graph()
    loaded_ont = []
    for f in ont_files:
        try:
            ont.parse(f, format="turtle")
            loaded_ont.append(f)
        except Exception as e:
            print(f"!! cannot parse ont file {f}: {e}")

    # Strip rdfs:domain / rdfs:range from the inference graph: with rdfs
    # inference, "x p y" + "p rdfs:range C" adds "y rdf:type C", which makes
    # every "sh:class C" check on the value of p tautological. Keeping only
    # rdfs:subClassOf (and the TBox individuals) gives us subclass inference
    # without hiding class errors.
    if not args.keep_domain_range:
        stripped = Graph()
        for t in ont:
            if t[1] not in (RDFS.domain, RDFS.range):
                stripped.add(t)
        ont = stripped

    lines = []
    def out(s=""):
        lines.append(s)
        print(s)

    out("=" * 78)
    out("HPC Resource ontology — SHACL validation")
    out("=" * 78)
    out(f"shapes   : {args.shapes} ({len(shapes)} triples)")
    for f in loaded_ont:
        out(f"ont      : {f}")
    for f in loaded:
        out(f"data     : {f}")
    # pySHACL does NOT expose ont_graph triples to the constraint evaluation
    # graph (it only uses them for inference), so TBox individuals (canonical
    # instances) such as :SLURM, :GCC or :Lustre would be invisible to sh:class.
    # Merge the TBox into the data graph instead; rdfs:subClassOf triples are
    # enough for subclass inference.
    data_all = Graph()
    for t in data:
        data_all.add(t)
    for t in ont:
        data_all.add(t)

    out(f"triples  : data={len(data)}  tbox={len(ont)}  total={len(data_all)}  inference={args.inference}")
    out()

    ok, results, _ = pyshacl.validate(
        data_all,
        shacl_graph=shapes,
        inference=None if args.inference == "none" else args.inference,
        advanced=True,
        allow_warnings=True,
    )

    sev = Counter()
    by_msg = defaultdict(list)
    by_shape = Counter()
    for r in results.subjects(RDF.type, SH.ValidationResult):
        s = str(results.value(r, SH.resultSeverity) or SH.Violation).split("#")[-1]
        sev[s] += 1
        msg = str(results.value(r, SH.resultMessage) or "")
        focus = results.value(r, SH.focusNode)
        path = results.value(r, SH.resultPath)
        by_msg[(s, msg)].append((focus, path))
        by_shape[str(results.value(r, SH.sourceShape))] += 1

    out("=" * 78)
    out(f"RESULT: {'✅ CONFORMS' if ok else '❌ DOES NOT CONFORM'}")
    out("=" * 78)
    for s in ("Violation", "Warning", "Info"):
        if sev[s]:
            out(f"  {s:10s}: {sev[s]}")
    out()

    if by_msg:
        out("DETAILS (grouped by message)")
        out("-" * 78)
        for (s, msg), items in sorted(by_msg.items(), key=lambda kv: (kv[0][0] != "Violation", kv[0][1])):
            out(f"\n[{s}] {msg}")
            uniq, seen = [], set()
            for focus, path in items:
                key = (str(focus), str(path))
                if key in seen:
                    continue
                seen.add(key)
                uniq.append((focus, path))
            out(f"       {len(uniq)} node(s):")
            for focus, path in uniq:
                f = str(focus).split("/")[-1].split("#")[-1]
                p = str(path).split("#")[-1] if path else ""
                out(f"         - {f}" + (f"  ({p})" if p else ""))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print(f"\nreport written to {args.out}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
