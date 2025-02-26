#!/usr/bin/env python3

import argparse
import csv
import logging
import os.path
import sys
from collections import Counter
from dataclasses import dataclass, field
from itertools import count
from typing import Generator, List, Literal, Union  # noqa

from pyhornedowl import open_ontology_from_file
from pyhornedowl.model import *


def to_ms(value: Union[
    ClassExpression, ObjectPropertyExpression, DataProperty, AnnotationProperty, Component, Variable, Atom]) -> str:

    if any(isinstance(value, t) for t in [ObjectProperty, DataProperty, AnnotationProperty, Class, Variable]):
        return str(value.first)

    if isinstance(value, InverseObjectProperty):
        return f"not {to_ms(value.first)}"


    # Class expressions
    if isinstance(value, ObjectIntersectionOf):
        return f"({' and '.join(to_ms(v) for v in value.first)})"
    if isinstance(value, ObjectUnionOf):
        return f"({' or '.join(to_ms(v) for v in value.first)})"
    if isinstance(value, ObjectComplementOf):
        return f"not ({to_ms(value.first)})"
    if isinstance(value, ObjectSomeValuesFrom):
        return f"({to_ms(value.ope)} some {to_ms(value.bce)})"
    if isinstance(value, ObjectAllValuesFrom):
        return f"({to_ms(value.ope)} only {to_ms(value.bce)})"
    if isinstance(value, ObjectHasSelf):
        return f"({to_ms(value.first)} Self)"
    if isinstance(value, ObjectMinCardinality):
        return f"({to_ms(value.ope)} min {value.n} {to_ms(value.bce)})"
    if isinstance(value, ObjectMaxCardinality):
        return f"({to_ms(value.ope)} max {value.n} {to_ms(value.bce)})"
    if isinstance(value, ObjectExactCardinality):
        return f"({to_ms(value.ope)} exactly {value.n} {to_ms(value.bce)})"
    if isinstance(value, DataSomeValuesFrom):
        return f"({value.dp} some {value.dr})"
    if isinstance(value, DataAllValuesFrom):
        return f"({value.dp} only {value.dr})"
    if isinstance(value, DataMinCardinality):
        return f"({value.dp} min {value.n} {value.dr})"
    if isinstance(value, DataMaxCardinality):
        return f"({value.dp} max {value.n} {value.dr})"
    if isinstance(value, DataExactCardinality):
        return f"({value.dp} exactly {value.n} {value.dr})"
    if isinstance(value, DataHasValue):
        return f"({value.dp} value {value.l})"


    # Rule atoms
    if isinstance(value, BuiltInAtom):
        return f"{value.pred}({', '.join(to_ms(v) for v in value.args)})"
    if isinstance(value, ClassAtom):
        return f"{to_ms(value.pred)}({to_ms(value.arg)})"
    if isinstance(value, DataPropertyAtom):
        return f"{value.pred}({', '.join(to_ms(v) for v in value.args)})"
    if isinstance(value, DifferentIndividualsAtom):
        return f"DifferentIndividuals({to_ms(value.first)}, {to_ms(value.second)})"
    if isinstance(value, ObjectPropertyAtom):
        return f"{value.pred}({', '.join(to_ms(v) for v in value.args)})"
    if isinstance(value, SameIndividualAtom):
        return f"SameIndividual({to_ms(value.first)}, {to_ms(value.second)})"

    # Components
    if isinstance(value, SubClassOf):
        return f"Class: {to_ms(value.sub)} SubClassOf: {to_ms(value.sup)}"
    if isinstance(value, EquivalentClasses):
        return f"EquivalentClasses: {', '.join(to_ms(v) for v in value.first)}"
    if isinstance(value, DisjointClasses):
        return f"DisjointClasses: {', '.join(to_ms(v) for v in value.first)}"
    if isinstance(value, DisjointUnion):
        return f"Class: {to_ms(value.first)} DisjointUnionOf: {', '.join(to_ms(v) for v in value.second)}"
    if isinstance(value, SubObjectPropertyOf):
        if isinstance(value.sub, ObjectPropertyExpression):
            return f"ObjectProperty: {to_ms(value.sub)} SubPropertyOf: {to_ms(value.sup)}"
        else:
            return f"ObjectProperty: {to_ms(value.sup)} SubPropertyChain: {' o '.join(to_ms(v) for v in value.sub)}"
    if isinstance(value, EquivalentObjectProperties):
        return f"EquivalentProperties: {', '.join(to_ms(v) for v in value.first)}"
    if isinstance(value, DisjointObjectProperties):
        return f"DisjointProperties: {', '.join(to_ms(v) for v in value.first)}"
    if isinstance(value, InverseObjectProperties):
        return f"ObjectProperty: {to_ms(value.first)} InverseOf: {to_ms(value.second)}"
    if isinstance(value, ObjectPropertyDomain):
        return f"ObjectProperty: {to_ms(value.ope)} Domain: {to_ms(value.ce)}"
    if isinstance(value, ObjectPropertyRange):
        return f"ObjectProperty: {to_ms(value.ope)} Range: {to_ms(value.ce)}"
    if isinstance(value, FunctionalObjectProperty):
        return f"ObjectProperty: {to_ms(value.first)} Characteristics: Functional"
    if isinstance(value, InverseFunctionalObjectProperty):
        return f"ObjectProperty: {to_ms(value.first)} Characteristics: InverseFunctional"
    if isinstance(value, ReflexiveObjectProperty):
        return f"ObjectProperty: {to_ms(value.first)} Characteristics: Reflexive"
    if isinstance(value, IrreflexiveObjectProperty):
        return f"ObjectProperty: {to_ms(value.first)} Characteristics: Irreflexive"
    if isinstance(value, SymmetricObjectProperty):
        return f"ObjectProperty: {to_ms(value.first)} Characteristics: Symmetric"
    if isinstance(value, AsymmetricObjectProperty):
        return f"ObjectProperty: {to_ms(value.first)} Characteristics: Asymmetric"
    if isinstance(value, TransitiveObjectProperty):
        return f"ObjectProperty: {to_ms(value.first)} Characteristics: Transitive"
    if isinstance(value, SubDataPropertyOf):
        return f"DataProperty: {to_ms(value.sub)} SubPropertyOf: {to_ms(value.sup)}"
    if isinstance(value, EquivalentDataProperties):
        return f"EquivalentProperties: {', '.join(to_ms(v) for v in value.first)}"
    if isinstance(value, DisjointDataProperties):
        return f"DisjointProperties: {', '.join(to_ms(v) for v in value.first)}"
    if isinstance(value, DataPropertyDomain):
        return f"DataProperty: {to_ms(value.dp)} Domain: {to_ms(value.ce)}"
    if isinstance(value, DataPropertyRange):
        return f"DataProperty: {to_ms(value.dp)} Range: {value.dr}"
    if isinstance(value, FunctionalDataProperty):
        return f"DataProperty: {to_ms(value.first)} Characteristics: Functional"
    if isinstance(value, HasKey):
        return f"Class: {to_ms(value.ce)} HasKey: {', '.join(to_ms(v) for v in value.vpe)}"
    if isinstance(value, SubAnnotationPropertyOf):
        return f"AnnotationProperty: {to_ms(value.sub)} SubPropertyOf: {to_ms(value.sup)}"
    if isinstance(value, AnnotationPropertyDomain):
        return f"AnnotationProperty: {to_ms(value.ap)} Domain: {value.iri}"
    if isinstance(value, AnnotationPropertyRange):
        return f"AnnotationProperty: {to_ms(value.ap)} Range: {value.iri}"
    if isinstance(value, Rule):
        return f"Rule: {' and '.join(to_ms(v) for v in value.head)} -> {' and '.join(to_ms(v) for v in value.body)}"

    logging.error(f"Unknown component: {value}")
    return str(value)





