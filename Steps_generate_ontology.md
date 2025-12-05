# ExA-AToW Ontology: Partner Guide with Examples

## 🎯 Quick Start: What You Need to Do

As an ExA-AToW partner, you need to define the **concepts** (classes), **relationships** (properties), and optionally **specific examples** (instances) for your domain area.

---

## 📚 Understanding the Building Blocks

### 1. **Classes** = Concepts/Things
Classes represent the "things" or "concepts" in your domain.

**Think of it as**: "What types of things exist in my area?"

**Examples:**
- In HPC: `ComputeNode`, `GPU`, `CPU`, `Memory`
- In Workflows: `WorkflowStep`, `DataTransfer`, `Task`
- In Jobs: `BatchJob`, `InteractiveJob`, `JobQueue`

### 2. **Properties** = Relationships
Properties define how classes relate to each other or what information they have.

**Two types:**

#### **ObjectProperty** = Connects two classes
**Think of it as**: "This thing is connected to that thing"

**Examples:**
- `hasProcessor` connects `ComputeNode` → `Processor`
- `executesOn` connects `Job` → `ComputeNode`
- `usesSoftware` connects `Workflow` → `SoftwareApplication`

#### **DatatypeProperty** = Connects a class to a value
**Think of it as**: "This thing has this measurable characteristic"

**Examples:**
- `hasCoreCount` connects `Processor` → integer number
- `hasMemorySize` connects `Memory` → number with unit
- `hasDuration` connects `Job` → time value

### 3. **Instances** = Specific Examples
Instances are concrete, real examples of your classes.

**Think of it as**: "A specific, named thing that exists"

**Examples:**
- `InMemory` is an instance of `DataManagementStorage`
- `SLURM` could be an instance of `JobScheduler`
- `MPI` could be an instance of `CommunicationLibrary`

### 4. **Restrictions (hasValue, hasUnit)**
Restrictions add constraints to properties, especially for measurements.

**Think of it as**: "This measurement must have a value AND a unit"

**Example:**
- `DieSize` must have both:
  - `hasValue`: the number (e.g., 450)
  - `hasUnit`: the unit (e.g., "mm²")

---

## 🔨 Step-by-Step: Building Your Ontology

We are creating individual ontologies for each area. These files will be created once you provide the content for classes and properties.


# Updating the Ontology

![Ontology construction description](resources/ontology_collaboration_description.png)

When modifying the ontology, update the appropriate JSON file(s) based on what you're changing:

## Adding New Classes

Each project area should have its own JSON file using the same structure.

### Entry Example
The `parent_class` field can be omitted if the entry directly belongs (subClassOf) to the class designated in the name of the JSON file.
```json
{
    "id": "ComputeNode",
    "parent_class": "HPCResource",
    "pref_label": {"en": "Node", "fr": "Noeud"},
    "comment": {
       "en": "A physical or virtual server that executes computational jobs within a partition.",
       "fr": "Un serveur physique ou virtuel qui exécute des tâches de calcul au sein d'une partition."
    },
    "link_html": "https://wiki.external.link" 
    "equivalent": "https://link.to.ontology#Concept"
}

```

### Steps:
- Edit the relevant `main_classes.json` or `sub_*_classes.json` file
- Add your class definition following the structure above
- Validate the JSON syntax before committing

## Adding Properties

The goal is to define relationships between existing classes using JSON property definitions. For example, connect a `Processor` class to a `DieSize` class using a `hasDieSize` property.

### Property Example
The `parent_class` field can be omitted if the entry directly belongs (subClassOf) to the class designated in the name of the JSON file.
```json
{
    "id": "hasDieSize",
    "property_type": "ObjectProperty",    
    "domain": "Processor",
    "range": "DieSize",
    "pref_label": {
        "en": "has die size",
        "fr": "a taille de puce"
    },
    "comment": {
        "en": "Processor has a die size, including a numeric value and a unit (e.g., mm²).",
        "fr": "Processeur a une taille de puce, incluant une valeur numérique et une unité (ex : mm²)."  
    }
}
```
### Steps:
*Option 1* : Add to existing file
- Add your property to an existing properties_*.json file if it fits that domain

