# Exa-AToW_onto

An ontology for describing the different aspects of the Exa-AToW project including HPC resources, system interactions, etc.

https://cnherrera.github.io/Exa-AToW_onto/index-en.html


## 🔍 Ontology concepts

This ontology models key entities and relationships involved in ExA-AToW (NumPEx PEPR):

Main entities under the ontology (list to be discuss) :
(In bold, those needed to be checked)


- **Job**: Concept that includes computational tasks, job descriptions, submission metadata, scheduling attributes, and runtime behavior in HPC environments.
- **HPC Resource**: Conceptual class encompassing physical and virtual resources involved in high-performance computing, including compute nodes, storage, interconnects, and infrastructure components.
- **ProcessorIndicatorEstimator**: Concept grouping all estimation tools, metrics, and models used to assess processor-related indicators such as power consumption, thermal footprint, and die size impact.
- **PhysicalCharacteristic**: Domain concept capturing the physical and structural properties of HPC components, such as memory capacity, die size, material lifetime, and energy efficiency attributes.
- **Workflow**: oncept grouping workflow-related entities such as execution steps, workflow engines, process definitions, dependencies, and orchestration strategies. Workflow properties are defined based on the paper Suter, F., et al. (2026). *A terminology for scientific workflow systems*. Future Generation Computer Systems, 174, 107974. https://doi.org/10.1016/j.future.2025.107974. 
- User: Concept encompassing individuals or agents who interact with the HPC system, including identity attributes, roles, permissions, and user behaviors.
- Authentication: Domain concept representing all aspects of authentication, including credentials, access protocols, identity validation, and login activities.


The ontology is serialized in Turtle (TTL) and can be used in semantic web applications and Linked Open Data (LOD) environments.

## Creation of the ontology -> For Exa-AToW partners! 
### main_classes.json
  File that describe each of the main aspects (entities) of the Exa-AToW project. 

### sub_HPC_classes.json
  JSON file describing the HPC Resources main class. 
  Each area of the project should ahve a JSON filw with this information.

  **Each partners should fill the information needed for their field**

example of entry (if entry is in the correct json file, then no need to add the parent_class):
```
  {
    "id": "ComputeNode",
    "parent_class": "HPCResource",
    "pref_label": {"en": "Node","fr": "Noeud"},
    "comment": {
       "en": "A physical or virtual server that executes computational jobs within a partition.",
       "fr": "Un serveur physique ou virtuel qui exécute des tâches de calcul au sein d'une partition."
    },
    "equivalent": ONTOLOGY.Name,
  },
```
## Adding properties



## Adding instances
In the ontology we will only add fixed instances.
Example:
```
    {
        "instance_name": "InMemory",
        "class_type": "DataManagementStorage",
        "pref_label": {"en": "In-Memory", "fr": "En mémoire"},
        "comment": {
            "en": "Data held in RAM.",
            "fr": "Données conservées en RAM."
        }

```

Other instances can be defined afterwards, when describing specific elements of the project.

```
from ontology_generator import ExaAToWOnto

onto =  ExaAToWOnto()
onto.add_instance(instance_name = "instance_naame", class_type = "class_type", pref_label = "pref_label", comment = "comment")
```


## 📁 Contents

- `exaatow-ontology.ttl`: Main ontology file
- `files/*.json`: JSON files describing each concept in the ontology, separated by classes.
- `docs/`: HTML documentation generated with Wicodo. (TBD)

## Recreation of the ontology in Python (rdflib)
This will be done at the project level. But if you wish to recreate the full ontology with additional information:
```
from ontology_generator import ExaAToWOnto

onto = ExaAToWOnto()
# we can add things here

onto.save_ontology("exaatoe_onto_vN.ttl", format="turtle")

```



## Visualization

To visualize the ontology:

- Use WebVOWL (through the ontology webpage generated with Widoco: XXXX)
- visualization tool in the Python file:
```
# After loading the ontology:

onto.visualize_graph(
    output_file="my_ontology_visualization.html",
    height="600px",
    physics=False  # Disable physics for static layout

# open the html file with a browser

```


## Ontology Concepts

Key classes include:

    HPCResource → CPU, GPU, RAM, SSD, etc.

    AuthenticationEntity → User, AccessToken, Session

    DieSize, Workload, MemoryCapacity as datatype-linked concepts