def ignore(value: Union[Individual, ClassExpression, Component, Atom]) -> bool:
    # Individuals
    if isinstance(value, Individual):
        return True

    # Class expressions
    if isinstance(value, ObjectIntersectionOf):
        return any(ignore(a) for a in value.first)
    if isinstance(value, ObjectUnionOf):
        return any(ignore(a) for a in value.first)
    if isinstance(value, ObjectComplementOf):
        return ignore(value.first)
    if isinstance(value, ObjectOneOf):
        return True
    if isinstance(value, ObjectSomeValuesFrom):
        return ignore(value.bce)
    if isinstance(value, ObjectAllValuesFrom):
        return ignore(value.bce)
    if isinstance(value, ObjectHasValue):
        return True
    if isinstance(value, ObjectMinCardinality):
        return ignore(value.bce)
    if isinstance(value, ObjectMaxCardinality):
        return ignore(value.bce)
    if isinstance(value, ObjectExactCardinality):
        return ignore(value.bce)

    # Rule atoms
    if isinstance(value, ClassAtom):
        return ignore(value.pred) or ignore(value.arg)
    if isinstance(value, DifferentIndividualsAtom):
        return ignore(value.first) or ignore(value.second)
    if isinstance(value, SameIndividualAtom):
        return ignore(value.first) or ignore(value.second)
    if isinstance(value, ObjectPropertyAtom):
        return any(ignore(a) for a in value.args)

    # Components start
    if isinstance(value, OntologyID):
        return True
    if isinstance(value, DocIRI):
        return True
    if isinstance(value, OntologyAnnotation):
        return True
    if isinstance(value, Import):
        return True
    if isinstance(value, DeclareClass):
        return True
    if isinstance(value, DeclareObjectProperty):
        return True
    if isinstance(value, DeclareAnnotationProperty):
        return True
    if isinstance(value, DeclareDataProperty):
        return True
    if isinstance(value, DeclareNamedIndividual):
        return True
    if isinstance(value, DeclareDatatype):
        return True
    if isinstance(value, SubClassOf):
        return ignore(value.sub) or ignore(value.sup)
    if isinstance(value, EquivalentClasses):
        return any(ignore(a) for a in value.first)
    if isinstance(value, DisjointClasses):
        return any(ignore(a) for a in value.first)
    if isinstance(value, DisjointUnion):
        return any(ignore(a) for a in value.second)
    if isinstance(value, ObjectPropertyDomain):
        return ignore(value.ce)
    if isinstance(value, ObjectPropertyRange):
        return ignore(value.ce)
    if isinstance(value, HasKey):
        return ignore(value.ce)
    if isinstance(value, SameIndividual):
        return True
    if isinstance(value, DifferentIndividuals):
        return True
    if isinstance(value, ClassAssertion):
        return True
    if isinstance(value, ObjectPropertyAssertion):
        return True
    if isinstance(value, NegativeObjectPropertyAssertion):
        return True
    if isinstance(value, DataPropertyAssertion):
        return True
    if isinstance(value, NegativeDataPropertyAssertion):
        return True
    if isinstance(value, AnnotationAssertion):
        # Ignore annotations
        return True
        # return ignore(value.subject)
    if isinstance(value, Rule):
        return any(ignore(a) for a in value.head + value.body)

    return False


