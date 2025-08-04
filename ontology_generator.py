import os
import rdflib
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD, SKOS
from typing import Dict, Optional, Union, List, Any
import json
import networkx as nx
from pyvis.network import Network
from pathlib import Path

class ExaAToWOnto:
    """
    ExaAToW Ontology Management Class
    
    This class provides a structured approach to manage the ExaAToW ontology
    for HPC, digital twin, and energy consumption monitoring applications.
    """
    
    def __init__(self, base_uri: str = "https://raw.githubusercontent.com/cnherrera/Exa-AToW_onto/refs/heads/main/test_ontology_exaatow.ttl#"):
        """
        Initialize the ExaAToW ontology manager
        
        Args:
            base_uri (str): Base URI for the ExaAToW ontology namespace
        """
        self.base_uri = base_uri.rstrip() + ("#" if not base_uri.endswith("#") else "")
        self.EXAATOW = Namespace(self.base_uri)
        self.graph = Graph()

        self.json_file_mapping = {}
        
        # if we aren't running in the `files` directory, add it as a prefix
        if os.path.exists("files"):
            print("Prefixing file load with 'files' directory")
            self.json_dir = "files"
        else:
            self.json_dir = ""
        
        # Bind standard namespaces
        self._bind_namespaces()
        
        # Initialize basic structure
        self._init_basic_structure()
    
    def _bind_namespaces(self):
        """Bind all necessary namespaces to the graph"""
        namespaces = {
            "exa-atow": self.EXAATOW,
            "skos": SKOS,
            "owl": OWL,
            "rdf": RDF,
            "rdfs": RDFS,
            "xsd": XSD,
            "eurio" : Namespace("http://data.europa.eu/s66#"),
            "hpc_onto" : Namespace("https://hpc-fair.github.io/ontology/#")
        }

        for prefix, namespace in namespaces.items():
            self.graph.bind(prefix, namespace)

    def _resolve_uri(self, uri_or_name: Union[URIRef, str], namespace: Optional[Namespace] = None) -> URIRef:
        """
        Resolve a URI or name to a proper URIRef using a global namespace lookup
        
        Args:
            uri_or_name: URI string or local name
            namespace: Namespace to use for local names (defaults to EXAATOW)
            
        Returns:
            URIRef: Resolved URI reference
        """
        if isinstance(uri_or_name, URIRef):
            return uri_or_name
        
        if isinstance(uri_or_name, str):
            # Handle full URIs
            if uri_or_name.startswith('http'):
                return URIRef(uri_or_name)
            
            # Handle prefixed names like "xsd:string", "rdfs:label"
            if ':' in uri_or_name:
                prefix, local = uri_or_name.split(':', 1)
                prefix_lower = prefix.lower()
                
                # Look up namespace globally
                if prefix_lower in self.namespaces:
                    return self.namespaces[prefix_lower][local]
                else:
                    logger.warning(f"Unknown namespace prefix: {prefix}. Using EXAATOW namespace.")
                    return self.EXAATOW[uri_or_name]
            
            # Handle local names - use provided namespace or default to EXAATOW
            ns = namespace or self.EXAATOW
            return ns[uri_or_name]
        
        raise ValueError(f"Cannot resolve URI: {uri_or_name}")


    def add_triple(self, subject: Union[URIRef, str], 
                   predicate: Union[URIRef, str], 
                   obj: Union[URIRef, Literal, str]):
        """
        Add a triple to the ontology graph
        
        Args:
            subject: The subject of the triple
            predicate: The predicate of the triple
            obj: The object of the triple
        """
        # Convert strings to URIRef if needed
        if isinstance(subject, str):
            subject = URIRef(subject) if subject.startswith('http') else self.EXAATOW[subject]
        if isinstance(predicate, str):
            predicate = URIRef(predicate) if predicate.startswith('http') else self.EXAATOW[predicate]
        if isinstance(obj, str) and not obj.startswith('http'):
            obj = self.EXAATOW[obj]
        elif isinstance(obj, str):
            obj = URIRef(obj)
            
        self.graph.add((subject, predicate, obj))
    
    def add_class(self, class_name: str, 
              parent_class: Optional[Union[URIRef, str]] = None,
              pref_label: Optional[Union[str, dict]] = None,
              comment: Optional[Union[str, dict]] = None,
              equivalent=None,
              json_path: Optional[str] = None,
              ):
        """
        Add an OWL class to the ontology
 
        Args:
            class_name: Name of the class
            parent_class: Parent class (for subclass relationships)
            pref_label: Preferred label for the class. Can be a string (default "en") or dict with lang keys.
            comment: Comment describing the class. Can be a string (default "en") or dict with lang keys.
            equivalent: Optional equivalent class
            json_path: Optional path to the JSON file in which this class should be dumped
        """

        if json_path is not None:
            if self.json_dir not in json_path:
                json_path =  os.path.join(self.json_dir, json_path)
            self.json_file_mapping[class_name] = json_path

        class_uri = self._resolve_uri(class_name)
        
        # Add class declaration
        self.add_triple(class_uri, RDF.type, OWL.Class)

        # Add subclass relationship if parent is specified
        if parent_class:
            parent_uri = self._resolve_uri(parent_class)
            self.graph.add((class_uri, RDFS.subClassOf, parent_uri))

        # Add equivalent class
        if equivalent:
            equivalent_uri = self._resolve_uri(equivalent)
            self.graph.add((class_uri, OWL.equivalentClass, equivalent_uri))

        # Add prefLabel(s)
        if pref_label:
            self._add_dict_property(class_uri, SKOS.prefLabel, pref_label)

        # Add comment(s)
        if comment:
            self._add_dict_property(class_uri, RDFS.comment, comment)
                

    def _add_dict_property(self, subject: URIRef, predicate: URIRef, 
                                   value: Union[str, Dict[str, str]], default_lang: str = "en"):
        """
        Add a property that can have multiple language variants
        
        Args:
            subject: Subject URI
            predicate: Predicate URI
            value: String or dictionary of language->value mappings
            default_lang: Default language if value is a string
        """
        if isinstance(value, dict):
            for lang, text in value.items():
                self.graph.add((subject, predicate, Literal(text, lang=lang)))
        else:
            self.graph.add((subject, predicate, Literal(value, lang=default_lang)))
    
    
    def add_property(self, property_name: str, 
                     property_type: str = "ObjectProperty",
                     domain: Optional[Union[URIRef, str, List[Union[URIRef, str]]]] = None,
                     range_: Optional[Union[URIRef, str]] = None,
                     comment: Optional[Union[str,dict]] = None,
                     pref_label: Optional[Union[str,dict]] = None,
                     lang: str = "en"):
        """
        Add an OWL property to the ontology
        
        Args:
            property_name: Name of the property
            property_type: Type of property ("ObjectProperty", "DatatypeProperty", "AnnotationProperty")
            domain: Domain class for the property -> it can be a list or individual
            range_: Range class or datatype for the property
            comment: Comment describing the property
            lang: Language tag for comments


        - **OWL.ObjectProperty** vs **OWL.DatatypeProperty**: whether the property points to another class (object) or to a literal value (data).
        - **OWL.AnnotationProperty**: used only for annotations (metadata).
        - **OWL.inverseOf**: links a property to its inverse (e.g., hasPart inverse of isPartOf).
        - **OWL.FunctionalProperty**: means a subject can have at most one value for this property.
        - **OWL.TransitiveProperty**: if A relates to B and B relates to C, then A relates to C.
        - **OWL.SymmetricProperty**: if A relates to B, then B relates to A.
        - **OWL.AsymmetricProperty**: if A relates to B, B cannot relate to A.
        - **OWL.ReflexiveProperty**: everything is related to itself.
        - **OWL.IrreflexiveProperty**: nothing is related to itself.

        # Define property type and features
           g.add((p, RDF.type, OWL.ObjectProperty))
           g.add((p, RDF.type, OWL.FunctionalProperty))
           g.add((p, RDF.type, OWL.TransitiveProperty))

        """
        property_uri = self._resolve_uri(property_name)
        
        # Add property declaration
        property_types = {
            "ObjectProperty": OWL.ObjectProperty,
            "DatatypeProperty": OWL.DatatypeProperty,
            "AnnotationProperty": OWL.AnnotationProperty
        }
        
        if property_type not in property_types:
            raise ValueError(f"Invalid property type: {property_type}")
            
        self.graph.add((property_uri, RDF.type, property_types[property_type]))
        
        # Add domain(s)
        if domain:
            domains = domain if isinstance(domain, list) else [domain]
            for d in domains:
                d_uri = self._resolve_uri(d)
                self.graph.add((property_uri, RDFS.domain, d_uri))   
        
        # Add range
        if range_:
            if isinstance(range_, str):
                range_ =  self.EXAATOW[range_] if not range_.startswith('http') else URIRef(range_)
            self.graph.add((property_uri, RDFS.range, range_))

            
        # Add prefLabel(s)
        if pref_label:
            self._add_dict_property(property_uri, SKOS.prefLabel, pref_label)

        # Add comment(s)
        if comment:
            self._add_dict_property(property_uri, RDFS.comment, comment)
            
    
    def add_instance(self, instance_name: str, 
                     class_type: Union[URIRef, str],
                     properties: Optional[dict] = None):
        """
        Add an instance (individual) to the ontology
        
        Args:
            instance_name: Name of the instance
            class_type: Class that this instance belongs to
            properties: Dictionary of properties and their values
        """
        instance_uri = self.EXAATOW[instance_name]
        
        # Convert class_type to URIRef if needed
        if isinstance(class_type, str):
            class_type = self.EXAATOW[class_type]
        
        # Add instance declaration
        self.graph.add((instance_uri, RDF.type, class_type))
        
        # Add properties if provided
        if properties:
            for prop, value in properties.items():
                prop_uri = self.EXAATOW[prop] if isinstance(prop, str) else prop
                if isinstance(value, str):
                    value = Literal(value)
                elif isinstance(value, (int, float)):
                    value = Literal(value)
                elif isinstance(value, bool):
                    value = Literal(value)
                self.graph.add((instance_uri, prop_uri, value))

    def load_and_add_classes(self, json_file, default_parent_class):
        """Load classes from JSON file and add them with fallback parent class."""
        
        with open(json_file, "r", encoding="utf-8") as f:
            s_classes = json.load(f)
    
        for s_class in s_classes:
            self.add_class(
                s_class["id"],
                pref_label=s_class["pref_label"],
                parent_class=s_class.get("parent_class", default_parent_class),
                comment=s_class["comment"]
             )
            
            self.json_file_mapping[s_class["id"]] = json_file


    def load_and_add_properties(self, json_file):
        """Load properties from JSON file and add them to the ontology."""
        with open(json_file, "r", encoding="utf-8") as f:
            properties = json.load(f)

        for prop in properties:
                self.add_property(
                    property_name=prop.get("id"),
                    property_type=prop.get("property_type", "ObjectProperty"),
                    domain=prop.get("domain"),
                    range_=prop.get("range"),
                    comment=prop.get("comment"),
                    pref_label=prop.get("pref_label")
#                    inverse_of=prop.get("inverse_of")
                    )


    def _init_basic_structure(self):
        """Initialize the basic structure of the ExaAToW ontology"""

        #--------------
        # Core Classes
        #--------------

        # Read JSON file with main classes
        self.load_and_add_classes(os.path.join(self.json_dir, "main_classes.json"), None)

        #--------------------
        # Adding subclasses
        #--------------------

        # dictionary of subclasses and their default parent class
        subclasses = {
            "sub_HPC_classes.json": "HPCResource",
            "sub_PIE_classes.json": "ProcessorIndicatorEstimator",
            "sub_PhysChar_classes.json": "PhysicalCharacteristic",
            "sub_Job_classes.json": "Job",
            "sub_Workflow_classes.json": "Workflow"
        }
        
        # add all subclasses
        for sub_file, parent in subclasses.items():
            self.load_and_add_classes(os.path.join(self.json_dir, sub_file), parent)

        # Workflow subclasses: Add using add_class
        self.load_and_add_classes("sub_Workflow_classes.json", "Workflow")
        

