# Exa-AToW HPC Resource Ontology

**Version:** 0.3  
**Prefix:** `exa-atow:`  
**Namespace:** `https://raw.githubusercontent.com/logistica-dev/exa-atow-ontologies/refs/heads/main/hpc_ontology/exaatow_hpc_ontology.ttl#`

---

## Purpose

This OWL/Turtle ontology models the physical and logical components of **French national HPC centers**, intended for use in a triple store queried by microservices. Key targets are:

| Center | Machine | Operator | Scheduler |
|--------|---------|----------|-----------|
| IDRIS (Orsay) | Jean Zay | CNRS | SLURM |
| CEA (Bruyères-le-Châtel) | Topaze / Joliot-Curie | CEA | PBS |
| Cines (Montpellier) | Adastra | Cines | SLURM |

The ontology supports describing HPC centers → supercomputers → hardware generations → compute nodes → processors/cards, and separately, SLURM partitions → node types → QoS, in a way that can be queried with SPARQL for automated configuration, documentation generation, or job submission guidance.

---

## File Structure

```
exaatow_hpc_ontology_v2.ttl   ← OWL ontology (Turtle)
exaatow_hpc_ontology.dot       ← Graphviz DOT for visualization
README.md                      ← This file
```

---

## Class Hierarchy Overview

```
owl:Thing
└── HPCResource
    ├── PhysicalResource
    │   ├── ComputeNode
    │   │   ├── ScalarNode            (CPU-only nodes)
    │   │   ├── AcceleratedNode       (CPU + GPU nodes)
    │   │   ├── FrontendNode          (login/submission)
    │   │   ├── PrePostNode           (pre/post-processing, e.g. jean-zay-pp)
    │   │   └── VisualizationNode     (GPU viz, e.g. jean-zay-visu)
    │   ├── Processor
    │   │   ├── CPU
    │   │   └── Accelerator
    │   │       └── GPU
    │   ├── AcceleratorCard           (physical card: e.g. NVIDIA A100 SXM4 80GB)
    │   ├── Core
    │   ├── Memory (volatile)
    │   │   ├── RAM
    │   │   └── HBMMemory             (GPU on-package HBM2e, HBM3)
    │   ├── Storage (persistent)
    │   │   ├── SSD
    │   │   │   └── NVMe              (local scratch)
    │   │   └── HDD
    │   ├── Interconnect
    │   │   ├── IntelOmniPath         (OPA 100 Gb/s, HPE SGI 8600 part of Jean Zay)
    │   │   ├── InfiniBand
    │   │   │   ├── InfiniBandHDR     (200 Gb/s)
    │   │   │   └── InfiniBandNDR     (400 Gb/s, Jean Zay H100 / gpu_p6)
    │   │   └── SlingShot             (HPE Cray 200 Gb/s, Adastra/Topaze)
    │   ├── Rack
    │   └── Server
    │
    ├── LogicalResource
    │   ├── Partition                 (SLURM partition, e.g. cpu_p1, gpu_p5, prepost)
    │   ├── FileSystem
    │   │   └── ParallelFileSystem
    │   │       ├── Lustre
    │   │       └── GPFS
    │   ├── StorageMount              ($HOME, $SCRATCH, $STORE, $WORK)
    │   └── QoS                       (SLURM quality of service class)
    │
    ├── System
    │   ├── Supercomputer
    │   ├── HPCCenter
    │   └── HardwareGeneration        (extension/phase, e.g. BullSequana XH3000 H100)
    │
    └── Infrastructure
        ├── CoolingSystem
        └── EnergyManagement

── (not subclass of HPCResource) ──────
Software
    ├── ResourceManager               (SLURM, PBS, LSF)
    ├── Compiler                      (GCC, Intel, NVCC, AOCC, Cray)
    ├── OperatingSystem
    ├── ParallelLibrary               (MPI, CUDA, OpenMP, ROCm)
    └── ModuleEnvironment             (Lmod, Environment Modules)

QuantitativeValue
    ├── DieSize, Lifetime, MemoryCapacity, StorageCapacity
    ├── Frequency, Bandwidth, Throughput
    ├── PowerConsumption → TDP
    └── PerformanceMetric → PeakPerformance

Organization
    └── FundingAgency

PartitionType
    ├── ComputePartition → CPUPartition / GPUPartition
    ├── PrePostPartition, VisualizationPartition
    ├── CompilationPartition, ArchivePartition
```

---

## Key Object Properties