def _index_to_str(index: int, choices: list[chr]) -> str:
    length = len(choices)
    res = ""
    while index >= 0:
        res = choices[index % length] + res
        index = index // length - 1
    return res


def class_generator():
    return (_index_to_str(i, [chr(c) for c in range(ord("A"), ord("O"))]) for i in count())
    # return (f"C{i}" for i in count())


def property_generator():
    return (_index_to_str(i, ["R", "S", "T", "U", "V", "W", "P", "Q"]) for i in count())
    # return (f"R{i}" for i in count())


def var_generator():
    return (f"X{i}" for i in count())


@dataclass
class Context:
    substitutions: dict[str, str] = field(default_factory=dict)
    properties: Generator[str, None, None] = field(default_factory=property_generator)
    classes: Generator[str, None, None] = field(default_factory=class_generator)
    variables: Generator[str, None, None] = field(default_factory=var_generator)


def sub[T: Union[Class, ObjectProperty, DataProperty, AnnotationProperty, Variable]](value: T,
                                                                                     ctx: Context) -> T:
    iri = str(value.first)

    sub = ctx.substitutions.get(iri, None)
    if sub is None:
        if isinstance(value, Class):
            sub = next(ctx.classes)
        if isinstance(value, ObjectProperty | DataProperty | AnnotationProperty):
            sub = next(ctx.properties)
        if isinstance(value, Variable):
            sub = next(ctx.variables)

        sub = IRI.parse(sub)
        ctx.substitutions[iri] = sub

    return type(value)(sub)