# Missing: link between subclasses.
# CPU and GPU has specufucations, i.,e. DieSize (property), Workload, 

# Supercomputer has name, etc.


        #Adding properties for Workflow
        self.load_and_add_properties("properties_workflow.json")



        #----------------------------------------
        # Properties definition
        #----------------------------------------

        prop_cpu_gpu = [{"rang": "DieSize", "comm":"CPU, GPU has a die size."}, {}]
        self.add_property("hasDieSize", 
                      property_type="DatatypeProperty",
                     domain=["CPU","GPU"],
                      range_="DieSize",
                      comment="CPU, GPU has a die size.")

        self.add_property("hasValue",
                          property_type="DatatypeProperty",
                          domain="DieSize",
                          range_="XSD:decimal",
                          comment={"en": "Numeric value.","fr": "Valeur numérique."})
        
        self.add_property("hasUnit", property_type="DatatypeProperty", domain="DieSize", range_="XSD:string",
            comment={ "en": "Unit of measurement (e.g., mm²).", "fr": "Unité de mesure (ex. : mm²)."})
        

#Instances:
#ex:cpu1 a ex:CPU ;
#        ex:hasDieSize ex:diesize1 .

#ex:diesize1 a ex:DieSize ;
#        ex:dieSizeValue "42.5"^^xsd:decimal ;
#        ex:unit "mm²" .

