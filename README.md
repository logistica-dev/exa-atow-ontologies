# Exa-AToW_onto
# HPC Authentication Ontology

An ontology for describing authentication, HPC resources, and system interactions in an environment integrating **Keycloak**, **Digital Twins**, and **HPC job scheduling (Buffers)**.

## 🔍 Description

This ontology models key entities and relationships involved in ExA-AToW (NumPEx PEPR):

- **HPC resources** (e.g., CPU, GPU, RAM)
- **Energy consumption**
- **Digital Twin interactions**
- **Dynamic resource allocation** through Buffers
- **Workflows**
- **Authentication**

and:
- **Physical Characteristics**: including objects not directly linked to any of the main entities, but being a physical property of them.

The ontology is serialized in Turtle (TTL) and can be used in semantic web applications and Linked Open Data (LOD) environments.

## Creation of the ontology->  Exa-AToW partners:
- main_classes.json file describe each of the main aspects (entities) of the Exa-AToW project. 
For each aspect of the project, there is a json file fill the information.

example of entry (if entry is in the correct json file, then no need to add the parent_class):
```
  {
    "id": "ComputeNode",
    "parent_class": "HPCResource",
    "pref_label": {"en": "Node","fr": "Noeud"},
    "comment": {
       "en": "A physical or virtual server that executes computational jobs within a partition.",
       "fr": "Un serveur physique ou virtuel qui exécute des tâches de calcul au sein d'une partition."
    }
  },
```


## 📁 Contents

- `ontology.ttl`: Main ontology file
- `ontology.json`: JSON serialization for WebVOWL visualization
- `docs/`: HTML documentation generated with [Widoco](https://github.com/dgarijo/Widoco)

## Recreation of the ontology in Python (rdflib)
This will be done at the project level. But if you wish to recreate the full ontology with additional information:
```
from exaatow_onto.py import ExaAToWOnto

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

onto.visualization()
# open the html file with a browser

```


## Ontology Concepts

Key classes include:

    HPCResource → CPU, GPU, RAM, SSD, etc.

    AuthenticationEntity → User, AccessToken, Session

    DieSize, Workload, MemoryCapacity as datatype-linked concepts