def normalise[T: Union[
    ClassExpression, ObjectPropertyExpression, DataProperty, AnnotationProperty, Component, Variable, Atom]](
        value: T,
        ctx: Context) -> T:
    if any(isinstance(value, t) for t in [ObjectProperty, DataProperty, AnnotationProperty, Class, Variable]):
        return sub(value, ctx)

    # ObjectProperty expressions
    if isinstance(value, InverseObjectProperty):
        return InverseObjectProperty(normalise(value.first, ctx))

    # Class expressions
    if isinstance(value, ObjectIntersectionOf):
        return ObjectIntersectionOf([normalise(v, ctx) for v in value.first])
    if isinstance(value, ObjectUnionOf):
        return ObjectUnionOf([normalise(v, ctx) for v in value.first])
    if isinstance(value, ObjectComplementOf):
        return ObjectComplementOf(normalise(value.first, ctx))
    if isinstance(value, ObjectSomeValuesFrom):
        return ObjectSomeValuesFrom(normalise(value.ope, ctx), normalise(value.bce, ctx))
    if isinstance(value, ObjectAllValuesFrom):
        return ObjectAllValuesFrom(normalise(value.ope, ctx), normalise(value.bce, ctx))
    if isinstance(value, ObjectHasSelf):
        return ObjectHasSelf(normalise(value.first, ctx))
    if isinstance(value, ObjectMinCardinality):
        return ObjectMinCardinality(value.n, normalise(value.ope, ctx), normalise(value.bce, ctx))
    if isinstance(value, ObjectMaxCardinality):
        return ObjectMaxCardinality(value.n, normalise(value.ope, ctx), normalise(value.bce, ctx))
    if isinstance(value, ObjectExactCardinality):
        return ObjectExactCardinality(value.n, normalise(value.ope, ctx), normalise(value.bce, ctx))
    if isinstance(value, DataSomeValuesFrom):
        return DataSomeValuesFrom(normalise(value.dp, ctx), value.dr)
    if isinstance(value, DataAllValuesFrom):
        return DataAllValuesFrom(normalise(value.dp, ctx), value.dr)
    if isinstance(value, DataMinCardinality):
        return DataMinCardinality(value.n, normalise(value.dp, ctx), value.dr)
    if isinstance(value, DataMaxCardinality):
        return DataMaxCardinality(value.n, normalise(value.dp, ctx), value.dr)
    if isinstance(value, DataExactCardinality, ):
        return DataExactCardinality(value.n, normalise(value.dp, ctx), value.dr)

    # Rule atoms
    if isinstance(value, BuiltInAtom):
        return BuiltInAtom(value.pred, [normalise(v, ctx) for v in value.args])
    if isinstance(value, ClassAtom):
        return ClassAtom(normalise(value.pred, ctx), normalise(value.arg, ctx))
    if isinstance(value, DataPropertyAtom):
        a, b = value.args
        return DataPropertyAtom(normalise(value.pred, ctx), (normalise(a, ctx), normalise(b, ctx)))
    if isinstance(value, DifferentIndividualsAtom):
        return DifferentIndividualsAtom(normalise(value.first, ctx), normalise(value.second, ctx))
    if isinstance(value, ObjectPropertyAtom):
        a, b = value.args
        return ObjectPropertyAtom(normalise(value.pred, ctx), (normalise(a, ctx), normalise(b, ctx)))
    if isinstance(value, SameIndividualAtom):
        return SameIndividualAtom(normalise(value.first, ctx), normalise(value.second, ctx))

    # Components
    if isinstance(value, SubClassOf):
        return SubClassOf(normalise(value.sub, ctx), normalise(value.sup, ctx))
    if isinstance(value, EquivalentClasses):
        return EquivalentClasses([normalise(v, ctx) for v in value.first])
    if isinstance(value, DisjointClasses):
        return DisjointClasses([normalise(v, ctx) for v in value.first])
    if isinstance(value, DisjointUnion):
        return DisjointUnion(sub(value.first, ctx), [normalise(v, ctx) for v in value.second])
    if isinstance(value, SubObjectPropertyOf):
        if isinstance(value.sub, ObjectPropertyExpression):
            return SubObjectPropertyOf(normalise(value.sub, ctx), normalise(value.sup, ctx))
        else:
            return SubObjectPropertyOf([normalise(v, ctx) for v in value.sub], normalise(value.sup, ctx))
    if isinstance(value, EquivalentObjectProperties):
        return EquivalentObjectProperties([normalise(v, ctx) for v in value.first])
    if isinstance(value, DisjointObjectProperties):
        return DisjointObjectProperties([normalise(v, ctx) for v in value.first])
    if isinstance(value, InverseObjectProperties):
        return InverseObjectProperties(normalise(value.first, ctx), normalise(value.second, ctx))
    if isinstance(value, ObjectPropertyDomain):
        return ObjectPropertyDomain(normalise(value.ope, ctx), normalise(value.ce, ctx))
    if isinstance(value, ObjectPropertyRange):
        return ObjectPropertyDomain(normalise(value.ope, ctx), normalise(value.ce, ctx))
    if isinstance(value, FunctionalObjectProperty):
        return FunctionalObjectProperty(normalise(value.first, ctx))
    if isinstance(value, InverseFunctionalObjectProperty):
        return InverseFunctionalObjectProperty(normalise(value.first, ctx))
    if isinstance(value, ReflexiveObjectProperty):
        return ReflexiveObjectProperty(normalise(value.first, ctx))
    if isinstance(value, IrreflexiveObjectProperty):
        return IrreflexiveObjectProperty(normalise(value.first, ctx))
    if isinstance(value, SymmetricObjectProperty):
        return SymmetricObjectProperty(normalise(value.first, ctx))
    if isinstance(value, AsymmetricObjectProperty):
        return AsymmetricObjectProperty(normalise(value.first, ctx))
    if isinstance(value, TransitiveObjectProperty):
        return TransitiveObjectProperty(normalise(value.first, ctx))
    if isinstance(value, SubDataPropertyOf):
        return SubDataPropertyOf(normalise(value.sub, ctx), normalise(value.sup, ctx))
    if isinstance(value, EquivalentDataProperties):
        return EquivalentDataProperties([normalise(v, ctx) for v in value.first])
    if isinstance(value, DisjointDataProperties):
        return DisjointDataProperties([normalise(v, ctx) for v in value.first])
    if isinstance(value, DataPropertyDomain):
        return DataPropertyDomain(normalise(value.dp, ctx), normalise(value.ce, ctx))
    if isinstance(value, DataPropertyRange):
        return DataPropertyRange(normalise(value.dp, ctx), value.dr)
    if isinstance(value, FunctionalDataProperty):
        return FunctionalDataProperty(normalise(value.first, ctx))
    if isinstance(value, HasKey):
        return HasKey(normalise(value.ce, ctx), [normalise(v, ctx) for v in value.vpe])
    if isinstance(value, SubAnnotationPropertyOf):
        return SubAnnotationPropertyOf(normalise(value.sub, ctx), normalise(value.sup, ctx))
    if isinstance(value, AnnotationPropertyDomain):
        return AnnotationPropertyDomain(normalise(value.ap, ctx), value.iri)
    if isinstance(value, AnnotationPropertyRange):
        return AnnotationPropertyRange(normalise(value.ap, ctx), value.iri)
    if isinstance(value, Rule):
        return Rule([normalise(v, ctx) for v in value.head], [normalise(v, ctx) for v in value.body])

    return value


