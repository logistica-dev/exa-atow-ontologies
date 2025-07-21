import rdflib
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD, SKOS
from typing import Optional, Union, List
import json

class ExaAToWOnto:
    """
    ExaAToW Ontology Management Class
    
    This class provides a structured approach to manage the ExaAToW ontology
    for HPC, digital twin, and energy consumption monitoring applications.
    """
    
    def __init__(self, base_uri: str = "https://github.com/cnherrera/Exa-AToW_onto/blob/main/test_ontology_exaatow.ttl#"):
        """
        Initialize the ExaAToW ontology manager
        
        Args:
            base_uri (str): Base URI for the ExaAToW ontology namespace
        """
        self.base_uri = base_uri
        self.EXAATOW = Namespace(base_uri)
        self.graph = Graph()
        
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
        }

        for prefix, namespace in namespaces.items():
            self.graph.bind(prefix, namespace)

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
              equivalent=None):
        """
        Add an OWL class to the ontology
 
        Args:
            class_name: Name of the class
            parent_class: Parent class (for subclass relationships)
            pref_label: Preferred label for the class. Can be a string (default "en") or dict with lang keys.
            comment: Comment describing the class. Can be a string (default "en") or dict with lang keys.
            equivalent: Optional equivalent class
        """
        class_uri = self.EXAATOW[class_name]

        # Add class declaration
        self.graph.add((class_uri, RDF.type, OWL.Class))

        # Add subclass relationship if parent is specified
        if parent_class:
            parent_uri = self.EXAATOW[parent_class] if isinstance(parent_class, str) else parent_class
            self.graph.add((class_uri, RDFS.subClassOf, parent_uri))

        # Add equivalent class
        if equivalent:
            self.graph.add((class_uri, OWL.equivalentClass, equivalent))

        # Add prefLabel(s)
        if pref_label:
            if isinstance(pref_label, dict):
                for lang, label in pref_label.items():
                    self.graph.add((class_uri, SKOS.prefLabel, Literal(label, lang=lang)))
            else:
                self.graph.add((class_uri, SKOS.prefLabel, Literal(pref_label, lang="en")))

        # Add comment(s)
        if comment:
            if isinstance(comment, dict):
                for lang, com in comment.items():
                    self.graph.add((class_uri, RDFS.comment, Literal(com, lang=lang)))
            else:
                self.graph.add((class_uri, RDFS.comment, Literal(comment, lang="en")))

#            def add_class(self, class_name: str, 
#                  parent_class: Optional[Union[URIRef, str]] = None,
#                  pref_label: Optional[str] = None,
#                  comment: Optional[str] = None,
#                  lang: str = "en",
#                  equivalent = None):
        """
        Add an OWL class to the ontology
        
        Args:
            class_name: Name of the class
            parent_class: Parent class (for subclass relationships)
            pref_label: Preferred label for the class
            comment: Comment describing the class
            lang: Language tag for labels and comments
        """
#        class_uri = self.EXAATOW[class_name]
#        
#        # Add class declaration
#        self.graph.add((class_uri, RDF.type, OWL.Class))
#        
#        # Add subclass relationship if parent is specified
#        if parent_class:
#            parent_uri = self.EXAATOW[parent_class] if isinstance(parent_class, str) else parent_class
#            self.graph.add((class_uri, RDFS.subClassOf, parent_uri))
#            
#        #Add equivalent classes    
#        if equivalent:
#            self.graph.add(class_uri, OWL.equivalentClass, equivalent)
#        
#        # Add preferred label
#        if pref_label:
#            self.graph.add((class_uri, SKOS.prefLabel, Literal(pref_label, lang=lang)))
#        
#        # Add comment
#        if comment:
#            self.graph.add((class_uri, RDFS.comment, Literal(comment, lang=lang)))
    
    def add_property(self, property_name: str, 
                     property_type: str = "ObjectProperty",
                     domain: Optional[Union[URIRef, str, List[Union[URIRef, str]]]] = None,
                     range_: Optional[Union[URIRef, str]] = None,
                     comment: Optional[str] = None,
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
        property_uri = self.EXAATOW[property_name]
        
        # Add property declaration
        if property_type == "ObjectProperty":
            self.graph.add((property_uri, RDF.type, OWL.ObjectProperty))
        elif property_type == "DatatypeProperty":
            self.graph.add((property_uri, RDF.type, OWL.DatatypeProperty))
        elif property_type == "AnnotationProperty":
            self.graph.add((property_uri, RDF.type, OWL.AnnotationProperty))
        
        # Add domain(s)
        if domain:
            domains = domain if isinstance(domain, list) else [domain]
            for d in domains:
                d_uri = self.EXAATOW[d] if isinstance(d, str) else d
                self.graph.add((property_uri, RDFS.domain, d_uri))

#        if domain:
#            print(domain)
#            if isinstance(domain, list):
#                for d_domain in domain:
#                    print(d_domain)
#                    if isinstance(d_domain, str):
#                        d_domain = self.EXAATOW[d_domain]
#                        print(d_domain)
#                    self.graph.add((property_uri, RDFS.domain, d_domain))
#            if isinstance(domain, str):
#                print(domain)
#                domain = self.EXAATOW[domain]
#                self.graph.add((property_uri, RDFS.domain, domain))
#            if isinstance(domain, URIRef):
#                print(domain)
#                self.graph.add((property_uri, RDFS.domain, domain)
                    
        
        # Add range
        if range_:
            if isinstance(range_, str):
                range_ = self.EXAATOW[range_] if not range_.startswith('http') else URIRef(range_)
            self.graph.add((property_uri, RDFS.range, range_))
        
        # Add comment
        if comment:
            self.graph.add((property_uri, RDFS.comment, Literal(comment, lang=lang)))
    
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
            print(s_class)
            self.add_class(
                s_class["id"],
                pref_label=s_class["pref_label"],
                parent_class=s_class.get("parent_class", default_parent_class),
                comment=s_class["comment"]
             )
            
    
    def _init_basic_structure(self):
        """Initialize the basic structure of the ExaAToW ontology"""

        #--------------
        # Core Classes
        #--------------
        # Read JSON file with classes
        with open("main_classes.json", "r", encoding="utf-8") as f:
            main_classes = json.load(f)

        # Add classes using add_class
        for m_class in main_classes:
            self.add_class(
                m_class["id"],
                pref_label=m_class["pref_label"],
                comment=m_class["comment"]
               )

        #--------------------
        # Adding subclasses
        #--------------------
        
        # HPC subclasses: Add using add_class
        self.load_and_add_classes("sub_HPC_classes.json", "HPCResource")

        # PIE subclasses: Add using add_class
        self.load_and_add_classes("sub_PIE_classes.json", "ProcessorIndicatorEstimator")
        
        # PhysChar subclasses: Add using add_class
        self.load_and_add_classes("sub_PhysChar_classes.json", "PhysicalCharacteristic")

        # Job subclasses: Add using add_class
        self.load_and_add_classes("sub_Job_classes.json", "Job")

        # Workflow subclasses: Add using add_class
        self.load_and_add_classes("sub_Workflow_classes.json", "Workflow")
# Missing: link between subclasses.
# CPU and GPU has specufucations, i.,e. DieSize (property), Workload, 

# Supercomputer has name, etc.




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
    
    def get_graph(self):
        """Return the RDF graph"""
        return self.graph
    
    def get_namespace(self):
        """Return the ExaAToW namespace"""
        return self.EXAATOW


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
    print(onto.serialize(destination="test.ttl",format="turtle"))
