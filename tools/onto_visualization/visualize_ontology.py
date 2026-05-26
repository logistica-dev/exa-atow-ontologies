#!/usr/bin/env python3
"""
visualize_ontology.py
─────────────────────
Parses an OWL/RDF Turtle (.ttl) ontology and generates a self-contained
interactive HTML visualization using vis.js (loaded from CDN).

Features:
  - Nodes colored by type (Class, Property, Instance)
  - Edge labels for relationship type (subClassOf, domain, range, etc.)
  - Click on any node → tooltip with rdfs:comment (EN + FR)
  - Hover → node label
  - Physics-based layout with toggle
  - Filter panel to show/hide edge types
  - Search box to highlight nodes

Usage:
    python3 visualize_ontology.py my_ontology.ttl
    python3 visualize_ontology.py my_ontology.ttl --output my_graph.html
    python3 visualize_ontology.py my_ontology.ttl --mode classes   (default: classes only)
    python3 visualize_ontology.py my_ontology.ttl --mode full      (classes + properties + instances)
"""

import re
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict


# ─── Turtle parser ────────────────────────────────────────────────────────────

def expand_prefix(term, prefixes):
    """Expand a prefixed name like exa-atow:CPU to its full URI."""
    if term.startswith('<') and term.endswith('>'):
        return term[1:-1]
    if ':' in term:
        prefix, local = term.split(':', 1)
        if prefix in prefixes:
            return prefixes[prefix] + local
    return term


def short_name(uri):
    """Return the local name of a URI (after # or last /)."""
    if '#' in uri:
        return uri.split('#')[-1]
    return uri.split('/')[-1]


def parse_ttl(filepath):
    """
    Minimal Turtle parser that extracts:
      - prefixes
      - triples (subject, predicate, object)
      - rdfs:comment values (EN and FR)
      - skos:prefLabel values
    """
    text = Path(filepath).read_text(encoding='utf-8')

    # ── 1. Extract prefix declarations ──
    prefixes = {}
    for m in re.finditer(r'@prefix\s+(\S+):\s+<([^>]+)>', text):
        prefixes[m.group(1)] = m.group(2)

    # ── 2. Strip comments (lines starting with #) ──
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith('#'):
            lines.append(line)
    text_clean = '\n'.join(lines)

    # ── 3. Extract triples via regex (handles most common TTL patterns) ──
    triples = []

    # Pattern: subject predicate object (object can be URI, prefixed, or literal)
    # We collect all statements for each subject block

    # Remove string literals with their content first (to avoid false matches)
    # then process
    
    # Tokenize: replace multiline strings
    text_clean = re.sub(r'""".*?"""', '""MLSTRING""', text_clean, flags=re.DOTALL)

    # Split into statement blocks (subjects)
    # Find subject ; predicate ; predicate . blocks
    
    def tokenize(s):
        """Very simple tokenizer for Turtle."""
        tokens = []
        i = 0
        while i < len(s):
            # Skip whitespace
            if s[i] in ' \t\n\r':
                i += 1
                continue
            # String literal with language tag
            if s[i] == '"':
                j = i + 1
                while j < len(s) and s[j] != '"':
                    if s[j] == '\\':
                        j += 2
                    else:
                        j += 1
                j += 1  # closing "
                # check for language tag @xx or datatype ^^
                if j < len(s) and s[j] == '@':
                    k = j + 1
                    while k < len(s) and s[k] not in ' \t\n\r;.,)':
                        k += 1
                    tokens.append(s[i:k])
                    i = k
                elif j + 1 < len(s) and s[j:j+2] == '^^':
                    k = j + 2
                    while k < len(s) and s[k] not in ' \t\n\r;.,)':
                        k += 1
                    tokens.append(s[i:k])
                    i = k
                else:
                    tokens.append(s[i:j])
                    i = j
            # URI
            elif s[i] == '<':
                j = s.index('>', i) + 1
                tokens.append(s[i:j])
                i = j
            # Punctuation
            elif s[i] in '.,;()[]':
                tokens.append(s[i])
                i += 1
            # Everything else (prefixed names, keywords)
            else:
                j = i
                while j < len(s) and s[j] not in ' \t\n\r.,;()[]':
                    j += 1
                tokens.append(s[i:j])
                i = j
        return tokens

    tokens = tokenize(text_clean)

    # Parse tokens into triples
    i = 0
    subject = None
    predicate = None

    def is_term(t):
        return t and t not in ['.', ';', ',', '(', ')', '[', ']', 'a',
                                'rdf:type', 'owl:Ontology']

    while i < len(tokens):
        t = tokens[i]

        if t == '.':
            subject = None
            predicate = None
            i += 1
            continue

        if t == ';':
            predicate = None
            i += 1
            continue

        if t == ',':
            # same subject, same predicate, new object
            i += 1
            continue

        if t in ('(', ')', '[', ']'):
            i += 1
            continue

        # Skip blank node openings
        if t == '_:':
            i += 1
            continue

        if subject is None:
            subject = expand_prefix(t, prefixes)
            i += 1
            continue

        if predicate is None:
            if t == 'a':
                predicate = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
            else:
                predicate = expand_prefix(t, prefixes)
            i += 1
            continue

        # Object
        obj_raw = t
        if obj_raw.startswith('"') or obj_raw == '""MLSTRING""':
            # literal — store as-is
            obj = obj_raw
        else:
            obj = expand_prefix(obj_raw, prefixes)

        if subject and predicate and obj:
            triples.append((subject, predicate, obj))

        i += 1

    return triples, prefixes


