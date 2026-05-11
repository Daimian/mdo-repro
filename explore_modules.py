import rdflib
from rdflib.namespace import RDF, RDFS, OWL

modules = {
    'core':       'mdo/mdo-core.owl',
    'structure':  'mdo/mdo-structure.owl',
    'calculation':'mdo/mdo-calculation.owl',
    'provenance': 'mdo/mdo-provenance.owl',
}

for name, path in modules.items():
    g = rdflib.Graph()
    g.parse(path)

    print(f"\n===== {name.upper()} =====")
    print(f"Triples: {len(g)}")

    imports = list(g.objects(None, OWL.imports))
    print(f"Imports: {[str(i) for i in imports]}")

    classes = list(g.subjects(RDF.type, OWL.Class))
    classes = [c for c in classes if isinstance(c, rdflib.URIRef)]
    print(f"Named classes: {len(classes)}")

    obj_props = list(g.subjects(RDF.type, OWL.ObjectProperty))
    print(f"Object properties: {len(obj_props)}")

    print("\nFirst 5 classes (with parent):")
    for c in sorted(classes)[:5]:
        c_short = str(c).rsplit('/', 1)[-1]
        parents = list(g.objects(c, RDFS.subClassOf))
        p_strs = [str(p).rsplit('/', 1)[-1] for p in parents if isinstance(p, rdflib.URIRef)]
        print(f"  {c_short:35s} <- {', '.join(p_strs) or 'owl:Thing'}")