| Property | Domain | Range | Notes |
|----------|--------|-------|-------|
| `hosts` | HPCCenter | Supercomputer | Center → machine |
| `operatedBy` | HPCCenter | Organization | |
| `fundedBy` | HPCCenter / Supercomputer | FundingAgency | e.g. GENCI, France 2030 |
| `hasPartition` | Supercomputer | Partition | Main partition link |
| `hasGeneration` | Supercomputer | HardwareGeneration | For multi-phase machines like Jean Zay |
| `composedOf` | Supercomputer | ComputeNode / Partition / Rack | |
| `hasPartitionType` | Partition | PartitionType | cpu/gpu/prepost/visu/compil |
| `hasQoS` | Partition | QoS | SLURM QoS classes |
| `usesNodeType` | Partition | ComputeNode | What nodes a partition exposes |
| `requiresModule` | Partition | SoftwareVersion | arch/a100, arch/h100 etc. |
| `equippedWith` | ComputeNode | Processor / AcceleratorCard / RAM / SSD / HDD | |
| `hasAcceleratorCard` | AcceleratedNode | AcceleratorCard | Explicit card link |
| `hostsAccelerator` | AcceleratorCard | Accelerator | Card → GPU chip |
| `belongsToPartition` | ComputeNode | Partition | Inverse of usesNodeType |
| `connectedVia` | ComputeNode | Interconnect | OPA or IB |
| `usesFileSystem` | Supercomputer | FileSystem | Lustre, GPFS |
| `hasStorageMount` | Supercomputer / HPCCenter | StorageMount | $HOME, $SCRATCH, $STORE |
| `mountedOn` | StorageMount | FileSystem | Which FS backs this mount |
| `hasPeakPerformance` | Supercomputer | PeakPerformance | e.g. 125.9 PFlop/s Jean Zay |
| `hasPowerConsumption` | Supercomputer / ComputeNode / Processor | PowerConsumption | |
| `gpuMemory` | GPU | MemoryCapacity | 16/32/80 GB |
| `hasTDP` | Processor | TDP | |
| `usesResourceManager` | Supercomputer | ResourceManager | |

---

## Key Datatype Properties

| Property | Domain | Range | Example |
|----------|--------|-------|---------|
| `shortName` | HPCResource | xsd:string | `"jean-zay"` |
| `location` | HPCCenter | xsd:string | `"Orsay, France"` |
| `documentationURL` | HPCCenter / Supercomputer / Partition | xsd:anyURI | IDRIS doc page |
| `partitionName` | Partition | xsd:string | `"gpu_p5"`, `"cpu_p1"` |
| `maxWallTime` | Partition | xsd:string | `"100:00:00"` |
| `defaultWallTime` | Partition | xsd:string | `"00:10:00"` |
| `allocatedFromQuota` | Partition | xsd:boolean | `false` for prepost/visu |
| `nodeCount` | Supercomputer / Partition | xsd:integer | `364` (gpu_p6) |
| `gpuCount` | ComputeNode | xsd:integer | `4`, `8` |
| `coreCount` | Processor | xsd:integer | `48` (Xeon Platinum 8468) |
| `socketCount` | ComputeNode | xsd:integer | `2` |
| `ramPerNode` | ComputeNode | xsd:integer | `512` (GB) |
| `model` | Processor | xsd:string | `"NVIDIA H100 SXM5"` |
| `architecture` | Processor | xsd:string | `"Hopper"`, `"Cascade Lake"` |
| `commissioningDate` | Supercomputer / HardwareGeneration | xsd:date | `"2019-01-01"` |
| `decommissioningDate` | Supercomputer / Partition … | xsd:date | |
| `mountPath` | StorageMount | xsd:string | `"$SCRATCH"` |
| `quota` | StorageMount | xsd:string | `"100 GB"` |
| `isPurged` | StorageMount | xsd:boolean | `true` for scratch |
| `hasValue` | QuantitativeValue | xsd:decimal | `125.9` |
| `hasUnit` | QuantitativeValue | xsd:string | `"PFlop/s"`, `"GB"` |

---

## Canonical Instances in the Ontology

The ontology ships with the following canonical instances ready to reference in your data:

**Resource Managers:** `exa-atow:SLURM`, `exa-atow:PBS`, `exa-atow:LSF`

**Compilers:** `exa-atow:GCC`, `exa-atow:IntelCompiler`, `exa-atow:NVCC`, `exa-atow:AOCC`, `exa-atow:CrayCC`