# ─── Graph builder ────────────────────────────────────────────────────────────

RDF_TYPE   = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
RDFS_SCO   = 'http://www.w3.org/2000/01/rdf-schema#subClassOf'
RDFS_DOM   = 'http://www.w3.org/2000/01/rdf-schema#domain'
RDFS_RNG   = 'http://www.w3.org/2000/01/rdf-schema#range'
RDFS_CMT   = 'http://www.w3.org/2000/01/rdf-schema#comment'
RDFS_LBL   = 'http://www.w3.org/2000/01/rdf-schema#label'
SKOS_PREF  = 'http://www.w3.org/2004/02/skos/core#prefLabel'
OWL_CLASS  = 'http://www.w3.org/2002/07/owl#Class'
OWL_OP     = 'http://www.w3.org/2002/07/owl#ObjectProperty'
OWL_DP     = 'http://www.w3.org/2002/07/owl#DatatypeProperty'
OWL_AP     = 'http://www.w3.org/2002/07/owl#AnnotationProperty'
OWL_EQC    = 'http://www.w3.org/2002/07/owl#equivalentClass'
OWL_INV    = 'http://www.w3.org/2002/07/owl#inverseOf'
OWL_SUB    = 'http://www.w3.org/2002/07/owl#subPropertyOf'
OWL_ONTO   = 'http://www.w3.org/2002/07/owl#Ontology'
RDFS_SUBP  = 'http://www.w3.org/2000/01/rdf-schema#subPropertyOf'


