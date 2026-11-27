# SHACL shapes — HPC ontology

SHACL validation of **`hpc centre` instances** (and everything a centre
aggregates: supercomputers, partitions, nodes, components, filesystems,
mounts, QoS, operating systems, software…) against the current TBox
`../hpc-core.ttl` + `../hpc.ttl` (`owl:versionInfo 0.3.0`).

## Files

| File | Purpose |
|---|---|
| `hpc-shapes.ttl` | 40 node shapes / 123 property shapes / 906 triples |
| `validate.py` | generic validator (shapes + TBox + `--data` files) |
| `example-hpc-center.ttl` | minimal **valid** centre — reference template |
| `example-hpc-center-bad.ttl` | deliberately **invalid** centre — negative test |
| `README.md` | this file |

## Quick start

```bash
cd hpc_ontology/shapes

# shapes self-check (no data)
python3 validate.py

# the valid template must conform
python3 validate.py --data example-hpc-center.ttl           # ✅ CONFORMS

# the broken template must be rejected
python3 validate.py --data example-hpc-center-bad.ttl       # ❌ 16 violations

# validate real ABoxes 
python3 validate.py --data ../instances/hpc-centers.ttl \
                              ../instances/hpc-instances-cines.ttl \
                              ../instances/hpc-instances-idris.ttl \
                              ../instances/hpc-instances-tgcc.ttl
```

Options: `--shapes FILE`, `--ont FILE…`, `--data FILE…`, `--format turtle`,
`--inference none|rdfs|owlrl|both`, `--out report.txt`,
`--keep-domain-range` (see below).

Exit code is `0` when the data conforms, `1` otherwise — usable in CI.

## What is enforced

**`sh:Violation`** (structural, mirrors the OWL restrictions of the TBox):

| Node shape | Key rules |
|---|---|
| `HPCCenterShape` | `rdfs:label` ≥1, `:location` exactly 1, `:operatedBy` ≥1 `:Organization`; typed targets for `:hosts`, `:hasStorageMount`, `:hasArchiveSystem`, `:hasCoolingSystem`; `xsd:anyURI` for URLs |
| `OrganizationShape`, `FundingAgencyShape` | `rdfs:label` ≥1, `:website` anyURI |
| `SupercomputerShape` | `:hostedAt` exactly 1 `:HPCCenter`, `:usesResourceManager` ≥1, `:hasPartition` ≥1, positive `:nodeCount`/`:totalCoresCount`, `:commissioningDate`/`:decommissioningDate` = `xsd:date`, typed `:usesFileSystem`/`:runsOS`/`:supportsCompiler` |
| `PartitionShape` | `:partitionName` exactly 1, `:usesNodeType` ≥1 `:ComputeNode`, positive counts, `:allocatedFromQuota` = boolean, typed `:hasQoS`/`:hasTotalScalarMemory`, `:maxWallTime` = `xsd:duration` |
| `ComputeNodeShape` | label, `:coresCountPerNode` ≥1, typed `:belongsToPartition`/`:hasMemoryComponent` |
| `ScalarNodeShape` / `AcceleratedNodeShape` | `:hasCPUComponent` ≥1 / `:hasAcceleratorCardComponent` ≥1 |
| `*ComponentShape` (CPU, Processor, Memory, Storage, AcceleratorCard, Interconnect) | `:refersToModel` exactly 1 of the right model class, `:quantity` ≥1 |
| `ProcessorShape` / `CPUShape` / `AcceleratorCardShape` / `MemoryShape` / `StorageShape` / `InterconnectShape` | core numeric fields, typed value objects |
| `QuantitativeValueShape` | `:hasValue` exactly 1 `xsd:decimal`, `:hasUnit` exactly 1 string |
| `Frequency/Bandwidth/Throughput/MemoryCapacity/StorageCapacity/PeakPerformance/NominalPower` | closed unit vocabularies |
| `QoSShape` | `rdfs:label` ≥1 (**`skos:prefLabel` alone is not enough**), `:maxWallTime` = `xsd:duration`, non-negative `:max*` quotas, boolean `:isDefaultQoS` |
| `FileSystemShape` / `StorageMountShape` / `ArchiveSystemShape` | label, typed `:usesTechnology`/`:mountedOn`, `:mountPath` exactly 1, typed `:hasThroughput`/`:hasStorageCapacity` |
| `OperatingSystemShape` / `SoftwareShape` / `CompilerShape` / `ResourceManagerShape` | label + datatypes |