#properties:
#CPU hasFeature DieSize
#GPU hasFeature DieSize
#CPU hasFeature Workload
#GPU hasFeature Workload
#XXX hasFeature lifetime
#RAM, SSD, HDD hasFeature MemoryCapacity
        
        # Energy and Digital Twin Classes
        self.add_class("EnergyConsumption", 
                      pref_label="Energy Consumption",
                      comment="Represents a measurement of energy usage.")
        
        self.add_class("DigitalTwin", 
                      pref_label="Digital Twin",
                      comment="Represents a virtual representation of a physical or logical entity.")
        
        self.add_class("SimulationResult",
                      parent_class = "DigitalTwin",
                      pref_label="Simulation Result",
                      comment="Represents the outcome of a simulation performed by a Digital Twin.")
        
        # Object Properties
        self.add_property("authenticates", 
                         property_type="ObjectProperty",
                         domain="User",
                         range_="Authentication",
                         comment="Relates a User to an Authentication event.")

        self.add_property("hasProperty"
                          )


        self.add_property("hasFlowType", 
                         property_type="ObjectProperty",
                         domain="Workflow",
                         range_="FlowType",
                         comment="Specifies the flow type of the workflow (task-based, iterative, or data-driven).")
    
    def serialize(self, format: str = "turtle", destination: Optional[str] = None):
        """
        Serialize the ontology to a file or return as string
        
        Args:
            format: Serialization format (turtle, xml, n3, json-ld, etc.)
            destination: File path to save the ontology (optional)
        
        Returns:
            str: Serialized ontology if no destination is provided
        """
        if destination:
            self.graph.serialize(destination=destination, format=format)
            return f"Ontology saved to {destination}"
        else:
            return self.graph.serialize(format=format)
    

    def visualize_graph(self, output_file="ontology_graph.html", height="800px", physics=True):
        """
        Create an enhanced interactive visualization of the ontology

        Args:
            output_file (str, optional): Filename for the output HTML file. Defaults to "ontology_graph.html".
            height (str, optional): Height of the visualization. Defaults to "800px".
            physics (bool, optional): Whether to enable physics simulation. Defaults to True.

        Returns:
            Network: PyVis Network object containing the visualization

        Example:
            # Create a visualization with default settings
            net = onto.visualize_graph()

            # Create a visualization with custom settings
            net = onto.visualize_graph(
                output_file="project_network.html",
                height="1000px",
                physics=False
            )
        """

        G = nx.DiGraph()

        # Store class types
        class_types = {}
        for s, p, o in self.graph.triples((None, RDF.type, None)):
            if o != RDFS.Class and isinstance(s, URIRef):
                class_types[str(s)] = str(o).split('#')[-1]

        # Add class nodes with labels
        for entity, entity_type in class_types.items():
            labels = list(self.graph.objects(URIRef(entity), RDFS.label))
            label = str(labels[0]) if labels else entity.split('#')[-1]
            descriptions = list(self.graph.objects(URIRef(entity), RDFS.comment))
            title = str(descriptions[0]) if descriptions else label
            G.add_node(entity, label=label, title=title, group=entity_type)

        # Add edges for subclass relationships (blue)
        for s, p, o in self.graph.triples((None, RDFS.subClassOf, None)):
            if str(s) in class_types and str(o) in class_types:
                G.add_edge(str(s), str(o), label="subClassOf", title="subClassOf", color='blue')

        # Add edges for object properties (red)
        for s, p, o in self.graph.triples((None, None, None)):
            if isinstance(s, URIRef) and isinstance(o, URIRef) and str(s) in class_types and str(o) in class_types:
                pred_labels = list(self.graph.objects(p, RDFS.label))
                pred_label = str(pred_labels[0]) if pred_labels else str(p).split('#')[-1]
                G.add_edge(str(s), str(o), label=pred_label, title=pred_label, color='red')

        # Create pyvis network
        net = Network(height=height, width="100%", directed=True, notebook=False)

        # Configure physics
        if physics:
            net.barnes_hut(spring_length=200, spring_strength=0.05, damping=0.09, gravity=-80)
        else:
            net.toggle_physics(False)

        # Add nodes and edges from NetworkX
        net.from_nx(G)

        # Customize visualization
        net.set_options("""
        var options = {
          "nodes": {
            "font": { "size": 14, "face": "Arial" },
            "borderWidth": 2,
            "shadow": true
          },
          "edges": {
            "smooth": { "enabled": true, "type": "dynamic" },
            "arrows": { "to": { "enabled": true, "scaleFactor": 0.5 } },
            "font": { "size": 12, "align": "middle" },
            "shadow": true
          },
          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true
          }
        }
        """)

        # Save visualization
        net.save_graph(output_file)
        print(f"Graph visualization saved to {output_file}")

        return net

    def get_graph(self):
        """Return the RDF graph"""
        return self.graph
    
    def get_namespace(self):
        """Return the ExaAToW namespace"""
        return self.EXAATOW
    
    def create_json_mapping(self) -> Dict[str, Dict[str, Union[str, Dict[str, str]]]]:
        """Create a dictionary mapping JSON files to their corresponding entries"""
        translate = {
            "prefLabel": "pref_label",
            "subClassOf": "parent_class",
            "type": None,
        }

        data = {}
        for item in self.graph:
            # Each node on the rdf graph consists of 3 values
            # (id, key, value)
            # Where id is the JSON representation
            # We must collect these key: val pairs onto their respective
            # JSON identifier before dumping

            # Group by id
            id = str(item[0]).split("#")[-1]

            # get the key of the key: val pair   
            key = str(item[1]).split("#")[-1]
            # translate from rdf term to json term
            # we default to the key itself, in case there are no translations available
            key = translate.get(key, key)
            # set translation to None to avoid dumping this key
            if key is None:
                continue
            # We need to select between a simple key: val and the language subtree
            if isinstance(item[2], URIRef):
                val = str(item[2]).split("#")[-1]
            # Literal is used for comments and labels, collect them into a properly nested dict
            elif isinstance(item[2], Literal):
                val = {item[2].language: item[2].value}            
            else:
                continue

            # Create this entry if it does not exist
            if id not in data:
                data[id] = {}

            if key in data[id] and isinstance(data[id][key], dict):
                # If the dictionary already exists, we need to ensure that the keys
                # are sorted to prevent the json files randomising the order every time
                tmp = data[id][key]
                tmp.update(val)
                val = dict(sorted(tmp.items()))

            data[id][key] = val

        return data

    def dump_to_json(self) -> None:
        print("Dumping ontology to json")

        # collect the data
        # This is a dict of {id: {data}}
        mapping = self.create_json_mapping()
        print(f"  We have {len(mapping)} entries in the graph derived mapping.\n")

        # for efficient file writing, we should group by file
        # entries without a file go in None
        # the end result of this should be a dict in the form:
        # {path: {id: {data}}}

        # key ordering for json output
        # id is always first, so not needed here
        key_order = ["parent_class", "pref_label", "comment"]
        file_grouping = {}
        for id, data in mapping.items():

            file = self.json_file_mapping.get(id, None)

            if file not in file_grouping:
                file_grouping[file] = {}

            # we need to ensure a common ordering of the keys
            # easiest to add the id into the data here
            tmp = {"id": id}

            for item in key_order:
                val = data.pop(item, None)

                if val is None:
                    continue

                tmp[item] = val  # type: ignore

            tmp.update(data)  # type: ignore

            file_grouping[file][id] = tmp

        # Now write the JSON
        for file, entries in file_grouping.items():
            if file is None:
                continue
            print(f"Treating file: {file}")
            print("  Loading existing ids", end="... ")
            try:
                if not os.path.exists(file):
                    existing_id_ordering = []
                    print("File not found, will be created.")
                else:
                    with open(file, "r") as o:
                        existing_id_ordering = [item["id"] for item in json.load(o)]
                    print(f"Done ({len(existing_id_ordering)})")
            except:
                print("Error")
                raise

            output = []
            for id in existing_id_ordering:
                data = entries.pop(id)
                output.append(data)

            for id, data in entries.items():
                output.append(data)

            with open(file, "w+") as o:
                json.dump(output, o, indent=2, ensure_ascii=False)
                o.write("\n")

        if len(file_grouping[None]) > 0:
            print(f"\nWarning: {len(file_grouping[None])} entries were not written (Do they have an assigned JSON file?)")
        
            for id in file_grouping[None]:
                print(f"  {id}")


# Example usage
if __name__ == "__main__":
    # Create an instance of the ontology
    onto = ExaAToWOnto()
    
    # Add a custom class
#    onto.add_class("CustomResource", 
#                   parent_class="HPCResource",
#                   pref_label="Custom Resource",
#                   comment="A custom HPC resource type.")
    
    # Add a custom property
#    onto.add_property("hasCustomProperty", 
#                      property_type="DatatypeProperty",
#                      domain="CustomResource",
#                      range_="http://www.w3.org/2001/XMLSchema#string",
#                      comment="A custom property for custom resources.")
    
    # Add an instance
#    onto.add_instance("myCustomResource", 
#                      "CustomResource",
#                      properties={"hasCustomProperty": "example_value"})
    
    # Print the ontology in Turtle format
    print(onto.serialize(destination="exaatow_ontology.ttl",format="turtle"))
