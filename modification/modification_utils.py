import glob
import json
from typing import Dict, List, Optional


class OntologyItem:
    """
    Class representing a single Ontology item

    Args:
        id (str): The unique identifier for the ontology item.
        pref_label (Dict[str, str]): A dictionary containing the preferred labels in different languages.
        comment (Dict[str, str]): A dictionary containing the comments in different languages.
        parent_class (Optional["OntologyItem"]: The parent ontology entry, if needed.
    """

    __slots__ = ["_id", "_labels", "_comments", "_sourcefile", "_parent"]
    
    def __init__(
        self,
        id: str,
        pref_label: Dict[str, str],
        comment: Dict[str, str],
        sourcefile: str,
        parent_class: Optional["OntologyItem"] = None,
        ):
    
        self._id = id
        self._labels = pref_label
        self._comments = comment

        self._sourcefile = sourcefile  # Path to the JSON file where this item is defined

        self._parent = parent_class

    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OntologyItem):
            return False

        return hash(self) == hash(other)

    def __repr__(self) -> str:
        return f"OntologyItem({self.id})"
    
    @property
    def id(self) -> str:
        return self._id

    @property
    def label_en(self) -> str:
        return self._labels.get("en", self._id)

    @property
    def label_fr(self) -> str:
        return self._labels.get("fr", "")

    @property
    def comment_en(self) -> str:
        return self._comments.get("en", "")

    @property
    def comment_fr(self) -> str:
        return self._comments.get("fr", "")
    
    @property
    def sourcefile(self) -> str:
        return self._sourcefile
    
    @property
    def parent(self) -> Optional["OntologyItem"]:
        return self._parent
    
    def set_parent(self, parent: "OntologyItem") -> None:
        self._parent = parent

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "pref_label": {
                "en": self.label_en,
                "fr": self.label_fr,
            },
            "comment": {
                "en": self.comment_en,
                "fr": self.comment_fr,
            },
        }

        if self.parent is not None:
            data["parent_class"] = self.parent.id
        return data


class JSONOntology:
    """
    Create a primitive representation of the Ontology data.

    Data should be stored in JSON files within a directory

    Args:
        ontology_dir (str): Path to the directory containing JSON files representing the ontology.
    """
    
    __slots__ = ["_paths", "_entries"]

    def __init__(self, sourcedir: str):
        self._paths = sorted(glob.glob(f"{sourcedir}/*.json"))

        print("Creating JSONOntology using base paths:")
        for path in self.paths:
            print(f"  {path}")

        self._entries = {}
        self._add_initial_entries()
        print(f"Intial entries added: {len(self._entries)}")
    
    def __getitem__(self, id: str) -> OntologyItem:
        if id in self._entries:
            return self._entries[id]
        
        raise KeyError(f"OntologyItem with id '{id}' does not exist")
    
    def _add_initial_entries(self):
        """
        Populate the initial entries from what's present in the json directory
        """
        has_parents = {}
        # Read all json files, concatenating into a single list
        for path in self.paths:
            with open(path) as f:
                data = json.load(f)
                
            while data:
                item = data.pop(0)

                parent_id = item.pop("parent_class", None)
                if parent_id is not None:
                    has_parents[item["id"]] = parent_id

                self.add_entry(sourcefile=path, **item)

        # Link any entries that have parents
        for id, parent_id in has_parents.items():
            self.entries[id].set_parent(self.entries[parent_id])

    @property
    def paths(self) -> List[str]:
        return self._paths
    
    def add_entry(self, *args, force: bool = False, **kwargs):
        entry = OntologyItem(*args, **kwargs)

        if not force and entry in self._entries:
            raise ValueError(f"Entry with ID {entry.id} already exists")

        self._entries[entry.id] = entry

    @property
    def entries(self) -> Dict[str, OntologyItem]:
        return self._entries

    def dump_to_json(self) -> None:
        for file in self._paths:
            with open(file, 'r', encoding="utf-8") as f:
                data = json.load(f)

            existing_ids = [item["id"] for item in data]
            
            for entry in self.entries.values():
                if not entry.sourcefile == file:
                    continue
                
                if entry.id in existing_ids:
                    continue

                data.append(entry.to_dict())

            with open(file, "w+", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write('\n')