**`sh:Warning`** (quality, non-blocking):

* every named `:HPCResource` instance should have `rdfs:label`
  (`:QuantitativeValue` subclasses are exempt);
* `:hosts` / `:hostedAt` inverse consistency (SPARQL);
* `:decommissioningDate` ≥ `:commissioningDate` (SPARQL);
* recommended links (`:fundedBy`, `:hasStorageMount`, `:hasCoolingSystem`,
  `:hasPeakPerformance`, `:hasTotalAcceleratorMemory`, `:housedInRack`, …).

## Design decisions (and why)

1. **Two severities.** `Violation` = a TBox restriction or a hard datatype is
   broken (an instance is not usable). `Warning` = the instance is usable but
   incomplete/inconsistent. `allow_warnings=True` keeps warnings from making
   the run fail.

2. **`rdfs:domain` / `rdfs:range` are stripped from the inference graph.**
   With `inference="rdfs"`, a triple `x :operatedBy y` plus
   `:operatedBy rdfs:range :Organization` *infers* `y a :Organization`, which
   makes the `sh:class :Organization` check tautological (any wrong value
   passes). `validate.py` therefore keeps only `rdfs:subClassOf` (needed so
   `:ScalarNode` instances are checked by `ComputeNodeShape`) and drops
   domain/range. Use `--keep-domain-range` to disable this.

3. **The TBox is merged into the data graph.** pySHACL uses `ont_graph` only
   for inference and does **not** expose its triples to `sh:class`. TBox
   individuals such as `:SLURM`, `:GCC`, `:Lustre`, `:NFS` would look
   untyped. Merging the TBox into the data graph makes `sh:class :Compiler`
   work and still lets `rdfs:subClassOf` drive subclass targeting.

4. **`sh:BlankNodeOrIRI` instead of `sh:IRI`** for object properties whose
   values may be inline blank nodes (e.g. `[ a :CPUComponent ; … ]`);
   `sh:class` still enforces the intended type.

5. **Unit vocabularies come from the ABoxes** (`GB`, `GiB`, `TB`, `TiB`,
   `PB`, `PiB`, `GHz`, `Gb/s`, `GB/s`, `GiB/s`, `PFlop/s`, `W`), not from
   guesswork. `:hasValue` is `xsd:decimal` because every ABox value is
   written that way.

6. **Datatypes follow the TBox**, even where the ABoxes currently disagree
   (`:maxWallTime xsd:duration`, `:defaultWallTime xsd:string`).

## Verified behaviour

| Data | Result |
|---|---|
| no data (self-check) | ✅ CONFORMS |
| `example-hpc-center.ttl` | ✅ CONFORMS |
| `example-hpc-center-bad.ttl` | ❌ 16 violations + 1 warning, each mapping to one deliberate error |

The invalid example deliberately breaks: missing `:location`, `:operatedBy` a
`:Supercomputer`, missing `:hostedAt`, negative `:nodeCount`, string
`:totalCoresCount`, missing `:partitionName`, `:usesNodeType` a centre,
`xsd:string` `:maxWallTime`, `Gbps` throughput unit, missing `:mountPath`,
`:mountedOn` a centre, QoS without `rdfs:label`.

## Known gaps / TBox issues surfaced by the shapes

These are **not** enforced, on purpose, until the TBox is fixed:

* `:contains` and `:partOf` have no `rdfs:domain` / `rdfs:range`.
* `:hasProcessorComponent`, `:hasCPUComponent`, `:hasAcceleratorCardComponent`
  have a domain but no range.
* `:isParallel` is declared with domain `:FileSystemTechnology`, but the
  ABoxes use it on `:FileSystem` — the shape checks it on `:FileSystem`.
* `:FileSystemTechnology` individuals (`:Lustre`, `:NFS`, `:GPFS`, `:BeeGFS`)
  have no `rdfs:label` (they are not `:HPCResource`, so no shape fires).
* `:maxGpusPerQoS`, used by the IDRIS QoS, is not defined in the TBox.

## Extending

Add a `sh:NodeShape` with `sh:targetClass :YourClass` and `sh:property`
blocks. Re-run `python3 validate.py --data …`. New classes only need a shape
if they carry a TBox restriction or a datatype that must be checked.