**Operating Systems:** `exa-atow:Linux`, `exa-atow:RedHat`, `exa-atow:Ubuntu`

---

## Instantiation Guide

Below is a quick sketch of how to create instances for Jean Zay. Full instance files should live in a separate Turtle file importing this ontology.

### HPC Center + Supercomputer

```turtle
@prefix exa-atow: <...#> .
@prefix xsd: <...> .

exa-atow:IDRIS rdf:type exa-atow:Organization ;
    rdfs:label "IDRIS" ;
    exa-atow:website "https://www.idris.fr"^^xsd:anyURI .

exa-atow:GENCI rdf:type exa-atow:FundingAgency ;
    rdfs:label "GENCI" .

exa-atow:IDRISCenter rdf:type exa-atow:HPCCenter ;
    exa-atow:shortName "idris" ;
    exa-atow:location "Orsay, France" ;
    exa-atow:operatedBy exa-atow:IDRIS ;
    exa-atow:hosts exa-atow:JeanZay .

exa-atow:JeanZay rdf:type exa-atow:Supercomputer ;
    rdfs:label "Jean Zay" ;
    exa-atow:shortName "jean-zay" ;
    exa-atow:commissioningDate "2019-06-01"^^xsd:date ;
    exa-atow:usesResourceManager exa-atow:SLURM ;
    exa-atow:fundedBy exa-atow:GENCI ;
    exa-atow:documentationURL "https://www.idris.fr/jean-zay/"^^xsd:anyURI .
```

### GPU (processor spec)

```turtle
exa-atow:H100_SXM5_80GB rdf:type exa-atow:GPU ;
    rdfs:label "NVIDIA H100 SXM5 80GB" ;
    exa-atow:model "NVIDIA H100 SXM5" ;
    exa-atow:architecture "Hopper" ;
    exa-atow:vendor "NVIDIA" ;
    exa-atow:coreCount 16896 .   # CUDA cores

exa-atow:H100_SXM5_80GB_Memory rdf:type exa-atow:MemoryCapacity ;
    exa-atow:hasValue "80"^^xsd:decimal ;
    exa-atow:hasUnit "GB" .
exa-atow:H100_SXM5_80GB exa-atow:gpuMemory exa-atow:H100_SXM5_80GB_Memory .
```

### AcceleratorCard

```turtle
exa-atow:Card_H100_SXM5 rdf:type exa-atow:AcceleratorCard ;
    rdfs:label "NVIDIA H100 SXM5 80GB card" ;
    exa-atow:vendor "NVIDIA" ;
    exa-atow:hostsAccelerator exa-atow:H100_SXM5_80GB .
```

### Compute Node (AcceleratedNode)

```turtle
# Template for a Jean Zay gpu_p6 node (quad-H100)
exa-atow:JeanZay_gpu_p6_NodeType rdf:type exa-atow:AcceleratedNode ;
    rdfs:label "Jean Zay gpu_p6 node (4x H100)" ;
    exa-atow:gpuCount 4 ;
    exa-atow:socketCount 2 ;
    exa-atow:ramPerNode 512 ;
    exa-atow:linkCount 4 ;          # 4 NDR InfiniBand links
    exa-atow:hasAcceleratorCard exa-atow:Card_H100_SXM5 ;
    exa-atow:connectedVia exa-atow:InfiniBandNDR .
```

### Partition

```turtle
exa-atow:Partition_gpu_p6 rdf:type exa-atow:Partition ;
    rdfs:label "Jean Zay gpu_p6 (H100 partition)" ;
    exa-atow:partitionName "gpu_p6" ;
    exa-atow:nodeCount 364 ;
    exa-atow:maxWallTime "100:00:00" ;
    exa-atow:defaultWallTime "00:10:00" ;
    exa-atow:allocatedFromQuota true ;
    exa-atow:hasPartitionType exa-atow:GPUPartition ;
    exa-atow:usesNodeType exa-atow:JeanZay_gpu_p6_NodeType ;
    exa-atow:documentationURL 
        "https://www.idris.fr/eng/jean-zay/gpu/jean-zay-gpu-exec_partition_slurm-eng.html"^^xsd:anyURI .

exa-atow:JeanZay exa-atow:hasPartition exa-atow:Partition_gpu_p6 .
```

---

## Changes from v0.2 → v0.3

### Bug Fixes

1. **RAM wrongly placed under `Storage`** — RAM is volatile memory, not persistent storage. Introduced `exa-atow:Memory` as a separate sibling branch under `PhysicalResource`. `RAM` and `HBMMemory` are now under `Memory`; `SSD` and `HDD` remain under `Storage`.

