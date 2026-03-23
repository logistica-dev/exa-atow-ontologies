# Exa-AToW HPC Resource Ontology


https://cnherrera.github.io/Exa-AToW_onto/hpc_ontology/exaatow_hpc_ontology.ttl

https://cnherrera.github.io/Exa-AToW_onto/hpc_ontology/grafo_full_Exa-AToW_HPC.html

The Exa-AToW HPC Ontology is an OWL 2 DL knowledge representation designed to formally describe the hardware, software, storage infrastructure, and organizational structure of High-Performance Computing (HPC) centers. It was developed within the Exa-AToW project as the semantic backbone for describing and comparing the French national supercomputing ecosystem.

The ontology enables answering structured queries such as:
- Which partitions provide access to NVIDIA H100 GPUs?
- Which systems use Slurm?
- What storage mounts are available to compute jobs?
- How does Adastra's AMD ROCm stack differ from Jean Zay's CUDA-based environment?

By encoding these facts as machine-readable RDF triples, the ontology supports interoperability, automated documentation, and integration with other semantic resources.


## Widoco
Link to Widoco

## Visualization
Link to nice visualization in a Knowledge Graph.


## What is inside?

The ontology is organized around five disjoint top-level branches:

| Branch  | definition  | Key subclasses  |
|---|---|---|
| HPC Center  | Institutional entity that operates and hosts one or more supercomputers.  |   |
| Organization  | Entité légale qui exploite, possède ou finance des installations HPC.  | Funding Agency    |
| Quantitative Value  | A value with an associated unit of measurement.  | Die Size, Memory Capacity, Lifetime, ... |
| HPC Resource  | All resources involved in high-performance computing.  | Infrastracture, Logical Resource (Software, Partition, etc), Physical resource (Supercomputer, ComputeNode, CPU, GPU, ...) |


HPC Center → *hosts* → Supercomputer → *composed of* → ComputeNode → *equipped with* →  CPUs / GPUs

---
## Validation
SHACL Shapes to be defined.


---

## License

© Exa-AToW team. See project repository for license details.
