# Exa-AToW Ontology

This ontology models the core entities and relationships involved in the **Exa-AToW**  project (part of the NumPEX PEPR initiative), focusing on high-performance computing (HPC) workflows, resources, and user interactions.

The ontology is serialized in **Turtle (TTL)** format and can be used in **Semantic Web** applications and **Linked Open Data (LOD)** environments.

https://cnherrera.github.io/Exa-AToW_onto/index-en.html


## 🔍 Ontology Concepts

The ontology defines key concepts for the ExA-AToW ecosystem:
(*Bold items indicate concepts that are under review*)
- **Job**: Represents computational tasks, job descriptions, submission metadata, scheduling attributes, and runtime behavior in HPC environments.
- **HPCResource**: Covers physical and virtual resources in HPC, including compute nodes, storage, interconnects, and infrastructure.
- **ProcessorIndicatorEstimator**: Groups estimation tools, metrics, and models used to assess processor indicators such as power consumption, thermal footprint, and die size.
- **PhysicalCharacteristic**: Captures physical and structural properties of HPC components like memory capacity, die size, material lifetime, and energy efficiency.
- **Workflow**: Encompasses workflow-related entities such as execution steps, workflow engines, orchestration strategies, and dependencies. Based on:  
  > Suter, F., et al. (2026). *A terminology for scientific workflow systems*. FGCS 174, 107974. [DOI](https://doi.org/10.1016/j.future.2025.107974)
- User: (TBD) Describes individuals or agents interacting with HPC systems, including identity attributes, roles, and behaviors.
- Authentication: (TBD) Models authentication concepts including credentials, identity validation, access protocols, and login activities.
- Digital Twins: (TBD)


## Ontology Construction: For Exa-AToW partners!

![Ontology construction description](resources/ontology_collaboration_description.png)


### `main_classes.json`
Describes each main concept (entity) in Exa-AToW. 

### sub_HPC_classes.json
  JSON file describing the HPC Resources main class. 
  Each area of the project should ahve a JSON filw with this information.

#### Entry example
Each project area should have its own JSON file using the same structure. This, ech partner should fill the required information.

`parent_class' can be omitted if the entry directly belongs (subclassOf) the class designed in the name of the JSON file.

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

### Property Definitions
**Goal**: define relationships between *existing* classes using JSON property definitions.
For example, connect a `Processor' class to a `DieSize' class using a `hasDieSize' property.
Example:
```
{
    "id": "hasDieSize",
    "property_type": "DatatypeProperty",    
    "domain": "Processor",
    "range": "DieSize",
    "pref_label": {
    "en": "has die size",
    "fr": "a taille de puce"
    },
    "comment": {
    "en": "Processor has a die size, including a numeric value and a unit (e.g., mm2).",
    "fr": "Processeur a une taille de puce, incluant une valeur numérique et une unité (ex : mm2)."  
    }
}
```

### Steps:
**Option 1**: Add to existing file
Add your property to an existing properties*.json file if it fits that domain.

**Option 2**: Create new file
- Create a new file: properties_<your_field>.json (in files folder)
- Add your properties as an array
- Register the file in list_properties.json in the 'ontology_generator.py' file

## Adding instances
Only fixed instances will be included in the ontology.
To create instances for your area, create a JSON file with each instance defined as this (also see files/instances_workflow.json): 
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


## 📁 Contents

- `exaatow-ontology.ttl`: Main ontology file
- `files/*.json`: JSON files describing each concept in the ontology, separated by classes, properties and fixed instances.
- `docs/`: HTML documentation generated with Wicodo. (TBD)

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