2. **`ScalarNode` used `owl:minCardinality 1` without a property** — removed the malformed bare cardinality restriction (it was missing `owl:onProperty`).

3. **`exa-atow:website` domain was only `Software`** — broadened to also cover `HPCCenter` and `Organization`.

4. **`exa-atow:vendor` domain did not include `AcceleratorCard`** — fixed.

5. **`exa-atow:hasCore` was declared as `owl:ObjectProperty` but embedded in the `## Datatype Properties` section** — moved to the Object Properties block.

6. **`PerformanceMetric` was not connected to the hierarchy** — it was an isolated class; `PeakPerformance` is now properly linked to it.

### New Classes

| Class | Why Added |
|-------|-----------|
| `Accelerator` | Parent of `GPU`; allows future FPGAs, IPUs, etc. |
| `AcceleratorCard` | Physical card (e.g. A100 SXM4 80 GB); critical for instance modeling |
| `HBMMemory` | High Bandwidth Memory on GPU; different from node DRAM |
| `Memory` | Proper volatile memory hierarchy (RAM, HBM) |
| `NVMe` | Local scratch storage on modern nodes |
| `HardwareGeneration` | Models Jean Zay's multi-phase architecture (HPE SGI 8600 + BullSequana XH3000) |
| `PrePostNode` | Dedicated prepost node (e.g. `jean-zay-pp`); maps to `prepost` partition |
| `VisualizationNode` | Dedicated viz node (e.g. `jean-zay-visu`) |
| `StorageMount` | User-facing mount ($HOME, $SCRATCH, $STORE, $WORK) with quota/purge info |
| `QoS` | SLURM Quality of Service class per partition |
| `CPUPartition` / `GPUPartition` | Finer partition type distinction |
| `InfiniBandHDR` | HDR 200 Gb/s (complement to existing NDR) |
| `SlingShot` | HPE Cray Slingshot for Adastra/Topaze |
| `PowerConsumption` + `TDP` | Energy/environmental analysis use case |
| `ParallelLibrary` | MPI, CUDA, OpenMP, ROCm |
| `ModuleEnvironment` | Lmod, Environment Modules |
| `FundingAgency` | GENCI, ANR, France 2030 |

### New Object Properties

`hasGeneration`, `hasAcceleratorCard`, `hostsAccelerator`, `fundedBy`, `hasPartition`, `hasQoS`, `usesNodeType`, `requiresModule`, `hasStorageMount`, `mountedOn`, `hasTDP`, `hasPowerConsumption`

### New Datatype Properties

`architecture`, `socketCount`, `ramPerNode`, `maxWallTime`, `defaultWallTime`, `allocatedFromQuota`, `mountPath`, `quota`, `isPurged`, `documentationURL`

---

## Visualizing the Ontology

The `.dot` file can be rendered with [Graphviz](https://graphviz.org/):

```bash
# SVG (recommended for zoom)
dot -Tsvg exaatow_hpc_ontology.dot -o exaatow_hpc_ontology.svg

# PNG
dot -Tpng -Gdpi=150 exaatow_hpc_ontology.dot -o exaatow_hpc_ontology.png

# PDF
dot -Tpdf exaatow_hpc_ontology.dot -o exaatow_hpc_ontology.pdf
```

Or open/paste into an online renderer such as [Edotor](https://edotor.net/) or [Graphviz Online](https://dreampuf.github.io/GraphvizOnline/).

**Color coding in the DOT diagram:**

| Color | Meaning |
|-------|---------|
| Dark navy | Top-level root (HPCResource) |
| Blues | Physical resources: nodes, processors, interconnects |
| Greens | Processor sub-hierarchy |
| Purple | Memory & quantitative values |
| Brown/orange | Persistent storage |
| Gold/yellow | Logical resources: partitions, file systems, mounts |
| Red shades | Partition types |
| Dark grey | Systems: HPCCenter, Supercomputer |
| Dashed borders | Software classes |

---

## Validation

Use a SHACL validator or OWL reasoner (e.g. HermiT, Pellet) after populating instances. Recommended tools:

- [Apache Jena / RIOT](https://jena.apache.org/documentation/io/) — syntax check: `riot --validate ontology.ttl`
- [ROBOT](http://robot.obolibrary.org/) — OWL reasoning and validation
- [Protégé](https://protege.stanford.edu/) — visual editing and reasoner integration

---

## License

© Exa-AToW team. See project repository for license details.
