# Exa-AToW Ontologies

The **[Exa-AToW](https://numpex.org/exaatow-architectures-and-tools-for-large-scale-workflows/)** (Architectures and Tools for Large-Scale Workflows) project, part of the [NumPEx](https://numpex.org/) PEPR, aims at providing solutions for the efficient management of large-scale workflows composed of HPDA, AI, and HPC tasks distributed over a continuum of resources ranging from Exascale and HPC infrastructures to data infrastructures. 

This repository contains the formal ontologies developed for the project. They provide a structured, semantic representation of the concepts, relationships, and constraints needed to describe:

- **workflows** and their execution,
- **HPC resources and infrastructures**,
- **environmental impacts** of HPC jobs and resources,
- and the **application services** that publish and execute jobs.

> This README gives the global view and the interaction between ontologies. Detailed specifications are maintained in each ontology folder.


## 1. Quick links

| Resource | Link |
|---|---|
| Integrated ontology documentation | [index.html](https://cnherrera.github.io/Exa-AToW_onto/index.html)  - *to be updated*|
| Integrated ontology source | [`exaatow_ontology.ttl`](exaatow_ontology.ttl) - *to be updated* |
| Workflow ontology | [`workflow_ontology/`](workflow_ontology/) · [README](workflow_ontology/readme.md) · [documentation](https://cnherrera.github.io/Exa-AToW_onto/workflow_ontology/index-en.html) |
| HPC Resource ontology | [`hpc_ontology/`](hpc_ontology/) · [README](hpc_ontology/README.md) · [documentation](https://cnherrera.github.io/Exa-AToW_onto/hpc_ontology/index.html) |
| PIE / Impacts-HPC ontology | [`impactsHPC_ontology/`](impactsHPC_ontology/) · [README](impactsHPC_ontology/README.md) |
| Application Services ontology | [`application-services/`](https://gitlab.com/ontologies_exa_atow/application-services/) · [README](https://gitlab.com/ontologies_exa_atow/application-services/README.md) |
| Multi-ontology viewer | [`tools/onto_visualization/`](tools/onto_visualization/) · [Onto Viewer](https://cnherrera.github.io/Exa-AToW_onto/tools/onto_visualization/onto-viewer.html)|
|  -- Partner construction guide | [Ontology Construction Guide for Exa-AToW Partners](#ontology-construction-guide-for-exa-atow-partners) - *to be updated*|


---

## 2. Ontology landscape

The repository is organised as a set of domain ontologies plus one integration layer.

| Layer | Location | Main files | Namespace | Purpose |
|---|---|---|---|---|
| **Integrated ontology** | repository root | `exaatow_ontology.ttl` | imports domain namespaces | Imports the three core domain ontologies and adds cross-domain alignments |
| **Workflow Ontology** | `workflow_ontology/` | `workflow_ontology.ttl`, `` | `https://w3id.org/Exa-AToW/exato-wf.ttl#` | Describes workflows, steps, parameters, data, engines, execution, provenance, and workflow properties |
| **HPC Resource Ontology** | `hpc_ontology/` | `hpc-core.ttl`, `hpc.ttl` | `https://w3id.org/Exa-AToW/hpc#` | Describes HPC centres, supercomputers, partitions, nodes, hardware, software, storage, and infrastructure |
| **PIE / Impacts-HPC Ontology** | `impactsHPC_ontology/` | `PIE.ttl`| `https://gitlab.aqmo.org/grichet/impacts-hpc/-/raw/main/ontology/PIE.ttl` | Describes environmental impact assessment for jobs, servers, clusters, and components |
| **Application Services Ontology** | Gitlab [Application Services](https://gitlab.com/ontologies_exa_atow/application-services) | `AaaS ontology.ttl` | `http://www.semanticweb.org/grichet/ontologies/applicationServices/` | Emerging ontology for HAPS, runtimes, runners, and jobs |

### What each ontology answers

- **Workflow Ontology** — *What is the workflow, what are its steps and dependencies, how is it executed, and where does its data come from?*
- **HPC Resource Ontology** — *Where does it run, on which centre, system, partition, node, accelerator, storage, or software stack?*
- **PIE / Impacts-HPC Ontology** — *What is the environmental impact of the job, server, cluster, or component, and how was that impact estimated?*
- **Integration layer** — *How do these three views connect into one knowledge graph?*

---

## 3. Workflow Ontology

The **Workflow Ontology** describes scientific and computational workflows, their execution environments, provenance, and interoperability across heterogeneous Workflow Management Systems.

It aligns with **PROV-O**, **WF4EVER** (`wfdesc` / `wfprov`), **PAV**, and the workflow-property framework of [Suter et al. (2026)](https://doi.org/10.1016/j.future.2025.107974)** . It models workflows, steps, dependencies, input/output parameters, data artefacts, execution environments, engines, execution status, and workflow properties such as granularity, modularity, flow type, and coupling.

The folder also contains a **CWL extension** and an active development package with SHACL shapes, a CWL-to-RDF pipeline, tests, and examples. Two workflow tracks currently coexist: the published bundle used by the integrated ontology and the more recent `development/` package.

Detailed specification: [`workflow_ontology/readme.md`](workflow_ontology/readme.md).

--- 

## 4. HPC Resource Ontology

The **HPC Resource Ontology** is an OWL 2 DL representation of HPC centres, their hardware, software, storage, and organisational structure. It supports describing and comparing systems such as CINES/Adastra, IDRIS/Jean Zay, and TGCC/Irène.

It is published as two modules sharing one namespace:

- **`hpc-core.ttl`** — minimal vocabulary: supercomputers, partitions, nodes, hardware models/components, storage, software, organisations.
- **`hpc.ttl`** — imports the core and adds infrastructure, interconnects, cooling, power distribution, file systems, mounts, QoS, and performance metrics.

A key design pattern separates **`HardwareModel`** (abstract model, e.g. NVIDIA H100) from **`HardwareComponent`** (a concrete installed instance). The ontology also provides quantitative values such as `TDP`, `NominalPower`, `DieSize`, and `MemoryCapacity`, which feed energy and impact calculations.

Detailed specification: [`hpc_ontology/README.md`](hpc_ontology/README.md).

---

## 5. PIE / Impacts-HPC Ontology

The **PIE / Impacts-HPC Ontology** defines the conceptual framework behind the [Impacts-HPC](https://gitlab.in2p3.fr/impacts-hpc/impacts-hpc) library.

It models physical HPC entities such as server parks, clusters, servers, processors, CPUs, GPUs, memory, storage, power supplies, cooling, and batteries; jobs as impact-assessed objects; environmental impact estimations (embodied, usage, and embedded); impact categories such as **ADPE**, **GWP**, and **PEC**; and allocation methods used to attribute impacts to a job.

The canonical PIE files are in `impactsHPC_ontology/`. The `pie_ontology/` folder is currently a placeholder.

Detailed specification: [`impactsHPC_ontology/README.md`](impactsHPC_ontology/README.md).

---

## 6. AaaS Ontology

The Exa-AToW Application Services ontology is an OWL ontology that describes the main concepts involved in Application Services. It provides a common vocabulary and a semantic model for describing HAPS, Runtimes, and Jobs deployed through these services.

Once populated with instances, the ontology will support queries such as:
- On which HPC centres can a given application be executed, and who is responsible for its execution at each centre?
- Which applications are available?
- What inputs and outputs are expected by a given application?
The ontology's vocabulary and properties are derived from the Application Services documentation.

Currently hosted in Gitlab.

Detailed specification: [`application-services/README`](https://gitlab.com/ontologies_exa_atow/application-services/README.md) 


## 7. Integration layer - To be updated

The root file [`exaatow_ontology.ttl`](exaatow_ontology.ttl) imports the Workflow, HPC, and PIE ontologies and adds cross-domain mappings.

Representative mappings include:

| From | Mapping | To |
|---|---|---|
| `hpc:Processor` | `owl:equivalentClass` | `pie:processor` |
| `hpc:CPU` | `owl:equivalentClass` | `pie:cpu` |
| `hpc:GPU` | `owl:equivalentClass` | `pie:gpu` |
| `hpc:RAM` | `owl:equivalentClass` | `pie:ram` |
| `hpc:SSD` | `owl:equivalentClass` | `pie:ssd` |
| `hpc:HDD` | `owl:equivalentClass` | `pie:hdd` |
| `hpc:Server` | `owl:equivalentClass` | `pie:server` |
| `hpc:Supercomputer` | `rdfs:subClassOf` | `pie:park` |
| `hpc:Partition` | `rdfs:subClassOf` | `pie:cluster` |
| `hpc:HPCResource` | `rdfs:subClassOf` | `pie:impactAssessedObject` |
| `hpc:coresCount` | `owl:equivalentProperty` | `pie:coresNumber` |

The integration layer also defines links such as:

- `exawf:utilizesHPCResource` — workflow `ExecutionEnvironment` → `hpc:HPCResource`.
- `exawf:executedOnPartition` — workflow `Execution` → `hpc:Partition`.
- `exawf:usesComputeNode` — workflow `WorkflowStep` → `hpc:ComputeNode`.
- `exawf:hasEnvironmentalImpact` — workflow entity → `pie:impactEstimation`.
- `exawf:WorkflowExecutionContext` — combines a workflow execution, the HPC infrastructure used, and the associated environmental impact.

The integration file is maintained centrally. Domain modules should not redefine these terms; propose new cross-domain mappings to the ontology coordinators.

> Some mappings still use older IRIs than the current domain modules, and some alignments are provisional. Verify the exact IRI before reuse.
> **Status:** the integration file also contains some provisional alignments that are still under discussion. Treat cross-domain mappings as reviewable design decisions, not as immutable facts.


---

## 8. Repository structure

```text
Exa-AToW_onto/
├── exaatow_ontology.ttl                 # Integrated ontology: imports + cross-domain alignments
├── index.html                           # Widoco documentation for the integrated ontology
├── README.md                            # Current README
├── Steps_generate_ontology.md           # Partner guide to generate ontologies (JSON examples obsolete)
│
├── workflow_ontology/
│   ├── exaatow_workflow_ontology.ttl    # Published workflow bundle (v0.1)
│   ├── exato-wf-cwl-extension.ttl       # CWL extension (v0.1)
│   ├── separate_data/
│   │   ├── exato-wf.ttl                 # Modular workflow core (v0.2)
│   │   └── exato-data.ttl               # Data/provenance module
│   ├── examples/kinetic_energy/         # End-to-end CWL → RDF example
│   ├── tools/                           # CWL-to-TTL helpers
│   ├── use_cases/                       # Use-case material
│   ├── index-en.html                    # Workflow documentation
│   ├── readme.md                        # Workflow README
│   └── resources/, webvowl/
│
├── hpc_ontology/
│   ├── hpc-core.ttl                     # Core HPC TBox (v0.3.0)
│   ├── hpc.ttl                          # Full HPC TBox (v0.3.0, imports core)
│   ├── instances/                       # ABox: centres, CINES, IDRIS, TGCC
│   ├── shapes/                          # SHACL shapes + validator + examples
│   ├── jena/                            # Fuseki/TDB2, SPARQL queries, Python client, chatbot
│   ├── graphs/                          # DOT sources and SVG diagrams
│   ├── query/, resources/, images/, webvowl/
│   ├── index.html                       # HPC documentation
│   └── README.md                        # HPC README
│
├── impactsHPC_ontology/                 # PIE ontology
│   ├── PIE.ttl
│   ├── PIE.rdf
│   ├── ontology_graph.jpg
│   └── README.md
├── pie_ontology/                        # Placeholder only (no ontology files yet)
├── resources/                           # Shared documentation assets
└── webvowl/                             # Bundled WebVOWL assets
```

### Notes on the structure

- **Published ontology modules** are the `.ttl` files in `workflow_ontology/`, `hpc_ontology/`, `impactsHPC_ontology/`, and the root integration file.
- **`pie_ontology/`** is currently an empty placeholder. Use `impactsHPC_ontology/` for PIE.
- **`files/` and `ontology_generator.py` are legacy.** The JSON-based generation workflow is retired. Do not add new JSON definitions or run the old generator for new ontology work.
- **`Steps_generate_ontology.md`** remains useful for its conceptual explanations of classes, object properties, data properties, instances, and restrictions. Its JSON mechanics no longer apply; use the OWL/Turtle guide in the next section instead.
- Generated documentation (`index-en.html`, `index.html`, WebVOWL data) should be regenerated through the agreed tooling rather than edited by hand.

---


## 9. Validation, querying, and visualisation

### 9.1 SHACL

- HPC: `hpc_ontology/shapes/hpc-shapes.ttl` and `hpc_ontology/shapes/validate.py`.
- Workflow: `workflow_ontology/exato-wf-cwl-shapes.ttl`.

Example:

```bash
cd hpc_ontology/shapes
python3 validate.py --data example-hpc-center.ttl
python3 validate.py --data ../instances/hpc-centers.ttl \
                              ../instances/hpc-instances-cines.ttl \
                              ../instances/hpc-instances-idris.ttl \
                              ../instances/hpc-instances-tgcc.ttl
```

### 9.2 SPARQL with Apache Jena / Fuseki

Example in the HPC ontology.
See the beginner-friendly guide in [`hpc_ontology/jena/README.md`](hpc_ontology/jena/README.md).

```bash
cd hpc_ontology/jena
make serve
```

Then open `http://localhost:3030` and query the `hpc` dataset, or use the Python client in `hpc_ontology/jena/python/`.

### 9.3 Visualisation - to be updated

- The multi-ontology viewer is in [`tools/onto_visualization/`](tools/onto_visualization/).
- It can load the Workflow, HPC, and PIE TBoxes plus HPC and workflow ABoxes, and it detects shared instances across sources.
- WebVOWL bundles are available in `webvowl/`, `workflow_ontology/webvowl/`, and `hpc_ontology/webvowl/`.
- Widoco documentation is generated in `index-en.html` (integrated), `workflow_ontology/index-en.html`, and `hpc_ontology/index.html`.

---

## 10. Contributing

- Use the repository issue tracker for questions, bug reports, and ontology-change proposals.
- Discuss new top-level concepts, namespaces, or cross-domain mappings with the ontology coordinators before implementing them.
- Keep changes focused and reviewable.
- Include validation evidence in pull requests.
- Follow the partner construction guide above.

---

## 11. License

Licensing is specified in the individual ontology folders and in the upstream project. The Workflow Ontology README states **CC-BY 4.0**; check the relevant folder README and repository metadata for the other modules before redistributing.

---

## 12. Contact

For questions, issues, or contributions, use the repository issue tracker:

- [Exa-AToW ontology repository issues](https://github.com/logistica-dev/exa-atow-ontologies/issues)

For ontology-specific questions, see the contacts and links in:

- [`workflow_ontology/readme.md`](workflow_ontology/readme.md)
- [`hpc_ontology/README.md`](hpc_ontology/README.md)
- [`impactsHPC_ontology/README.md`](impactsHPC_ontology/README.md)
- [`application-services/README.md`](https://gitlab.com/ontologies_exa_atow/application-services/README.md)
