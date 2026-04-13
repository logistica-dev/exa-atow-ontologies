# Exa-AToW HPC Resource Ontology


| Resource | Link |
|---|---|
| Ontology (TTL) | https://cnherrera.github.io/Exa-AToW_onto/hpc_ontology/exaatow_hpc_ontology.ttl |
| Knowledge Graph viewer | https://cnherrera.github.io/Exa-AToW_onto/hpc_ontology/grafo_full_Exa-AToW_HPC.html |
| Widoco documentation | *(link to be added)* |

## Overview

The **Exa-AToW HPC Ontology** is an OWL 2 DL knowledge representation designed to formally describe the hardware, software, storage infrastructure, and organizational structure of High-Performance Computing (HPC) centers. It was developed within the Exa-AToW project as the semantic backbone for describing and comparing the French national supercomputing ecosystem.

It enables answering structured SPARQL queries such as:
- Which partitions provide access to NVIDIA H100 GPUs?
- Which systems use Slurm?
- What storage mounts are available to compute jobs?
- How does Adastra's AMD ROCm stack differ from Jean Zay's CUDA-based environment?

By encoding these facts as machine-readable RDF triples, the ontology supports interoperability, automated documentation, and integration with other semantic resources such as the PIE environmental impact ontology.



## Architecture

The ontology is organized around five disjoint top-level branches:

| Branch  | Information  |   |
|---|---|---|
| HPC Center  | *Definition:* Institutional entity that operates and hosts one or more supercomputers. <br> | ![HPC Center](images/HPCCenter.png)  |
| Organization  | *Definition:* Entité légale qui exploite, possède ou finance des installations HPC. <br> *Key Classes:* Funding Agency    |  ![Organization](images/Organization.png)  |
| Quantitative Value  | *Definition:* A value with an associated unit of measurement.  <br> *Key Classes:* Die Size, Memory Capacity, Lifetime, ... |  ![Quantitative Value](images/QuantitativeValue.png)  |
| HPC Resource  | *Definition:* All resources involved in high-performance computing. <br> *Key Classes:* Infrastracture, Logical Resource (Software, Partition, etc), Physical resource (Supercomputer, ComputeNode, CPU, GPU, ...) | ![HPC Resource](images/HPCResource.png)   |



| Branch | Description | Key classes |
|---|---|---|
| **PhysicalResource** | All tangible hardware | `Supercomputer`, `ComputeNode`, `HardwareModel`, `HardwareComponent` and all their subclasses |
| **LogicalResource** | Software-defined or scheduler-visible resources | `Partition`, `QoS`, `FileSystem`, `StorageMount`, `Software` and subclasses |
| **Infrastructure** | Facility-level support systems | `CoolingSystem`, `EnergyManagement`, `PowerDistributionUnit` |
| **QuantitativeValue** | Typed numeric values with units | `TDP`, `NominalPower`, `Frequency`, `Bandwidth`, `MemoryCapacity`, `PeakPerformance`, … |
| **Organization** *(independent)* | Institutions operating or funding centers | `FundingAgency` |
| **HPCCenter** *(independent)* | Institutional host of one or more supercomputers | — |

### Core design pattern: HardwareModel vs HardwareComponent

A central design decision separates **abstract hardware specifications** (`HardwareModel`) from **contextualized instantiations** (`HardwareComponent`):

```
ComputeNode
  ├─ hasCPUComponent ──────────► CPUComponent
  │                                  ├─ refersToModel ──► CPU (e.g. AMD EPYC 9654)
  │                                  └─ quantity: 2
  ├─ hasAcceleratorCardComponent ► AcceleratorCardComponent
  │                                  ├─ refersToModel ──► AcceleratorCard (e.g. MI250X)
  │                                  └─ quantity: 4
  ├─ hasMemoryComponent ──────────► MemoryComponent
  │                                  ├─ refersToModel ──► RAM / HBMMemory
  │                                  └─ quantity: 1
  ├─ hasInterconnectComponent ────► InterconnectComponent
  │                                  ├─ refersToModel ──► Interconnect (e.g. Slingshot)
  │                                  └─ linkCount: 1..4
  └─ hasStorageComponent ─────────► StorageComponent
                                     ├─ refersToModel ──► SSD / HDD
                                     └─ quantity: 4
```


Example:

HPC Center → *hosts* → Supercomputer → *composed of* → ComputeNode → *equipped with* →  CPUs / GPUs

![HPC Center](images/HPCCenter-chain-CPUGPU.png)

### Energy calculation path

The ontology was designed to feed energy microservices (PUE estimation, carbon footprint):

```
Partition
  └─ usesNodeType ──► ComputeNode
                         ├─ hasNominalPower ──► NominalPower  (e.g. 945 W / scalar node)
                         ├─ hasCPUComponent
                         │    └─ refersToModel ──► CPU ──► hasTDP ──► TDP  (e.g. 360 W)
                         └─ hasAcceleratorCardComponent
                              └─ refersToModel ──► AcceleratorCard ──► hasTDP ──► TDP  (e.g. 560 W)
```

`NominalPower` (on `ComputeNode`) captures the full node power budget including DRAM and board overhead, derived from the Adastra documentation formula:
> *945 W = 360 W/socket × 2 + 100 W DRAM + 125 W other (scalar node)*  
> *2670 W = 180 W CPU + 70 W DRAM + 560 W × 4 MI250X + 180 W other (GPU node)*

`TDP` (on `Processor` and `AcceleratorCard`) captures the manufacturer-specified per-component thermal design power.

---


---
## Validation
SHACL Shapes to be defined.


---

## License

© Exa-AToW team. See project repository for license details.
