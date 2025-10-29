"""
ExaAToW Ontology Management System

This module provides a structured approach to manage the ExaAToW ontology
for HPC, workflows and energy consumption monitoring applications.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Optional, Union, List, Any

import rdflib
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD, SKOS

import networkx as nx
from pyvis.network import Network

# ==============================
# GLOBAL CONFIG LOADING
# ==============================

def _check_attribute_yaml(value, default):
        """Return value if it exists and not None, otherwise return default."""
        return value if value is not None else default
    
file_config = "ontology_config.yaml"
if os.path.exists(file_config):
    with open(file_config, "r") as file:
        config = yaml.safe_load(file)
else:
    config={}

LANG = _check_attribute_yaml(config.get("default_lang"),"en")
FILES_DIR = _check_attribute_yaml(config.get("files_dir"),"files")
DEFAULT_BASE_URI = _check_attribute_yaml(config.get("base_uri"),"https://localhost/myontology#")

   
class CreateOnto:
    """
    Ontology Management Class
    
    This class provides a structured approach to manage the ontology.
    """
    
    def __init__(self, base_uri: str = DEFAULT_BASE_URI):
        """
        Initialize the ExaAToW ontology manager
        
        Args:
            base_uri (str): Base URI for the ExaAToW ontology namespace
        """
        self.base_uri = base_uri.rstrip() + ("#" if not base_uri.endswith("#") else "")
        self.ONTO = Namespace(self.base_uri)
        self.graph = Graph()
        self.json_file_mapping = {}
        self.FILES_DIR = FILES_DIR
        self.DEFAULT_LANG = LANG

        # Determine JSON directory
        self.json_dir = self.FILES_DIR if os.path.exists(self.FILES_DIR) else ""
        if self.json_dir:
            print(f"Using '{self.json_dir}' directory for JSON files")
        
        # Initialize ontology structure
        self._bind_namespaces()
        self._init_basic_structure()

    def _bind_namespaces(self):
        """Bind all necessary namespaces to the graph"""
        namespaces = {
            "exa-atow": self.ONTO,
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

    @property
    def namespaces(self) -> Dict[str, Namespace]:
        """Get all bound namespaces as a dictionary"""
        return {prefix: ns for prefix, ns in self.graph.namespaces()}

    def _resolve_uri(self, uri_or_name: Union[URIRef, str], namespace: Optional[Namespace] = None) -> URIRef:
        """
        Resolve a URI or name to a proper URIRef using a global namespace lookup
        
        Args:
            uri_or_name: URI string or local name
            namespace: Namespace to use for local names (defaults to ONTO)
            
        Returns:
            URIRef: Resolved URI reference
        """
        if isinstance(uri_or_name, URIRef):
            return uri_or_name

        if not isinstance(uri_or_name, str):
            raise ValueError(f"Cannot resolve URI: {uri_or_name}")
            
        # Handle full URIs
        if uri_or_name.startswith(('http://', 'https://')):
            return URIRef(uri_or_name)

        #Handle prefixed names like "xsd:string", "rdfs:label"
        if ':' in uri_or_name:
            prefix, local = uri_or_name.split(':', 1)
            prefix_lower = prefix.lower()##

            # Get the namespace URI for this prefix
            for ns_prefix, ns_uri in self.graph.namespaces():
                if ns_prefix == prefix_lower:
                    # Create a Namespace object and use it to append the local part
                    return Namespace(ns_uri)[local]
                
            # If prefix not found, warn and use ONTO
            print(f"Warning: Unknown namespace prefix '{prefix}'. Using ONTO namespace.")
            return self.ONTO[uri_or_name]

        # Handle local names
        ns = namespace or self.ONTO
        return ns[uri_or_name]

    
    # ==========================================
    # File I/O Utilities
    # ==========================================

    def _load_json(self, filename: str) -> Any:
        """
        Load JSON file from the configured directory
        
        Args:
            filename: Name of the JSON file
            
        Returns:
            Parsed JSON data
        """
        filepath = os.path.join(self.json_dir, filename) if self.json_dir else filename
        print(filepath)
        
        with open(filepath, "r", encoding="utf-8") as f:
            f_json = json.load(f)
            return f_json

        
    def _handle_json_path(self, identifier: str, json_path: Optional[str]) -> None:
        """
        Register JSON file mapping for an identifier
        
        Args:
            identifier: Class or instance identifier
            json_path: Path to JSON file
        """
        if json_path:
            if self.json_dir and self.json_dir not in json_path:
                json_path = os.path.join(self.json_dir, json_path)
            self.json_file_mapping[identifier] = json_path
            

    # ==========================================
    # Triple
    # ==========================================
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
            subject = self._resolve_uri(subject) 
            
        if isinstance(predicate, str):
            predicate = self._resolve_uri(predicate)
            
        if isinstance(obj, str):
            obj = self._resolve_uri(obj)
            
        self.graph.add((subject, predicate, obj))

        
    # ==========================================
    # Class Management
    # ==========================================
        
    def add_class(self, class_name: str, 
              parent_class: Optional[Union[URIRef, str]] = None,
              pref_label: Optional[Union[str, dict]] = None,
              comment: Optional[Union[str, dict]] = None,
              equivalent: Optional[Union[URIRef, str]]=None,
              link_html: Optional[str] = None,
              one_of : Optional[str] = None,
              cardinality: Optional[dict]=None,
              restrictions: Optional[List[dict]]=None,    
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
            link_html: Optional external link
            one_of: Optional list of individuals that constitute the enumerated class
            restrictions: Optional[List[dict]] = None,
            cardinality: Optional[dict] = None,
            json_path: Optional path to JSON file in which this class should be dumped
        """

        self._handle_json_path(class_name, json_path)
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

        # Add OneOf enumeration
        if one_of:
            # Convert all items to URIRefs
            individual_uris = [self._resolve_uri(item) for item in one_of]
        
            # Create the RDF Collection (list) for OneOf
            collection = BNode()
            self.graph.add((class_uri, OWL.equivalentClass, collection))
        
            # Add the restriction that says this class is exactly these individuals
            restriction = BNode()
            self.graph.add((collection, RDF.type, OWL.Class))
            self.graph.add((collection, OWL.oneOf, restriction))
        
            # Add the individuals to the collection
            from rdflib.collection import Collection
            Collection(self.graph, restriction, individual_uris)

        # Property restrictions
        if restrictions:
            for restriction in restrictions:
                self._add_restriction(class_uri, restriction)

        # Cardinality restrictions
        if cardinality:
            self._add_cardinality(class_uri, cardinality)

        # Add external link
        if link_html:
            self.graph.add((class_uri, RDFS.seeAlso, URIRef(link_html)))
    
        # Add labels and comments
        if pref_label:
            self._add_multilingual_property(class_uri, SKOS.prefLabel, pref_label)

        if comment:
            self._add_multilingual_property(class_uri, RDFS.comment, comment)


    def _add_restriction(self, class_uri, restriction_config):
        """Add property restrictions to a class"""
        restriction = BNode()
        self.graph.add((class_uri, RDFS.subClassOf, restriction))
        self.graph.add((restriction, RDF.type, OWL.Restriction))
    
        prop_uri = self._resolve_uri(restriction_config["property"])
        self.graph.add((restriction, OWL.onProperty, prop_uri))
    
        if "some_values_from" in restriction_config:
            value_class = self._resolve_uri(restriction_config["some_values_from"])
            self.graph.add((restriction, OWL.someValuesFrom, value_class))
    
        elif "all_values_from" in restriction_config:
            value_class = self._resolve_uri(restriction_config["all_values_from"])
            self.graph.add((restriction, OWL.allValuesFrom, value_class))
    
        elif "has_value" in restriction_config:
            value = self._resolve_uri(restriction_config["has_value"])
            self.graph.add((restriction, OWL.hasValue, value))

            
    def _add_cardinality(self, class_uri, cardinality_config):
        """
        Add cardinality restrictions to a class using equivalentClass with intersection
    
        Args:
            cardinality_config: Dictionary with keys:
                - property: The property to restrict (required)
                - on_class: Target class for qualified cardinality (optional)
                - exactly: Exact cardinality (mutually exclusive with min/max)
                - min: Minimum cardinality
                - max: Maximum cardinality
        """
        # Create blank nodes for the intersection structure
        equiv_class = BNode()
        restriction = BNode()
    
        # The class is equivalent to an intersection
        self.graph.add((class_uri, OWL.equivalentClass, equiv_class))
        self.graph.add((equiv_class, RDF.type, OWL.Class))
    
        # Create the intersection list: (OriginalClass AND Restriction)
        intersection_node = BNode()
        self.graph.add((equiv_class, OWL.intersectionOf, intersection_node))
    
        # Build the list: [class_uri, restriction]
        from rdflib.collection import Collection
        Collection(self.graph, intersection_node, [class_uri, restriction])
    
        # Define the restriction
        self.graph.add((restriction, RDF.type, OWL.Restriction))
    
        prop_uri = self._resolve_uri(cardinality_config["property"])
        self.graph.add((restriction, OWL.onProperty, prop_uri))
    
        # Check if it's a qualified cardinality (with on_class)
        on_class = cardinality_config.get("on_class")
    
        if "exactly" in cardinality_config:
            cardinality_value = Literal(cardinality_config["exactly"], 
                                   datatype=XSD.nonNegativeInteger)
            if on_class:
                self.graph.add((restriction, OWL.qualifiedCardinality, cardinality_value))
                self.graph.add((restriction, OWL.onClass, self._resolve_uri(on_class)))
            else:
                self.graph.add((restriction, OWL.cardinality, cardinality_value))
        else:
            if "min" in cardinality_config:
                min_value = Literal(cardinality_config["min"], 
                               datatype=XSD.nonNegativeInteger)
                if on_class:
                    self.graph.add((restriction, OWL.minQualifiedCardinality, min_value))
                    self.graph.add((restriction, OWL.onClass, self._resolve_uri(on_class)))
                else:
                    self.graph.add((restriction, OWL.minCardinality, min_value))
        
            if "max" in cardinality_config:
                max_value = Literal(cardinality_config["max"], 
                               datatype=XSD.nonNegativeInteger)
                if on_class:
                    self.graph.add((restriction, OWL.maxQualifiedCardinality, max_value))
                    # Only add onClass if not already added by min
                    if "min" not in cardinality_config:
                        self.graph.add((restriction, OWL.onClass, self._resolve_uri(on_class)))
                else:
                    self.graph.add((restriction, OWL.maxCardinality, max_value))
                
               
    def load_and_add_classes(self, json_file: str, default_parent_class: Optional[str] = None) -> None:
        """
        Load classes from JSON file and add them with fallback parent class.

        Args:
            json_file: Path to JSON file containing class definitions
            default_parent_class: Fallback parent class if not specified in JSON
        """
        print(json_file)
        with open(json_file, "r", encoding="utf-8") as f:
            classes_data = json.load(f)
    
        for class_info in classes_data:
            self.add_class(
                class_name = class_info["id"],
                pref_label = class_info["pref_label"],
                parent_class = class_info.get("parent_class", default_parent_class),
                equivalent = class_info.get("equivalent"),
                link_html = class_info.get("link_html"),
                json_path = class_info.get("json_path"),
                restrictions = class_info.get("restrictions"),
                cardinality = class_info.get("cardinality"),
                one_of = class_info.get("one_of"),    
                comment = class_info["comment"]
             )            
            self.json_file_mapping[class_info["id"]] = json_file

            
    # ==========================================
    # Property Management
    # ==========================================
    
    def _add_multilingual_property(self, subject: URIRef, predicate: URIRef, 
                           value: Union[str, Dict[str, str]],
                           default_lang: str = None)-> None:
        """
        Add a property that can have multiple language variants
        
        Args:
            subject: Subject URI
            predicate: Predicate URI
            value: String or dictionary of language->value mappings
            default_lang: Default language if value is a string
        """
        if default_lang is None:
            default_lang = self.DEFAULT_LANG
        
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
                     json_path: Optional[str] = None,
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

        """

        self._handle_json_path(property_name, json_path)
        
        property_uri = self._resolve_uri(property_name)
        
        # Add property declaration
        property_types = {
            "ObjectProperty": OWL.ObjectProperty,
            "DatatypeProperty": OWL.DatatypeProperty,
            "AnnotationProperty": OWL.AnnotationProperty
        }
        
        if property_type not in property_types:
            raise ValueError(f"Invalid property type: {property_type}. "
                           f"Must be one of {list(property_types.keys())}")

        # Add property declaration
        self.graph.add((property_uri, RDF.type, property_types[property_type]))
        
        # Add domain(s)
        if domain:
            domains = domain if isinstance(domain, list) else [domain]
            for d in domains:
                d_uri = self._resolve_uri(d)
                self.graph.add((property_uri, RDFS.domain, d_uri))   
        
        # Add range
        if range_:
            range_uri = self._resolve_uri(range_) if isinstance(range_, str) else range_
            self.graph.add((property_uri, RDFS.range, range_uri))
            
        # Add prefLabel(s)
        if pref_label:
            self._add_multilingual_property(property_uri, SKOS.prefLabel, pref_label)

        # Add comment(s)
        if comment:
            self._add_multilingual_property(property_uri, RDFS.comment, comment)


    def load_and_add_properties(self, json_file: str) -> None:
        """
        Load properties from JSON file and add them to the ontology
        
        Args:
            json_file: Path to JSON file containing property definitions
        """
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


    # ==========================================
    # Restriction Management
    # ==========================================

    def add_restriction_to_class(self,
                                 class_name: str,
                                 property_name: str,
                                 all_values_from: Optional[Union[URIRef, str]] = None,
                                 enumeration: Optional[list] = None,
                                 comment: Optional[Union[str, dict]] = None):
        """
        Add an OWL Restriction to an existing class without redefining it.

        Args:
            class_name: Name of the existing class
            property_name: Property to restrict
            all_values_from: Datatype or class for allValuesFrom
            enumeration: List of values for owl:oneOf (only used if provided)
            comment: Comment describing this restriction
        """

        class_uri = self._resolve_uri(class_name)
        restriction_bnode = BNode()

        # Create restriction
        self.graph.add((restriction_bnode, RDF.type, OWL.Restriction))

        # Specify the property being restricted
        property_uri = self._resolve_uri(property_name)
        self.graph.add((restriction_bnode, OWL.onProperty, property_uri))

        # Add enumeration constraint(e.g., GB, TB, ...)
        if enumeration:
            datatype_bnode = BNode()
            enum_list = self._create_list(enumeration, datatype=True)
            self.graph.add((datatype_bnode, RDF.type, RDFS.Datatype))
            self.graph.add((datatype_bnode, OWL.oneOf, enum_list))
            self.graph.add((restriction_bnode, OWL.allValuesFrom, datatype_bnode))

        # Add allValuesFrom constraint
        elif all_values_from:
            range_uri = self._resolve_uri(all_values_from) if isinstance(all_values_from, str) else all_values_from
            self.graph.add((restriction_bnode, OWL.allValuesFrom, range_uri))

        # Add comment specific to restriction
        if comment:
            self._add_multilingual_property(restriction_bnode, RDFS.comment, comment)

        # Link restriction to class
        self.graph.add((class_uri, RDFS.subClassOf, restriction_bnode))


    def _create_list(self, values, datatype=False) -> BNode:
        """
        Helper to create RDF collections (rdf:List) for enumerations.
        """
        first_node = BNode()
        current_node = first_node
        
        for i, val in enumerate(values):
            lit = Literal(val) if not datatype else Literal(val, datatype=XSD.string)
            self.graph.add((current_node, RDF.first, lit))
            
            if i == len(values) - 1:
                self.graph.add((current_node, RDF.rest, RDF.nil))
            else:
                next_node = BNode()
                self.graph.add((current_node, RDF.rest, next_node))
                current_node = next_node
                
        return first_node

    def load_restrictions(self, json_file: str) -> None:
        """
        Load restrictions from JSON file and apply them
        
        Args:
            json_file: Path to JSON file containing restriction definitions
        """
        try:
            restrictions_data = self._load_json(json_file)
        except FileNotFoundError:
            print(f"Warning: Restrictions file '{json_file}' not found. Skipping.")
            return
        
        for entry in restrictions_data:
            class_name = entry["class_name"]
            
            for restriction in entry["restrictions"]:
                kwargs = {
                    "class_name": class_name,
                    "property_name": restriction["property_name"],
                    "comment": restriction.get("comment")
                }
                
                if "enumeration" in restriction:
                    kwargs["enumeration"] = restriction["enumeration"]
                
                if "all_values_from" in restriction:
                    xsd_type = restriction["all_values_from"].split(":")[-1]
                    kwargs["all_values_from"] = getattr(XSD, xsd_type)
                
                self.add_restriction_to_class(**kwargs)


    # ==========================================
    # Instance Management
    # ==========================================
    def add_instance(self, instance_name: str, 
                     class_type: Union[URIRef, str, List[Union[URIRef, str]]],
                     properties: Optional[dict] = None,
                     pref_label: Optional[Union[str, dict]] = None,
                     comment: Optional[Union[str, dict]] = None,
                     json_path: Optional[str] = None):
        """
        Add an instance (individual) to the ontology

        Args:
            instance_name: Name of the instance
            class_type: Class(es) that this instance belongs to - can be single class or list
            properties: Dictionary of properties and their values
            pref_label: Preferred label (string - default "en"- or dict with lang keys).
            comment: Comment describing the instance (string - default "en"-  or dict with lang keys.
            json_path: Optional path to  JSON file for export
        """
        # Handle JSON file mapping (consistent with add_class)
        self._handle_json_path(instance_name, json_path)

        # Use _resolve_uri for consistency
        instance_uri = self._resolve_uri(instance_name)

        # Handle multiple class types
        class_types = class_type if isinstance(class_type, list) else [class_type]
        for cls in class_types:
            cls_uri = self._resolve_uri(cls)
            # Use add_triple method for consistency (if available), otherwise use graph.add
            self.add_triple(instance_uri, RDF.type, cls_uri)

        # Add prefLabel(s)
        if pref_label:
            self._add_multilingual_property(instance_uri, SKOS.prefLabel, pref_label)

        # Add comment(s)
        if comment:
            self._add_multilingual_property(instance_uri, RDFS.comment, comment)

        # Add properties if provided
        if properties:
            for prop_name, values in properties.items():
                prop_uri = self._resolve_uri(prop_name)

                # Handle multiple values for a property
                value_list = values if isinstance(values, list) else [values]

                for value in value_list:
                    # Convert value to appropriate RDF term inline
                    if isinstance(value, (URIRef, Literal, BNode)):
                        # Already an RDF term
                        rdf_value = value
                    elif isinstance(value, str):
                        # Check if it's a URI or should be resolved as one
                        if value.startswith(('http://', 'https://')):
                            rdf_value = URIRef(value)
                        elif ':' in value and not value.startswith('_:'):
                            # Try to resolve as URI, fallback to literal
                            try:
                                rdf_value = self._resolve_uri(value)
                            except:
                                rdf_value = Literal(value)
                        elif value.startswith('_:'):
                            # Blank node
                            rdf_value = BNode(value[2:])
                        else:
                            # Regular string literal
                            rdf_value = Literal(value)
                    elif isinstance(value, bool):
                        rdf_value = Literal(value)
                    elif isinstance(value, (int, float)):
                        rdf_value = Literal(value)
                    else:
                        # Default to string literal
                        rdf_value = Literal(str(value))

                    self.add_triple(instance_uri, prop_uri, rdf_value)

    def load_instances(self, json_file: str) -> None:
        """
        Load instances from JSON file and add them
        
        Args:
            json_file: Path to JSON file containing instance definitions
        """
        try:
            instances_data = self._load_json(json_file)
        except FileNotFoundError:
            print(f"Warning: Instances file '{json_file}' not found. Skipping.")
            return
        
        for inst in instances_data:
            self.add_instance(
                instance_name = inst["id"],
                class_type = inst["class_type"],
                pref_label = inst.get("pref_label"),
                comment = inst.get("comment"),
                properties = inst.get("properties"),
                json_path = inst.get("json_path")
            )


    # ==========================================
    # Ontology Initialization
    # ==========================================

    def _init_basic_structure(self):
        """Initialize the basic structure of the ontology"""

        # Load main classes
#        self.load_and_add_classes(
#            os.path.join(self.json_dir, "main_classes.json"),
#            None
#        )

        # #############################################    
        # Global statement of "hasUnit" and "hasValue"
        # #############################################
        self.add_property(
                    property_name="hasValue",
                    property_type="DatatypeProperty",
                    range_="XSD:decimal",
                    comment={"en": "Numeric value.","fr": "Valeur numérique"},
                    pref_label={"en": "has numeric value","fr": "a valeur numérique"})
        
        self.add_property(
                    property_name="hasUnit",
                    property_type="DatatypeProperty",
                    range_="XSD:string",
                    comment={"en": "Unit of measurement.","fr": "Unité de mesure"},
                    pref_label={"en": "has unit","fr": "a unité"})#
        ################################################
        

            
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
        """Return the ONTO namespace"""
        return self.ONTO
    
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

#_______________________________________________________________________________
# Exa-AToW use case

if __name__ == "__main__":
    # Create an instance of the ontology
    onto_exaatow = CreateOnto("https://raw.githubusercontent.com/cnherrera/Exa-AToW_onto/refs/heads/main/test_ontology_exaatow.ttl#")

    # Load subclasses
    # dictionary of subclasses and their default parent class#
#    subclasses = {
#            "sub_HPC_classes.json": "HPCResource",
#            "sub_PIE_classes.json": "ProcessorIndicatorEstimator",
#            "sub_PhysChar_classes.json": "PhysicalCharacteristic",
#            "sub_Job_classes.json": "Job",
#            "sub_Workflow_classes.json": "Workflow"
#    }
#        
#    for sub_file, parent in subclasses.items():
#        onto_exaatow.load_and_add_classes(os.path.join(onto_exaatow.json_dir, sub_file), parent)
    onto_exaatow.load_and_add_classes(os.path.join(onto_exaatow.json_dir, "sub_Workflow_classes_new.json"))

    # Load properties
    list_properties=[
            "properties_workflow.json"#,
#            "properties_HPC.json"
    ]
        
    for props in list_properties:
        onto_exaatow.load_and_add_properties(os.path.join(onto_exaatow.json_dir, props))

    # Load and add restrictions
#    onto_exaatow.load_restrictions("add_restrictions_hasValue_hasUnit.json")

    # Load and add instances
    list_instances=[
            "instances_workflow.json"
            ]
    for instances in list_instances:
        onto_exaatow.load_instances(instances)

    # Print the ontology in Turtle format
    onto_exaatow.serialize(destination="exaatow_workflow_ontology.ttl",format="turtle")


    
#################################################################################################    
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
    

        #=+++++++++++++++++++++++++++++++++++++++++++++++++++

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

        # Energy and Digital Twin Classes#
#        self.add_class("EnergyConsumption", 
#                      pref_label="Energy Consumption",
#                      comment="Represents a measurement of energy usage.")
        
#        self.add_class("SimulationResult",
#                      parent_class = "DigitalTwin",
#                      pref_label="Simulation Result",
#                      comment="Represents the outcome of a simulation performed by a Digital Twin.")
        
        # Object Properties
#        self.add_property("authenticates", 
#                         property_type="ObjectProperty",
#                         domain="User",
#                         range_="Authentication",
#                         comment="Relates a User to an Authentication event.")

    