def build_graph(triples, mode='classes'):
    """
    Build nodes and edges for vis.js.
    mode = 'classes'  → only classes and subClassOf / equivalentClass
    mode = 'full'     → classes + properties (with domain/range) + instances
    """
    # Collect types
    types = defaultdict(set)
    comments_en = {}
    comments_fr = {}
    labels = {}

    for s, p, o in triples:
        if p == RDF_TYPE:
            types[s].add(o)
        if p == RDFS_CMT:
            if o.endswith('@en"') or o.endswith('"@en'):
                val = re.sub(r'^"|"@en$|"@en"$', '', o).strip('"')
                comments_en[s] = val
            elif o.endswith('@fr"') or o.endswith('"@fr'):
                val = re.sub(r'^"|"@fr$|"@fr"$', '', o).strip('"')
                comments_fr[s] = val
            elif s not in comments_en:
                val = o.strip('"')
                comments_en[s] = val
        if p in (SKOS_PREF, RDFS_LBL):
            if o.endswith('@en"') or o.endswith('"@en'):
                val = re.sub(r'^"|"@en$|"@en"$', '', o).strip('"')
                labels[s] = val
            elif s not in labels:
                labels[s] = re.sub(r'"@\w+$', '', o).strip('"')

    def get_label(uri):
        if uri in labels:
            return labels[uri]
        return short_name(uri)



    def get_tooltip(uri):
        parts = [f"<b>{get_label(uri)}  ", f"<i>{short_name(uri)}</i>", ""]
        if uri in comments_en:
            parts.append(f"🇬🇧 {comments_en[uri]}")
        if uri in comments_fr:
            parts.append(f"🇫🇷 {comments_fr[uri]}")
        return " ".join(parts)
    
    
    # Colour scheme — fixed roles (type-based, agnostic)
    COLOR_PROP_OBJ = {"background": "#5C6BC0", "border": "#3949ab", "font": "white"}
    COLOR_PROP_DT  = {"background": "#26A69A", "border": "#00796b", "font": "white"}
    COLOR_INSTANCE = {"background": "#FF7043", "border": "#bf360c", "font": "gray"}

    # Palette for class branches — auto-assigned per top-level branch
    BRANCH_PALETTE = [
        {"background": "#2E86AB", "border": "#1a5f7a", "font": "white"},  # blue
        {"background": "#7B1FA2", "border": "#4a0072", "font": "white"},  # purple
        {"background": "#C62828", "border": "#7f0000", "font": "white"},  # red
        {"background": "#F9A825", "border": "#f57f17", "font": "white"},  # yellow
        {"background": "#2E7D32", "border": "#1b5e20", "font": "white"},  # green
        {"background": "#00838F", "border": "#005662", "font": "white"},  # teal
        {"background": "#AD1457", "border": "#78002e", "font": "white"},  # pink
        {"background": "#4527A0", "border": "#1a0072", "font": "white"},  # deep purple
        {"background": "#E65100", "border": "#ac1900", "font": "white"},  # deep orange
        {"background": "#37474F", "border": "#102027", "font": "white"},  # blue grey
    ]
    COLOR_ROOT = {"background": "#1a3a4a", "border": "#000", "font": "white"}  # root node

    # Build parent map: child → parent (via subClassOf)
    parent_map = {}
    for s, p, o in triples:
        if p == RDFS_SCO and not o.startswith('_'):
            parent_map[s] = o

    # Find root classes (no parent, or parent is owl:Thing)
    OWL_THING = 'http://www.w3.org/2002/07/owl#Thing'
    all_classes = {s for s, p, o in triples
                   if p == RDF_TYPE and o == OWL_CLASS}

    def get_root_branch(uri, depth=0):
        """Walk up subClassOf chain to find the top-level branch (depth=1 from root)."""
        if depth > 20:  # cycle guard
            return uri
        parent = parent_map.get(uri)
        if parent is None or parent == OWL_THING:
            return uri  # this IS a root
        grandparent = parent_map.get(parent)
        if grandparent is None or grandparent == OWL_THING:
            return parent  # parent is root → we are a direct child = branch root
        return get_root_branch(parent, depth + 1)

    # branch_color_map will be built after include_uris is populated
    branch_color_map = {}

    def node_color(uri, uri_types):
        if OWL_OP in uri_types:
            return COLOR_PROP_OBJ
        if OWL_DP in uri_types:
            return COLOR_PROP_DT
        if OWL_CLASS in uri_types or uri in parent_map:
            # Root node itself
            if uri not in parent_map or parent_map.get(uri) in (None, OWL_THING):
                return COLOR_ROOT
            branch = get_root_branch(uri)
            return branch_color_map.get(branch, BRANCH_PALETTE[0])
        # Instance
        if uri_types - {OWL_ONTO, OWL_AP}:
            return COLOR_INSTANCE
        return BRANCH_PALETTE[0]

    # Build node set
    nodes_dict = {}
    edges = []

    # Determine which URIs to include
    include_uris = set()

    for s, p, o in triples:
        s_types = types.get(s, set())

        # Always include classes
        if OWL_CLASS in s_types:
            include_uris.add(s)

        # subClassOf between classes
        if p == RDFS_SCO and not o.startswith('_'):
            include_uris.add(s)
            include_uris.add(o)

        if mode in ('full', 'instances'):
            # instances: subjects that have rdf:type pointing to a known class
            if p == RDF_TYPE and o not in (OWL_CLASS, OWL_OP, OWL_DP, OWL_AP, OWL_ONTO):
                if OWL_CLASS not in s_types and OWL_OP not in s_types and OWL_DP not in s_types:
                    include_uris.add(s)
                    include_uris.add(o)  # ensure target class is included

        if mode == 'full':
            if OWL_OP in s_types or OWL_DP in s_types:
                include_uris.add(s)

    # Filter out external URIs (not in our namespace) for cleaner graph
    ns_prefix = None
    for s, p, o in triples:
        if p == RDF_TYPE and o == OWL_ONTO:
            # s is the ontology URI, extract base namespace
            if '#' in s:
                ns_prefix = s.split('#')[0] + '#'
            break

    def is_own(uri):
        if ns_prefix and uri.startswith(ns_prefix):
            return True
        # Also include blank nodes and owl built-ins we want
        if uri.startswith('http://www.w3.org/2002/07/owl#'):
            return False
        if uri.startswith('http://www.w3.org/1999/02/22-rdf-syntax-ns#'):
            return False
        if uri.startswith('http://www.w3.org/2000/01/rdf-schema#'):
            return False
        if uri.startswith('_:'):
            return False
        return True

    include_uris = {u for u in include_uris if is_own(u)}

    # Assign a color index to each top-level branch (now include_uris is known)
    branch_roots = sorted(set(
        get_root_branch(c) for c in all_classes
        if c in include_uris
    ))
    branch_color_map = {
        root: BRANCH_PALETTE[i % len(BRANCH_PALETTE)]
        for i, root in enumerate(branch_roots)
    }

    # Build vis.js nodes
    node_id_map = {}
    for idx, uri in enumerate(sorted(include_uris)):
        nid = idx
        node_id_map[uri] = nid
        sn = short_name(uri)
        color_info = node_color(uri, types.get(uri, set()))
        nodes_dict[uri] = {
            "id": nid,
            "label": get_label(uri),
            "title": get_tooltip(uri),
            "color": {
                "background": color_info["background"],
                "border": color_info["border"],
            },
            "font": {"color": color_info.get("font", "white")},
            "shape": "box" if OWL_CLASS in types.get(uri, set()) else
                     "ellipse" if (OWL_OP in types.get(uri, set()) or
                                   OWL_DP in types.get(uri, set())) else "dot",
        }

    # Build edges
    edge_id = 0
    seen_edges = set()

    EDGE_STYLES = {
        'subClassOf':     {"color": "#555", "dashes": False, "width": 2},
        'equivalentClass':{"color": "#E91E63", "dashes": [5,5], "width": 2},
        'domain':         {"color": "#1565C0", "dashes": [3,3], "width": 1},
        'range':          {"color": "#2E7D32", "dashes": [3,3], "width": 1},
        'subPropertyOf':  {"color": "#6A1B9A", "dashes": [5,3], "width": 1},
        'inverseOf':      {"color": "#E65100", "dashes": [5,5], "width": 1},
        'type':           {"color": "#FF7043", "dashes": [4,3], "width": 1.5},
    }

    def add_edge(src, tgt, label, etype='subClassOf'):
        nonlocal edge_id
        key = (src, tgt, label)
        if key in seen_edges:
            return
        if src not in node_id_map or tgt not in node_id_map:
            return
        seen_edges.add(key)
        style = EDGE_STYLES.get(etype, EDGE_STYLES['subClassOf'])
        edges.append({
            "id": edge_id,
            "from": node_id_map[src],
            "to": node_id_map[tgt],
            "label": label,
            "type": etype,
            "arrows": "to",
            "dashes": style["dashes"],
            "color": {"color": style["color"]},
            "width": style["width"],
            "font": {"size": 9, "color": "#444", "align": "middle"},
            "smooth": {"type": "curvedCW", "roundness": 0.1},
        })
        edge_id += 1

    for s, p, o in triples:
        if s not in include_uris or o not in include_uris:
            continue
        sn_p = short_name(p)

        if p == RDFS_SCO:
            add_edge(s, o, 'subClassOf', 'subClassOf')
        elif p == OWL_EQC:
            add_edge(s, o, 'equivalentClass', 'equivalentClass')
        elif p == OWL_INV:
            add_edge(s, o, 'inverseOf', 'inverseOf')
        elif p in (RDFS_SUBP, OWL_SUB):
            add_edge(s, o, 'subPropertyOf', 'subPropertyOf')
        elif p == RDFS_DOM and mode == 'full':
            add_edge(s, o, 'domain', 'domain')
        elif p == RDFS_RNG and mode == 'full':
            add_edge(s, o, 'range', 'range')
        elif p == RDF_TYPE and mode in ('full', 'instances'):
            # only draw type edges for instances (not class→owl:Class)
            s_types_local = types.get(s, set())
            if OWL_CLASS not in s_types_local and OWL_OP not in s_types_local and OWL_DP not in s_types_local:
                add_edge(s, o, 'type', 'type')

    nodes_list = list(nodes_dict.values())
    return nodes_list, edges


