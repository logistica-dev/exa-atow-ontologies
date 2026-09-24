#!/usr/bin/env python3
"""
cwl_to_ttl.py
=============
Reads a CWL workflow file (Workflow + referenced CommandLineTool/ExpressionTool)
and generates an OWL/Turtle ABox instance using:
  - exato-wf  (core workflow ontology)
  - exato-wf-cwl  (CWL extension)

Usage:
    python cwl_to_ttl.py kinetic_energy_workflow.cwl -o output_instance.ttl
    python cwl_to_ttl.py my_workflow.cwl --base http://example.org/myns# -o out.ttl

The script resolves all 'run:' references relative to the main CWL file,
so it works with split CWL (one file per tool) or packed CWL.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

# ─── Ontology namespaces ────────────────────────────────────────────────────

EXATO_WF     = Namespace("https://w3id.org/Exa-AToW/exato-wf.ttl#")
EXATO_WF_CWL = Namespace("https://raw.githubusercontent.com/cnherrera/Exa-AToW_onto/refs/heads/main/workflow_ontology/exato-wf-cwl-extension.ttl#")
PROV         = Namespace("http://www.w3.org/ns/prov#")
WFDESC       = Namespace("http://purl.org/wf4ever/wfdesc#")
SKOS         = Namespace("http://www.w3.org/2004/02/skos/core#")


# ─── Helpers ────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Turn any string into a safe URI local name."""
    text = re.sub(r"[^\w]", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def load_cwl(path: Path) -> dict:
    """Load a YAML/CWL file and return as dict."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_run(run_ref: Any, base_dir: Path) -> tuple[dict | None, str]:
    """
    Resolve a 'run:' field value.
    Returns (cwl_dict_or_None, label_hint).
    If run_ref is a string (file path), load and return that file.
    If it's already an inline dict, return it directly.
    """
    if isinstance(run_ref, str):
        tool_path = base_dir / run_ref
        if tool_path.exists():
            return load_cwl(tool_path), tool_path.stem
    elif isinstance(run_ref, dict):
        return run_ref, run_ref.get("label", run_ref.get("id", "inline_tool"))
    return None, str(run_ref)


def cwl_type_to_xsd(cwl_type: Any) -> URIRef:
    """Map a CWL primitive type string to an XSD type URI."""
    mapping = {
        "float":   XSD.float,
        "double":  XSD.double,
        "int":     XSD.integer,
        "long":    XSD.long,
        "string":  XSD.string,
        "boolean": XSD.boolean,
        "File":    XSD.anyURI,
        "null":    OWL.Nothing,
    }
    if isinstance(cwl_type, str):
        # Handle optional types like "float?" → strip "?"
        base = cwl_type.rstrip("?").split("[]")[0]
        return mapping.get(base, XSD.string)
    return XSD.string


# ─── Core converter ─────────────────────────────────────────────────────────

class CWLToTTL:
    """
    Converts a CWL Workflow document into an OWL/Turtle instance graph
    using the exato-wf and exato-wf-cwl ontologies.
    """

    def __init__(self, cwl_path: Path, base_ns: str):
        self.cwl_path = cwl_path
        self.base_dir = cwl_path.parent
        self.NS = Namespace(base_ns)
        self.g = Graph()
        self._bind_prefixes()

    def _bind_prefixes(self):
        g = self.g
        g.bind("rdf",          RDF)           # explicit @prefix rdf: <...> in output
        g.bind("exato-wf",     EXATO_WF)
        g.bind("exato-wf-cwl", EXATO_WF_CWL)
        g.bind("prov",         PROV)
        g.bind("wfdesc",       WFDESC)
        g.bind("skos",         SKOS)
        g.bind("owl",          OWL)
        g.bind("rdfs",         RDFS)
        g.bind("xsd",          XSD)
        g.bind("inst",         self.NS)

    # ── Workflow-level ───────────────────────────────────────────────────────

    def _add_workflow(self, cwl: dict, wf_uri: URIRef):
        g = self.g
        g.add((wf_uri, RDF.type,       OWL.NamedIndividual))
        g.add((wf_uri, RDF.type,       EXATO_WF_CWL.CWLWorkflow))
        g.add((wf_uri, RDF.type,       EXATO_WF.Workflow))

        label = cwl.get("label") or cwl.get("id") or self.cwl_path.stem
        g.add((wf_uri, RDFS.label,               Literal(label, lang="en")))
        g.add((wf_uri, EXATO_WF.workflowName,    Literal(label, datatype=XSD.string)))

        if "doc" in cwl:
            g.add((wf_uri, EXATO_WF.workflowDescription, Literal(cwl["doc"], datatype=XSD.string)))
            g.add((wf_uri, RDFS.comment,                  Literal(cwl["doc"], lang="en")))

        if "cwlVersion" in cwl:
            g.add((wf_uri, EXATO_WF_CWL.cwlVersion, Literal(cwl["cwlVersion"], datatype=XSD.string)))

        g.add((wf_uri, EXATO_WF_CWL.cwlClass, Literal("Workflow", datatype=XSD.string)))

        # Canonical CWL workflow properties
        g.add((wf_uri, EXATO_WF.hasCompositionMethod, EXATO_WF.SchemaBased))
        g.add((wf_uri, EXATO_WF.hasAbstractionLevel,  EXATO_WF.Concrete))
        g.add((wf_uri, EXATO_WF.hasFlowType,          EXATO_WF.DataDriven))

    # ── Workflow-level inputs / outputs ─────────────────────────────────────

    def _add_workflow_inputs(self, cwl: dict, wf_uri: URIRef) -> dict[str, URIRef]:
        """
        Add top-level workflow input parameters.
        Returns {param_id: param_uri} for later data-link wiring.
        """
        wf_inputs: dict[str, URIRef] = {}
        inputs = cwl.get("inputs", {})
        if isinstance(inputs, list):
            inputs = {p["id"]: p for p in inputs}

        for param_id, param_def in inputs.items():
            if isinstance(param_def, str):
                param_def = {"type": param_def}
            param_slug = slugify(param_id)
            param_uri  = self.NS[f"wf_input_{param_slug}"]
            wf_inputs[param_id] = param_uri

            self.g.add((param_uri, RDF.type,   OWL.NamedIndividual))
            self.g.add((param_uri, RDF.type,   EXATO_WF_CWL.CWLInputParameter))
            self.g.add((param_uri, RDF.type,   EXATO_WF.InputParameter))
            self.g.add((param_uri, RDFS.label, Literal(param_def.get("label", param_id), lang="en")))
            self.g.add((param_uri, EXATO_WF.parameterName,
                        Literal(param_id, datatype=XSD.string)))
            self.g.add((param_uri, EXATO_WF_CWL.parameterID,
                        Literal(param_id, datatype=XSD.string)))

            cwl_type = param_def.get("type", "string")
            self.g.add((param_uri, EXATO_WF.parameterType,
                        Literal(str(cwl_type), datatype=XSD.string)))

            if "doc" in param_def:
                self.g.add((param_uri, RDFS.comment, Literal(param_def["doc"], lang="en")))

            # Link to workflow
            self.g.add((wf_uri, WFDESC.hasInput, param_uri))

        return wf_inputs

    def _add_workflow_outputs(self, cwl: dict, wf_uri: URIRef) -> dict[str, URIRef]:
        """
        Add top-level workflow output parameters.
        Returns {param_id: param_uri} for data-link wiring.
        """
        wf_outputs: dict[str, URIRef] = {}
        outputs = cwl.get("outputs", {})
        if isinstance(outputs, list):
            outputs = {p["id"]: p for p in outputs}

        for param_id, param_def in outputs.items():
            if isinstance(param_def, str):
                param_def = {"type": param_def}
            param_slug = slugify(param_id)
            param_uri  = self.NS[f"wf_output_{param_slug}"]
            wf_outputs[param_id] = param_uri

            self.g.add((param_uri, RDF.type,   OWL.NamedIndividual))
            self.g.add((param_uri, RDF.type,   EXATO_WF_CWL.CWLOutputParameter))
            self.g.add((param_uri, RDF.type,   EXATO_WF.OutputParameter))
            self.g.add((param_uri, RDFS.label, Literal(param_def.get("label", param_id), lang="en")))
            self.g.add((param_uri, EXATO_WF.parameterName,
                        Literal(param_id, datatype=XSD.string)))
            self.g.add((param_uri, EXATO_WF_CWL.parameterID,
                        Literal(param_id, datatype=XSD.string)))

            cwl_type = param_def.get("type", "string")
            self.g.add((param_uri, EXATO_WF.parameterType,
                        Literal(str(cwl_type), datatype=XSD.string)))

            if "doc" in param_def:
                self.g.add((param_uri, RDFS.comment, Literal(param_def["doc"], lang="en")))

            # Link to workflow
            self.g.add((wf_uri, WFDESC.hasOutput, param_uri))

        return wf_outputs

    # ── Steps ───────────────────────────────────────────────────────────────

    def _add_step(
        self,
        step_id: str,
        step_def: dict,
        wf_uri: URIRef,
        wf_inputs: dict[str, URIRef],
    ) -> tuple[URIRef, dict[str, URIRef], dict[str, URIRef]]:
        """
        Add a CWLWorkflowStep + its referenced CommandLineTool.
        Returns (step_uri, step_in_params, step_out_params).
        """
        g = self.g
        step_slug = slugify(step_id)
        step_uri  = self.NS[f"step_{step_slug}"]

        g.add((step_uri, RDF.type,   OWL.NamedIndividual))
        g.add((step_uri, RDF.type,   EXATO_WF_CWL.CWLWorkflowStep))
        g.add((step_uri, RDF.type,   EXATO_WF.WorkflowStep))

        label = step_def.get("label", step_id)
        g.add((step_uri, RDFS.label,           Literal(label, lang="en")))
        g.add((step_uri, EXATO_WF.stepName,    Literal(label, datatype=XSD.string)))
        g.add((step_uri, EXATO_WF_CWL.stepID,  Literal(step_id, datatype=XSD.string)))

        if "doc" in step_def:
            g.add((step_uri, EXATO_WF.stepDescription, Literal(step_def["doc"], datatype=XSD.string)))
            g.add((step_uri, RDFS.comment,              Literal(step_def["doc"], lang="en")))

        # Link step ↔ workflow
        g.add((wf_uri,   EXATO_WF.hasStep,        step_uri))
        g.add((step_uri, EXATO_WF.isPartOfWorkflow, wf_uri))

        # ── Resolve run target (tool) ────────────────────────────────────
        run_ref  = step_def.get("run")
        tool_cwl, tool_label = resolve_run(run_ref, self.base_dir)
        tool_uri = self.NS[f"tool_{step_slug}"]

        if tool_cwl:
            cwl_class = tool_cwl.get("class", "CommandLineTool")
            if cwl_class == "CommandLineTool":
                g.add((tool_uri, RDF.type, OWL.NamedIndividual))
                g.add((tool_uri, RDF.type, EXATO_WF_CWL.CWLCommandLineTool))
                g.add((tool_uri, RDF.type, EXATO_WF.WorkflowStep))
                g.add((tool_uri, RDFS.label,
                       Literal(tool_cwl.get("label", tool_label), lang="en")))
                if "doc" in tool_cwl:
                    g.add((tool_uri, RDFS.comment, Literal(tool_cwl["doc"], lang="en")))
                if "baseCommand" in tool_cwl:
                    bc = tool_cwl["baseCommand"]
                    g.add((tool_uri, EXATO_WF_CWL.baseCommand,
                           Literal(str(bc) if isinstance(bc, list) else bc,
                                   datatype=XSD.string)))
                    g.add((tool_uri, EXATO_WF.commandLine,
                           Literal(" ".join(bc) if isinstance(bc, list) else bc,
                                   datatype=XSD.string)))
                if "cwlVersion" in tool_cwl:
                    g.add((tool_uri, EXATO_WF_CWL.cwlVersion,
                           Literal(tool_cwl["cwlVersion"], datatype=XSD.string)))
                g.add((tool_uri, EXATO_WF_CWL.cwlClass,
                       Literal("CommandLineTool", datatype=XSD.string)))
            elif cwl_class == "ExpressionTool":
                g.add((tool_uri, RDF.type, OWL.NamedIndividual))
                g.add((tool_uri, RDF.type, EXATO_WF_CWL.CWLExpressionTool))
                if "expression" in tool_cwl:
                    g.add((tool_uri, EXATO_WF_CWL.expression,
                           Literal(tool_cwl["expression"], datatype=XSD.string)))
        else:
            # run: is just a string we can't resolve (remote URI etc.)
            g.add((tool_uri, RDF.type, OWL.NamedIndividual))
            g.add((tool_uri, RDF.type, EXATO_WF_CWL.CWLCommandLineTool))
            g.add((tool_uri, RDFS.label, Literal(str(run_ref), lang="en")))

        g.add((step_uri, EXATO_WF_CWL.runs, tool_uri))

        # ── Step input parameters ────────────────────────────────────────
        step_in_params: dict[str, URIRef] = {}
        step_ins = step_def.get("in", {})
        if isinstance(step_ins, list):
            step_ins = {p["id"]: p for p in step_ins}

        # Get tool input metadata for richer descriptions
        tool_input_meta: dict = {}
        if tool_cwl:
            raw = tool_cwl.get("inputs", {})
            if isinstance(raw, list):
                tool_input_meta = {p["id"]: p for p in raw}
            else:
                tool_input_meta = raw

        for in_id, in_def in step_ins.items():
            if isinstance(in_def, str):
                in_def = {"source": in_def}
            p_slug  = slugify(in_id)
            p_uri   = self.NS[f"step_{step_slug}_in_{p_slug}"]
            step_in_params[in_id] = p_uri

            g.add((p_uri, RDF.type,   OWL.NamedIndividual))
            g.add((p_uri, RDF.type,   EXATO_WF_CWL.CWLInputParameter))
            g.add((p_uri, RDF.type,   EXATO_WF.InputParameter))
            g.add((p_uri, RDFS.label, Literal(in_id, lang="en")))
            g.add((p_uri, EXATO_WF.parameterName,  Literal(in_id, datatype=XSD.string)))
            g.add((p_uri, EXATO_WF_CWL.parameterID, Literal(in_id, datatype=XSD.string)))

            # Enrich with tool metadata if available
            meta = tool_input_meta.get(in_id, {})
            if isinstance(meta, str):
                meta = {"type": meta}
            if "type" in meta:
                g.add((p_uri, EXATO_WF.parameterType,
                       Literal(str(meta["type"]), datatype=XSD.string)))
            if meta.get("doc"):
                g.add((p_uri, RDFS.comment, Literal(meta["doc"], lang="en")))

            # Link to step
            g.add((step_uri, EXATO_WF.hasInputParameter, p_uri))

        # ── Step output parameters ───────────────────────────────────────
        step_out_params: dict[str, URIRef] = {}
        step_outs = step_def.get("out", [])
        if isinstance(step_outs, list):
            # list of strings or list of dicts
            step_outs = {
                (o["id"] if isinstance(o, dict) else o): (o if isinstance(o, dict) else {})
                for o in step_outs
            }

        tool_output_meta: dict = {}
        if tool_cwl:
            raw = tool_cwl.get("outputs", {})
            if isinstance(raw, list):
                tool_output_meta = {p["id"]: p for p in raw}
            else:
                tool_output_meta = raw

        for out_id, out_def in step_outs.items():
            p_slug  = slugify(out_id)
            p_uri   = self.NS[f"step_{step_slug}_out_{p_slug}"]
            step_out_params[out_id] = p_uri

            g.add((p_uri, RDF.type,   OWL.NamedIndividual))
            g.add((p_uri, RDF.type,   EXATO_WF_CWL.CWLOutputParameter))
            g.add((p_uri, RDF.type,   EXATO_WF.OutputParameter))
            g.add((p_uri, RDFS.label, Literal(out_id, lang="en")))
            g.add((p_uri, EXATO_WF.parameterName,  Literal(out_id, datatype=XSD.string)))
            g.add((p_uri, EXATO_WF_CWL.parameterID, Literal(out_id, datatype=XSD.string)))

            meta = tool_output_meta.get(out_id, {})
            if isinstance(meta, str):
                meta = {"type": meta}
            if "type" in meta:
                g.add((p_uri, EXATO_WF.parameterType,
                       Literal(str(meta["type"]), datatype=XSD.string)))
            if meta.get("doc"):
                g.add((p_uri, RDFS.comment, Literal(meta["doc"], lang="en")))

            g.add((step_uri, EXATO_WF.hasOutputParameter, p_uri))

        return step_uri, step_in_params, step_out_params

    # ── Data links (wiring) ─────────────────────────────────────────────────

    def _wire_data_links(
        self,
        cwl: dict,
        step_registry: dict[str, tuple[URIRef, dict, dict]],
        wf_inputs: dict[str, URIRef],
        wf_outputs: dict[str, URIRef],
    ):
        """
        For every step input 'source:' field, create the data-link triples:
          - exato-wf-cwl:sourceFrom (step output → step input)
          - exato-wf-cwl:sourceWorkflowInput (wf input → step input)
          - exato-wf:dependsOn (step → step) — derived from above
          - exato-wf:connectsTo (output param → input param)
        Also wire workflow-level output 'outputSource:' fields.
        """
        g = self.g
        steps = cwl.get("steps", {})
        if isinstance(steps, list):
            steps = {s["id"]: s for s in steps}

        for step_id, step_def in steps.items():
            if step_id not in step_registry:
                continue
            step_uri, step_in_params, _ = step_registry[step_id]

            step_ins = step_def.get("in", {})
            if isinstance(step_ins, list):
                step_ins = {p["id"]: p for p in step_ins}

            for in_id, in_def in step_ins.items():
                if isinstance(in_def, str):
                    in_def = {"source": in_def}
                source = in_def.get("source")
                if not source:
                    continue

                in_param_uri = step_in_params.get(in_id)
                if not in_param_uri:
                    continue

                # source can be a string like "step_id/output_id" or just "wf_input_id"
                sources = source if isinstance(source, list) else [source]
                for src in sources:
                    if "/" in src:
                        # step_id/out_param_id
                        src_step_id, src_out_id = src.split("/", 1)
                        if src_step_id in step_registry:
                            src_step_uri, _, src_out_params = step_registry[src_step_id]
                            src_out_uri = src_out_params.get(src_out_id)
                            if src_out_uri:
                                # Data link: output param → input param
                                g.add((in_param_uri, EXATO_WF_CWL.sourceFrom, src_out_uri))
                                g.add((src_out_uri,  EXATO_WF.connectsTo,     in_param_uri))
                                # Step dependency
                                g.add((step_uri, EXATO_WF.dependsOn, src_step_uri))
                    else:
                        # Workflow-level input
                        wf_in_uri = wf_inputs.get(src)
                        if wf_in_uri:
                            g.add((in_param_uri, EXATO_WF_CWL.sourceWorkflowInput, wf_in_uri))

        # Wire workflow-level outputs
        outputs = cwl.get("outputs", {})
        if isinstance(outputs, list):
            outputs = {p["id"]: p for p in outputs}
        for out_id, out_def in outputs.items():
            if isinstance(out_def, str):
                continue
            out_source = out_def.get("outputSource")
            if not out_source:
                continue
            wf_out_uri = wf_outputs.get(out_id)
            if not wf_out_uri:
                continue
            sources = out_source if isinstance(out_source, list) else [out_source]
            for src in sources:
                if "/" in src:
                    src_step_id, src_out_id = src.split("/", 1)
                    if src_step_id in step_registry:
                        _, _, src_out_params = step_registry[src_step_id]
                        src_out_uri = src_out_params.get(src_out_id)
                        if src_out_uri:
                            g.add((src_out_uri, EXATO_WF.connectsTo, wf_out_uri))

    # ── Main entry point ────────────────────────────────────────────────────

    def convert(self) -> Graph:
        cwl     = load_cwl(self.cwl_path)
        wf_name = slugify(cwl.get("label") or self.cwl_path.stem)
        wf_uri  = self.NS[f"wf_{wf_name}"]

        # ── Ontology declaration with owl:imports ────────────────────────
        onto_uri = URIRef(str(self.NS).rstrip("#") + ".ttl")
        self.g.add((onto_uri, RDF.type, OWL.Ontology))
        #self.g.add((onto_uri, OWL.imports,
        #            URIRef("https://raw.githubusercontent.com/cnherrera/Exa-AToW_onto"
        #                   "/refs/heads/main/workflow_ontology/exato-wf-cwl-extension.ttl")))
        #self.g.add((onto_uri, OWL.imports,
        #            URIRef("https://w3id.org/Exa-AToW/exato-wf.ttl")))

        self._add_workflow(cwl, wf_uri)
        wf_inputs  = self._add_workflow_inputs(cwl, wf_uri)
        wf_outputs = self._add_workflow_outputs(cwl, wf_uri)

        # Process steps
        step_registry: dict[str, tuple[URIRef, dict, dict]] = {}
        steps = cwl.get("steps", {})
        if isinstance(steps, list):
            steps = {s["id"]: s for s in steps}

        for step_id, step_def in steps.items():
            step_uri, in_params, out_params = self._add_step(
                step_id, step_def, wf_uri, wf_inputs
            )
            step_registry[step_id] = (step_uri, in_params, out_params)

        # Wire data links
        self._wire_data_links(cwl, step_registry, wf_inputs, wf_outputs)

        return self.g


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert a CWL workflow to an OWL/Turtle instance (exato-wf + exato-wf-cwl)"
    )
    parser.add_argument("cwl_file",  help="Path to the CWL Workflow file (.cwl or .yaml)")
    parser.add_argument("-o", "--output", default=None,
                        help="Output TTL file path (default: <cwl_stem>_instance.ttl)")
    parser.add_argument("--base", default=None,
                        help="Base namespace URI for instances "
                             "(default: http://example.org/<cwl_stem>#)")
    args = parser.parse_args()

    cwl_path = Path(args.cwl_file)
    if not cwl_path.exists():
        print(f"Error: {cwl_path} not found", file=sys.stderr)
        sys.exit(1)

    stem     = slugify(cwl_path.stem)
    base_ns  = args.base or f"http://example.org/{stem}#"
    out_path = Path(args.output) if args.output else cwl_path.parent / f"{stem}_instance.ttl"

    print(f"Reading  : {cwl_path}")
    print(f"Base NS  : {base_ns}")
    print(f"Output   : {out_path}")

    converter = CWLToTTL(cwl_path, base_ns)
    g = converter.convert()

    ttl_str = g.serialize(format="turtle")
    # Ensure @prefix rdf: is always present (rdflib may omit it if not used as prefix)
    if "@prefix rdf:" not in ttl_str:
        ttl_str = "@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n" + ttl_str
    with open(str(out_path), "w", encoding="utf-8") as f_out:
        f_out.write(ttl_str)
    print(f"Done — {len(g)} triples written to {out_path}")


if __name__ == "__main__":
    main()
