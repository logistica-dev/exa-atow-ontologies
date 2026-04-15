# Exa-AToW HPC Resource Ontology

A vocabulary for describing supercomputers — their hardware, software, storage, and the organizations that run them. Built for the Exa-AToW project



## Widoco
Link to Widoco

## Visualization
Link to nice visualization in   Knowledge graph


## What is inside?
Supercomputers  →  composed of  →  Compute Nodes  →  equipped with  →  CPUs / GPUs
     │                                                                       │
     ├── Partitions (SLURM/PBS)  →  Quality of Service (QoS) classes        │
     ├── File Systems  →  Storage Mounts ($HOME, $SCRATCH, $WORK…)          │
     ├── Software (compilers, MPI libs, resource managers)                   │
     └── Infrastructure (cooling, power, PDUs)                               │
                                                                             TDP / Die Size / Process Node
HPC Centers  →  operated by  →  Organizations  →  funded by  →  Funding Agencies



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

Or open/paste into an online renderer such as [Graphviz Online](https://dreampuf.github.io/GraphvizOnline/).



---

## Validation
Shapes is used as SHACL validator. 


---

## License

© Exa-AToW team. See project repository for license details.