def analyse_file(file: str) -> Counter[Component]:
    try:
        ontology = open_ontology_from_file(file)
    except Exception as e:
        logging.error(f"Failed to open ontology file {file}: {e}")
        return Counter()

    normalised_axioms: List[Component] = []
    for annotated_axiom in ontology.get_axioms():
        # Ignore annotations
        axiom = annotated_axiom.component
        if ignore(axiom):
            continue

        normalised = normalise(axiom, Context())
        normalised_axioms.append(normalised)

    return Counter(normalised_axioms)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", help="OWL input file or directory of OWL input files", nargs="+",
                        required=True)
    parser.add_argument("--output", "-o", help="CSV output file (defaults to stdout)", default=None)
    parser.add_argument("--output-mode", "-m", help="In case of multiple input files what should be the output",
                        choices=["aggregate", "individual"], default="aggregate")

    args = parser.parse_args()

    inputs = args.input
    output = args.output
    output_mode: Literal["aggregate", "individual"] = args.output_mode

    with (open(output, "w") if output is not None else sys.stdout) as f:
        writer = csv.writer(f)
        writer.writerow(["File", "Pattern", "Count"])

        aggregate: Counter[Component] = Counter()
        for input in inputs:
            if os.path.isdir(input):
                for filename in os.listdir(input):
                    if not any(filename.endswith(ext) for ext in [".owl", ".rdf", ".owx", ".omn", "ofn"]):
                        continue

                    file_path = os.path.join(input, filename)

                    # Prefer xml over other formats
                    owx_path = file_path[:file_path.rindex(".")] + ".owx"
                    if file_path != owx_path and os.path.exists(owx_path):
                        continue

                    result = analyse_file(file_path)
                    if output_mode == "aggregate":
                        aggregate += result
                    else:
                        _save_result(filename, result, writer)
            else:
                result = analyse_file(input)
                if output_mode == "aggregate":
                    aggregate += result
                else:
                    _save_result(input, result, writer)

        if output_mode == "aggregate":
            _save_result(input if len(inputs) == 1 else "", aggregate, writer)


def _save_result(filename, r, writer):
    for k, v in sorted(r.items(), key=lambda x: x[1], reverse=True):
        writer.writerow([filename, to_ms(k), v])


if __name__ == "__main__":
    main()