# ─── HTML generator ───────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Ontology Visualizer — {title}</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #e8f4f8; color: #1a1a2e; display: flex; flex-direction: column; height: 100vh; }}

  #header {{ background: #c5dfe8; padding: 10px 20px; display: flex; align-items: center; gap: 16px; border-bottom: 1px solid #a0c8d8; flex-shrink: 0; }}
  #header h1 {{ font-size: 15px; color: #1a3a4a; white-space: nowrap; }}

  #search {{ padding: 6px 12px; border-radius: 20px; border: 1px solid #a0c8d8; background: white; color: #1a1a2e; font-size: 13px; width: 220px; }}
  #search:focus {{ outline: none; border-color: #2E86AB; }}

  #controls {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
  .toggle-btn {{ padding: 4px 10px; border-radius: 12px; border: 1px solid #a0c8d8; background: #daedf5; color: #1a3a4a; cursor: pointer; font-size: 11px; transition: all 0.2s; }}
  .toggle-btn.active {{ background: #2E86AB; border-color: #2E86AB; color: white; }}

  #main {{ display: flex; flex: 1; overflow: hidden; }}
  #graph {{ flex: 1; background: #f0f8fb; }}

  #sidebar {{ width: 280px; background: #daedf5; border-left: 1px solid #a0c8d8; padding: 16px; overflow-y: auto; flex-shrink: 0; font-size: 12px; color: #1a1a2e; }}
  #sidebar h2 {{ font-size: 13px; color: #1a5f7a; margin-bottom: 12px; border-bottom: 1px solid #a0c8d8; padding-bottom: 6px; }}
  #node-info {{ line-height: 1.6; }}
  #node-info .label {{ font-size: 15px; font-weight: bold; color: #1a5f7a; margin-bottom: 4px; }}
  #node-info .uri {{ font-size: 10px; color: #555; margin-bottom: 10px; word-break: break-all; }}
  #node-info .comment {{ margin-top: 8px; padding: 8px; background: white; border-radius: 6px; line-height: 1.5; border: 1px solid #a0c8d8; }}
  #node-info .lang-flag {{ font-size: 11px; color: #777; }}

  #legend {{ margin-top: 16px; }}
  #legend h3 {{ font-size: 11px; color: #1a5f7a; margin-bottom: 8px; }}
  .leg-item {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 11px; color: #1a1a2e; }}
  .leg-dot {{ width: 14px; height: 14px; border-radius: 3px; flex-shrink: 0; }}

  #stats {{ margin-top: 16px; font-size: 11px; color: #555; line-height: 1.8; }}
  
  #physics-btn {{ padding: 4px 10px; border-radius: 12px; border: 1px solid #a0c8d8; background: #daedf5; color: #1a3a4a; cursor: pointer; font-size: 11px; }}
  #physics-btn.active {{ background: #26A69A; border-color: #26A69A; color: white; }}

  .placeholder {{ color: #888; font-style: italic; font-size: 11px; margin-top: 20px; text-align: center; }}
</style>
</head>
<body>

<div id="header">
  <h1>🔷 {title}</h1>
  <input id="search" type="text" placeholder="Search nodes…" oninput="searchNodes(this.value)">
  <div id="controls">
    <span style="font-size:11px;color:#888">Show edges:</span>
    <button class="toggle-btn active" data-type="subClassOf" onclick="toggleEdge(this)">subClassOf</button>
    <button class="toggle-btn active" data-type="equivalentClass" onclick="toggleEdge(this)">equivalentClass</button>
    <button class="toggle-btn active" data-type="subPropertyOf" onclick="toggleEdge(this)">subPropertyOf</button>
    <button class="toggle-btn" data-type="domain" onclick="toggleEdge(this)">domain</button>
    <button class="toggle-btn" data-type="range" onclick="toggleEdge(this)">range</button>
    <button class="toggle-btn" data-type="inverseOf" onclick="toggleEdge(this)">inverseOf</button>
    <button class="toggle-btn active" data-type="type" onclick="toggleEdge(this)">rdf:type</button>
  </div>
  <button id="physics-btn" class="active" onclick="togglePhysics(this)">⚡ Physics ON</button>
  <button class="toggle-btn" onclick="network.fit()">⊞ Fit</button>
</div>

<div id="main">
  <div id="graph"></div>
  <div id="sidebar">
    <div id="legend">
      <h3>Legend — Node types</h3>
      <div id="branch-legend"></div>
      <div class="leg-item"><div class="leg-dot" style="background:#5C6BC0"></div>Object property</div>
      <div class="leg-item"><div class="leg-dot" style="background:#26A69A"></div>Datatype property</div>
      <div class="leg-item"><div class="leg-dot" style="background:#FF7043"></div>Instance</div>
      <div class="leg-item"><div class="leg-dot" style="background:#1a3a4a"></div>Root class</div>
      <br>
      <h3>Legend — Edge types</h3>
      <div class="leg-item"><div class="leg-dot" style="background:#555;border-radius:0;height:3px;margin-top:5px"></div>subClassOf</div>
      <div class="leg-item"><div class="leg-dot" style="background:#E91E63;border-radius:0;height:2px;margin-top:5px"></div>equivalentClass</div>
      <div class="leg-item"><div class="leg-dot" style="background:#1565C0;border-radius:0;height:2px;margin-top:5px"></div>domain</div>
      <div class="leg-item"><div class="leg-dot" style="background:#2E7D32;border-radius:0;height:2px;margin-top:5px"></div>range</div>
      <div class="leg-item"><div class="leg-dot" style="background:#888;border-radius:0;height:2px;margin-top:5px;border-top:2px dotted #888"></div>rdf:type</div>
    </div>
    <h2>Node Inspector</h2>
    <div id="node-info">
      <div class="placeholder">Click any node to see its description</div>
    </div>
    <div id="stats">
      <b>Graph stats</b><br>
      Nodes: {node_count}<br>
      Edges: {edge_count}<br>
      Mode: {mode}
    </div>
  </div>
</div>

<script>
const ALL_NODES = {nodes_json};
const ALL_EDGES = {edges_json};

// Node data map for inspector
const nodeData = {{}};
ALL_NODES.forEach(n => {{ nodeData[n.id] = n; }});

// Edge data
const edgeData = {{}};
ALL_EDGES.forEach(e => {{ edgeData[e.id] = e; }});

// Visible edge types
const visibleTypes = new Set(['subClassOf', 'equivalentClass', 'subPropertyOf', 'inverseOf', 'type']);

function getVisibleEdges() {{
  return ALL_EDGES.filter(e => visibleTypes.has(e.type));
}}

const nodesDS = new vis.DataSet(ALL_NODES);
const edgesDS = new vis.DataSet(getVisibleEdges());

const container = document.getElementById('graph');
const options = {{
  physics: {{
    enabled: true,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {{
      gravitationalConstant: -80,
      centralGravity: 0.01,
      springLength: 120,
      springConstant: 0.08,
      damping: 0.4,
    }},
    stabilization: {{ iterations: 200 }},
  }},
  interaction: {{
    hover: true,
    tooltipDelay: 200,
    navigationButtons: true,
    keyboard: true,
  }},
  edges: {{
    font: {{ size: 9, color: '#aaa', strokeWidth: 0 }},
    smooth: {{ type: 'curvedCW', roundness: 0.1 }},
  }},
  nodes: {{
    borderWidth: 1.5,
    borderWidthSelected: 3,
    font: {{ size: 11 }},
  }},
}};

// Build branch legend dynamically from node colors
const branchLegend = document.getElementById('branch-legend');
const seenColors = new Map();
ALL_NODES.forEach(function(n) {{
  if (n.shape === 'box' && n.color.background !== '#1a3a4a') {{
    var bg = n.color.background;
    if (!seenColors.has(bg)) {{
      seenColors.set(bg, n.label);
      var div = document.createElement('div');
      div.className = 'leg-item';
      div.innerHTML = '<div class="leg-dot" style="background:' + bg + '"></div>' + n.label + ' branch';
      branchLegend.appendChild(div);
    }}
  }}
}});

const network = new vis.Network(container, {{ nodes: nodesDS, edges: edgesDS }}, options);

// ── Node click → inspector ──
network.on('click', function(params) {{
  if (params.nodes.length > 0) {{
    const nid = params.nodes[0];
    const n = nodeData[nid];
    if (!n) return;

    // Parse tooltip back to structured info
    const titleHtml = n.title || '';
    document.getElementById('node-info').innerHTML = titleHtml
      .replace(/<b>(.*?)<\/b>/, '<div class="label">$1</div>')
      .replace(/<i>(.*?)<\/i>/, '<div class="uri">$1</div>')
      .replace(/🇬🇧 (.*?)(<br>|$)/g, '<div class="comment"><span class="lang-flag">🇬🇧 EN</span><br>$1</div>')
      .replace(/🇫🇷 (.*?)(<br>|$)/g, '<div class="comment"><span class="lang-flag">🇫🇷 FR</span><br>$1</div>');
  }}
}});

// ── Search ──
function searchNodes(query) {{
  if (!query) {{
    nodesDS.update(ALL_NODES.map(n => ({{ id: n.id, opacity: 1, borderWidth: 1.5 }})));
    return;
  }}
  const q = query.toLowerCase();
  const updates = ALL_NODES.map(n => {{
    const match = n.label.toLowerCase().includes(q) || (n.title || '').toLowerCase().includes(q);
    return {{ id: n.id, opacity: match ? 1 : 0.15, borderWidth: match ? 3 : 1 }};
  }});
  nodesDS.update(updates);
}}

// ── Toggle edge types ──
function toggleEdge(btn) {{
  const etype = btn.dataset.type;
  btn.classList.toggle('active');
  if (visibleTypes.has(etype)) {{
    visibleTypes.delete(etype);
  }} else {{
    visibleTypes.add(etype);
  }}
  edgesDS.clear();
  edgesDS.add(getVisibleEdges());
}}

// ── Toggle physics ──
let physicsOn = true;
function togglePhysics(btn) {{
  physicsOn = !physicsOn;
  network.setOptions({{ physics: {{ enabled: physicsOn }} }});
  btn.textContent = physicsOn ? '⚡ Physics ON' : '⚡ Physics OFF';
  btn.classList.toggle('active', physicsOn);
}}
</script>
</body>
</html>
"""


def generate_html(nodes, edges, title, mode, output_path):
    html = HTML_TEMPLATE.format(
        title=title,
        nodes_json=json.dumps(nodes, ensure_ascii=False),
        edges_json=json.dumps(edges, ensure_ascii=False),
        node_count=len(nodes),
        edge_count=len(edges),
        mode=mode,
    )
    Path(output_path).write_text(html, encoding='utf-8')
    print(f"✅  Saved: {output_path}  ({len(nodes)} nodes, {len(edges)} edges)")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Visualize OWL/TTL ontology as interactive HTML')
    parser.add_argument('input', help='Path to .ttl file')
    parser.add_argument('--output', '-o', help='Output HTML path (default: <input>.html)')
    parser.add_argument('--mode', choices=['classes', 'instances', 'full'], default='classes',
                        help='classes = class hierarchy only; instances = classes + instances; full = classes + instances + properties')
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = args.output or input_path.with_suffix('.html')
    title = f"Ontology — {input_path.name}"

    print(f"Parsing {input_path}...")
    triples, prefixes = parse_ttl(input_path)
    print(f"  → {len(triples)} triples, {len(prefixes)} prefixes")

    print(f"Building graph (mode={args.mode})...")
    nodes, edges = build_graph(triples, mode=args.mode)
    print(f"  → {len(nodes)} nodes, {len(edges)} edges")

    generate_html(nodes, edges, title, args.mode, output_path)


if __name__ == '__main__':
    main()