*Option 2* : Create new file
- Create a new file: `properties_<your_field>.json` (in files folder)
- Add your properties as an array
- Register the file in `list_properties` in the ontology_generator.py file (`main`)


## Adding Instances

Only fixed instances will be included in the ontology.
To create instances for your area, create a JSON file with each instance defined as follows (see `files/instances_workflow.json` for reference):

### Instance Example
```json

{
    "instance_name": "InMemory",
    "class_type": "DataManagementStorage",
    "pref_label": {"en": "In-Memory", "fr": "En mémoire"},
    "comment": {
        "en": "Data held in RAM.",
        "fr": "Données conservées en RAM."
    }
}
```
### Steps:
- Modify `instances_workflow.json` or create a new instances file
- Add your instance definitions following the structure above
- Validate the JSON syntax before committing


## Visualization
To visualize the ontology:

- Use WebVOWL (through the ontology webpage generated with Widoco: XXXX)
- Open the `exaatow-ontology.ttl` with the open-source software Protege.
- visualization tool in the Python file. After loading the ontology:
```
onto.visualize_graph(
    output_file="my_ontology_visualization.html",
    height="600px",
    physics=False  # Disable physics for static layout
```
and open the html file with a browser.




# Example Domain: Authentication & Security

Let's say you're responsible for **Authentication** in ExA-AToW. Here's how to build it:

---

### **Step 1: Define Your Main Classes**

Create or edit `files/sub_Authentication_classes.json`:

```json
[
  {
    "id": "Credential",
    "parent_class": "AuthenticationEntity",
    "pref_label": {
      "en": "Credential",
      "fr": "Identifiant"
    },
    "comment": {
      "en": "A piece of information used to verify identity, such as passwords, tokens, or certificates.",
      "fr": "Information utilisée pour vérifier l'identité, comme les mots de passe, jetons ou certificats."
    }
  },
  {
    "id": "Password",
    "parent_class": "Credential",
    "pref_label": {
      "en": "Password",
      "fr": "Mot de passe"
    },
    "comment": {
      "en": "A secret string of characters used for authentication.",
      "fr": "Une chaîne secrète de caractères utilisée pour l'authentification."
    }
  },
  {
    "id": "AccessToken",
    "parent_class": "Credential",
    "pref_label": {
      "en": "Access Token",
      "fr": "Jeton d'accès"
    },
    "comment": {
      "en": "A time-limited credential granting access to protected resources.",
      "fr": "Un identifiant à durée limitée accordant l'accès aux ressources protégées."
    }
  },
  {
    "id": "AuthenticationProtocol",
    "parent_class": "AuthenticationEntity",
    "pref_label": {
      "en": "Authentication Protocol",
      "fr": "Protocole d'authentification"
    },
    "comment": {
      "en": "A standardized method for verifying user identity (e.g., OAuth, LDAP, Kerberos).",
      "fr": "Une méthode standardisée pour vérifier l'identité de l'utilisateur (ex : OAuth, LDAP, Kerberos)."
    }
  }
]
```

**Key Points:**
- `id`: Unique name for your class (use CamelCase)
- `parent_class`: What broader concept does this belong to?
- `pref_label`: Bilingual labels (EN/FR)
- `comment`: Clear explanation in both languages

---

### **Step 2: Define Properties (Relationships)**

Create or edit `files/properties_authentication.json`:

```json
[
  {
    "id": "usesCredential",
    "property_type": "ObjectProperty",
    "domain": "User",
    "range": "Credential",
    "pref_label": {
      "en": "uses credential",
      "fr": "utilise identifiant"
    },
    "comment": {
      "en": "Relates a user to the credential they use for authentication.",
      "fr": "Relie un utilisateur à l'identifiant qu'il utilise pour l'authentification."
    }
  },
  {
    "id": "implementsProtocol",
    "property_type": "ObjectProperty",
    "domain": "HPCSystem",
    "range": "AuthenticationProtocol",
    "pref_label": {
      "en": "implements protocol",
      "fr": "implémente protocole"
    },
    "comment": {
      "en": "Indicates which authentication protocol is used by an HPC system.",
      "fr": "Indique quel protocole d'authentification est utilisé par un système HPC."
    }
  },
  {
    "id": "hasExpirationTime",
    "property_type": "DatatypeProperty",
    "domain": "AccessToken",
    "range": "xsd:dateTime",
    "pref_label": {
      "en": "has expiration time",
      "fr": "a temps d'expiration"
    },
    "comment": {
      "en": "The date and time when the access token expires.",
      "fr": "La date et l'heure d'expiration du jeton d'accès."
    }
  },
  {
    "id": "hasTokenLength",
    "property_type": "DatatypeProperty",
    "domain": "AccessToken",
    "range": "xsd:integer",
    "pref_label": {
      "en": "has token length",
      "fr": "a longueur de jeton"
    },
    "comment": {
      "en": "The length of the token in characters or bytes.",
      "fr": "La longueur du jeton en caractères ou octets."
    }
  }
]
```

**Key Points:**
- **ObjectProperty**: Connects two classes (`domain` → `range`)
- **DatatypeProperty**: Connects a class to a data value
- `range` for datatypes uses XML Schema types: `xsd:string`, `xsd:integer`, `xsd:dateTime`, etc.

---

### **Step 3: Add Instances (Optional but Helpful)**

Create or edit `files/instances_authentication.json`:

```json
[
  {
    "instance_name": "OAuth2",
    "class_type": "AuthenticationProtocol",
    "pref_label": {
      "en": "OAuth 2.0",
      "fr": "OAuth 2.0"
    },
    "comment": {
      "en": "Industry-standard protocol for authorization.",
      "fr": "Protocole standard de l'industrie pour l'autorisation."
    }
  },
  {
    "instance_name": "Kerberos",
    "class_type": "AuthenticationProtocol",
    "pref_label": {
      "en": "Kerberos",
      "fr": "Kerberos"
    },
    "comment": {
      "en": "Network authentication protocol using tickets.",
      "fr": "Protocole d'authentification réseau utilisant des tickets."
    }
  },
  {
    "instance_name": "LDAP",
    "class_type": "AuthenticationProtocol",
    "pref_label": {
      "en": "LDAP",
      "fr": "LDAP"
    },
    "comment": {
      "en": "Lightweight Directory Access Protocol for directory services.",
      "fr": "Protocole d'accès aux annuaires pour les services d'annuaire."
    }
  }
]
```

---

### **Step 4: Add Restrictions with hasValue and hasUnit**

For properties that represent measurements, you need both a value and a unit.

Edit or create `files/add_restrictions_authentication_hasValue_hasUnit.json`:

```json
[
  {
    "class_name": "TokenSize",
    "has_value_property": "hasTokenSizeValue",
    "has_unit_property": "hasTokenSizeUnit"
  },
  {
    "class_name": "SessionDuration",
    "has_value_property": "hasSessionDurationValue",
    "has_unit_property": "hasSessionDurationUnit"
  }
]
```

**What this means:**
- `TokenSize` is a class that represents a measurement
- It MUST have two properties:
  - `hasTokenSizeValue` (e.g., 256)
  - `hasTokenSizeUnit` (e.g., "bits")

**Then define the property that uses it:**

In `properties_authentication.json`:

```json
{
  "id": "hasTokenSize",
  "property_type": "ObjectProperty",
  "domain": "AccessToken",
  "range": "TokenSize",
  "pref_label": {
    "en": "has token size",
    "fr": "a taille de jeton"
  },
  "comment": {
    "en": "The size of the access token, including value and unit (e.g., 256 bits).",
    "fr": "La taille du jeton d'accès, incluant valeur et unité (ex : 256 bits)."
  }
}
```

---

## 🌟 Complete Example: Processor with Die Size

Let's see a complete example from HPC:

### Classes (in `sub_HPC_classes.json`):

```json
[
  {
    "id": "Processor",
    "parent_class": "HPCResource",
    "pref_label": {"en": "Processor", "fr": "Processeur"},
    "comment": {
      "en": "A central processing unit in an HPC system.",
      "fr": "Une unité centrale de traitement dans un système HPC."
    }
  },
  {
    "id": "DieSize",
    "parent_class": "PhysicalCharacteristic",
    "pref_label": {"en": "Die Size", "fr": "Taille de puce"},
    "comment": {
      "en": "The physical size of a processor die.",
      "fr": "La taille physique d'une puce de processeur."
    }
  }
]
```

### Properties (in `properties_HPC.json`):

```json
[
  {
    "id": "hasDieSize",
    "property_type": "ObjectProperty",
    "domain": "Processor",
    "range": "DieSize",
    "pref_label": {"en": "has die size", "fr": "a taille de puce"},
    "comment": {
      "en": "Processor has a die size, including a numeric value and a unit (e.g., mm²).",
      "fr": "Processeur a une taille de puce, incluant une valeur numérique et une unité (ex : mm²)."
    }
  }
]
```

### Restrictions (in `add_restrictions_HPC_hasValue_hasUnit.json`):

```json
[
  {
    "class_name": "DieSize",
    "has_value_property": "hasDieSizeValue",
    "has_unit_property": "hasDieSizeUnit"
  }
]
```

**Result:** A `Processor` can have a `DieSize` of 450 mm² where:
- 450 is the `hasDieSizeValue`
- "mm²" is the `hasDieSizeUnit`

---

## 📋 Checklist for Partners

When creating your ontology section:

- [ ] **Identify your main concepts** (classes)
  - What are the key "things" in your domain?
  
- [ ] **Create class hierarchy**
  - Which concepts are subtypes of others?
  - Use `parent_class` to show relationships
  
- [ ] **Define relationships** (properties)
  - ObjectProperty: How do your classes connect to each other?
  - DatatypeProperty: What measurable attributes do they have?
  
- [ ] **Add measurement restrictions** (if needed)
  - Does your property need both value AND unit?
  - Add to `add_restrictions_hasValue_hasUnit.json`
  
- [ ] **Create instances** (optional)
  - Are there standard, fixed examples everyone should know?
  
- [ ] **Use bilingual labels** (EN/FR)
  - Provide both languages when possible
  
- [ ] **Write clear comments**
  - Explain what each concept means
  

  

## ❓ Common Questions

**Q: What's the difference between ObjectProperty and DatatypeProperty?**
- **ObjectProperty**: Links two classes together (e.g., Job → ComputeNode)
- **DatatypeProperty**: Links a class to a simple value (e.g., Job → duration in seconds)

**Q: When do I need hasValue/hasUnit?**
- Whenever you have a **measurement** that needs both a number and a unit
- Examples: size (450 mm²), memory (64 GB), power (250 W), time (30 minutes)

**Q: Should I create instances?**
- Only for **well-known, standard things** that everyone in the domain recognizes
- Examples: OAuth, SLURM, MPI, InMemory storage
- Don't create instances for user-specific or temporary things

**Q: How do I link my classes to existing ones?**
- Use `parent_class` to show your class is a subtype
- Use properties with appropriate `domain` and `range`
- Example: Your `GPUNode` can be a subclass of `ComputeNode`

**Q: Can I have multiple parent classes?**
- The current JSON structure supports one `parent_class`
- For multiple inheritance, discuss with the ontology coordinator

---
