import rdflib
from rdflib.namespace import RDF, RDFS, OWL
import graphviz

g = rdflib.Graph()
for f in ['mdo-core.owl', 'mdo-structure.owl',
          'mdo-calculation.owl', 'mdo-provenance.owl']:
    g.parse(f'mdo/{f}')

def short(uri):
    s = str(uri)
    for prefix, ns in [
        ('core:', 'https://w3id.org/mdo/core/'),
        ('structure:', 'https://w3id.org/mdo/structure/'),
        ('calculation:', 'https://w3id.org/mdo/calculation/'),
        ('provenance:', 'https://w3id.org/mdo/provenance/'),
        ('prov:', 'http://www.w3.org/ns/prov#'),
        ('qudt:', 'http://qudt.org/schema/qudt/'),
        ('owl:', 'http://www.w3.org/2002/07/owl#'),
        ('emmo:', 'http://emmo.info/domains/emmo-material.owl#'),
        ('chebi:', 'http://purl.obolibrary.org/obo/'),
    ]:
        if s.startswith(ns):
            return prefix + s[len(ns):]
    return s.rsplit('/', 1)[-1].rsplit('#', 1)[-1]

def nid(uri):
    return str(uri).replace(':', '_').replace('/', '_').replace('#', '_').replace('.', '_')

def get_module(uri):
    s = str(uri)
    if '/core/' in s: return 'core'
    if '/structure/' in s: return 'structure'
    if '/calculation/' in s: return 'calculation'
    if '/provenance/' in s: return 'provenance'
    if 'prov#' in s: return 'prov'
    if 'qudt' in s: return 'qudt'
    return 'other'

FILL = {'core':'#D6EAF8','structure':'#D5F5E3','calculation':'#FDEBD0',
        'provenance':'#E8DAEF','prov':'#F5EEF8','qudt':'#EAECEE','other':'#F2F3F4'}
BORDER = {'core':'#4A90D9','structure':'#50C878','calculation':'#FF8C42',
          'provenance':'#9B59B6','prov':'#C39BD3','qudt':'#85929E','other':'#BDC3C7'}

all_classes = {c for c in g.subjects(RDF.type, OWL.Class) if isinstance(c, rdflib.URIRef)}
obj_props = {p for p in g.subjects(RDF.type, OWL.ObjectProperty) if isinstance(p, rdflib.URIRef)}
data_props = {p for p in g.subjects(RDF.type, OWL.DatatypeProperty) if isinstance(p, rdflib.URIRef)}

class_dps = {}
for dp in data_props:
    for dom in g.objects(dp, RDFS.domain):
        if isinstance(dom, rdflib.URIRef):
            class_dps.setdefault(dom, []).append(short(dp))

def add_class_node(dot, c, use_record=False):
    mod = get_module(c)
    label = short(c)
    if use_record:
        dps = class_dps.get(c, [])
        if dps:
            dp_str = '\\l'.join(sorted(dps)) + '\\l'
            label = f'{{{label}|{dp_str}}}'
        else:
            label = f'{{{label}}}'
    dot.node(nid(c), label=label, fillcolor=FILL.get(mod,'#F2F3F4'),
             color=BORDER.get(mod,'#BDC3C7'), penwidth='2')

# ============================================================
# FIGURE 1: Class Hierarchy
# ============================================================
d1 = graphviz.Digraph('class_hierarchy', format='png')
d1.attr(rankdir='BT', label='MDO Class Hierarchy', fontsize='18',
        labelloc='t', fontname='Helvetica', bgcolor='white', nodesep='0.4', ranksep='0.6',
        dpi='300')
d1.attr('node', shape='box', style='filled,rounded', fontname='Helvetica', fontsize='11')
d1.attr('edge', arrowhead='empty', color='#555555')

for c in all_classes:
    add_class_node(d1, c)
for c in all_classes:
    for p in g.objects(c, RDFS.subClassOf):
        if isinstance(p, rdflib.URIRef) and p in all_classes:
            d1.edge(nid(c), nid(p))

with d1.subgraph(name='cluster_legend') as leg:
    leg.attr(label='Modules', style='dashed', color='gray', fontsize='12')
    for m, fc in [('core','#D6EAF8'),('structure','#D5F5E3'),
                  ('calculation','#FDEBD0'),('provenance','#E8DAEF'),
                  ('external','#EAECEE')]:
        leg.node(f'leg_{m}', label=m, fillcolor=fc, shape='box',
                 style='filled,rounded', fontsize='9')

d1.render('mdo_class_hierarchy', cleanup=True)
print('1/7 mdo_class_hierarchy.png')

# ============================================================
# FIGURE 2: Object Property Map
# ============================================================
d2 = graphviz.Digraph('property_map', format='png')
d2.attr(rankdir='LR', label='MDO Object Properties (Domain -> Range)',
        fontsize='18', labelloc='t', fontname='Helvetica', bgcolor='white',
        nodesep='0.3', ranksep='1.0', dpi='300')
d2.attr('node', shape='box', style='filled,rounded', fontname='Helvetica', fontsize='11')

added = set()
for prop in obj_props:
    domains = [d for d in g.objects(prop, RDFS.domain) if isinstance(d, rdflib.URIRef)]
    ranges = [r for r in g.objects(prop, RDFS.range) if isinstance(r, rdflib.URIRef)]
    for d in domains:
        if nid(d) not in added:
            mod = get_module(d)
            d2.node(nid(d), label=short(d), fillcolor=FILL.get(mod,'#F2F3F4'),
                    color=BORDER.get(mod,'#BDC3C7'), penwidth='2')
            added.add(nid(d))
        for r in ranges:
            if nid(r) not in added:
                mod = get_module(r)
                d2.node(nid(r), label=short(r), fillcolor=FILL.get(mod,'#F2F3F4'),
                        color=BORDER.get(mod,'#BDC3C7'), penwidth='2')
                added.add(nid(r))
            mp = get_module(prop)
            d2.edge(nid(d), nid(r), label=short(prop), fontsize='9',
                    color=BORDER.get(mp,'#888'), fontcolor=BORDER.get(mp,'#888'))

d2.render('mdo_property_map', cleanup=True)
print('2/7 mdo_property_map.png')

# ============================================================
# FIGURE 3: Full OntoGraf-style
# ============================================================
d3 = graphviz.Digraph('ontograf', format='png')
d3.attr(rankdir='TB', label='MDO Full Ontology Graph', fontsize='28',
        labelloc='t', fontname='Helvetica-Bold', bgcolor='white',
        nodesep='0.4', ranksep='0.8', dpi='300', pad='0.5',
        ratio='0.75', size='20,16!')
d3.attr('node', shape='record', style='filled', fontname='Helvetica', fontsize='14',
        margin='0.2,0.1')
d3.attr('edge', penwidth='1.2')

# Group classes by module in clusters for better layout
module_classes_3 = {}
for c in all_classes:
    module_classes_3.setdefault(get_module(c), []).append(c)

MODULE_LABELS_3 = {'core': 'mdo-core', 'structure': 'mdo-structure',
                   'calculation': 'mdo-calculation', 'provenance': 'mdo-provenance',
                   'prov': 'W3C PROV-O', 'qudt': 'QUDT'}

for mod in ['core', 'structure', 'calculation', 'provenance', 'prov', 'qudt']:
    classes = module_classes_3.get(mod, [])
    if not classes:
        continue
    with d3.subgraph(name=f'cluster_onto_{mod}') as sg:
        sg.attr(label=MODULE_LABELS_3.get(mod, mod),
                style='rounded,filled',
                color=BORDER.get(mod, '#AAA'),
                fillcolor=FILL.get(mod, '#F8F8F8') + '30',
                fontname='Helvetica-Bold', fontsize='16',
                fontcolor=BORDER.get(mod, '#AAA'))
        for c in sorted(classes, key=lambda x: short(x)):
            mod_c = get_module(c)
            label = short(c)
            dps = class_dps.get(c, [])
            if dps:
                dp_str = '\\l'.join(sorted(dps)) + '\\l'
                label = f'{{{label}|{dp_str}}}'
            else:
                label = f'{{{label}}}'
            sg.node(nid(c), label=label,
                    fillcolor=FILL.get(mod_c, '#F2F3F4'),
                    color=BORDER.get(mod_c, '#AAA'), penwidth='2')

for c in all_classes:
    for p in g.objects(c, RDFS.subClassOf):
        if isinstance(p, rdflib.URIRef) and p in all_classes:
            d3.edge(nid(c), nid(p), arrowhead='empty', color='#333', penwidth='2.0')
for prop in obj_props:
    domains = [d for d in g.objects(prop, RDFS.domain) if isinstance(d, rdflib.URIRef)]
    ranges = [r for r in g.objects(prop, RDFS.range) if isinstance(r, rdflib.URIRef)]
    for d in domains:
        for r in ranges:
            mp = get_module(prop)
            d3.edge(nid(d), nid(r), label=short(prop), fontsize='11',
                    fontname='Helvetica',
                    color=BORDER.get(mp,'#888'), fontcolor=BORDER.get(mp,'#888'),
                    style='dashed', arrowhead='vee', penwidth='1.5')

d3.render('mdo_ontograf', cleanup=True)
print('3/7 mdo_ontograf.png')

# ============================================================
# FIGURES 4-7: Per-module diagrams
# ============================================================
for mod_name, mod_file in [('core','mdo/mdo-core.owl'),('structure','mdo/mdo-structure.owl'),
                            ('calculation','mdo/mdo-calculation.owl'),('provenance','mdo/mdo-provenance.owl')]:
    mg = rdflib.Graph()
    mg.parse(mod_file)

    dot = graphviz.Digraph(f'module_{mod_name}', format='png')
    dot.attr(rankdir='TB', label=f'MDO Module: {mod_name}', fontsize='16',
             labelloc='t', fontname='Helvetica', bgcolor='white', dpi='300')
    dot.attr('node', shape='record', style='filled', fontname='Helvetica', fontsize='10',
             fillcolor=FILL.get(mod_name,'#F2F3F4'),
             color=BORDER.get(mod_name,'#BDC3C7'), penwidth='2')

    mc = {c for c in mg.subjects(RDF.type, OWL.Class) if isinstance(c, rdflib.URIRef)}

    mdp = {}
    for dp in mg.subjects(RDF.type, OWL.DatatypeProperty):
        if isinstance(dp, rdflib.URIRef):
            for dom in mg.objects(dp, RDFS.domain):
                if isinstance(dom, rdflib.URIRef):
                    mdp.setdefault(dom, []).append(short(dp))

    ext_added = set()
    for c in mc:
        label = short(c)
        dps = mdp.get(c, [])
        if dps:
            dp_str = '\\l'.join(sorted(dps)) + '\\l'
            label = f'{{{label}|{dp_str}}}'
        else:
            label = f'{{{label}}}'
        dot.node(nid(c), label=label)

    for c in mc:
        for p in mg.objects(c, RDFS.subClassOf):
            if isinstance(p, rdflib.URIRef):
                if p not in mc and nid(p) not in ext_added:
                    dot.node(nid(p), label=short(p), fillcolor='#EAECEE', color='#85929E')
                    ext_added.add(nid(p))
                if p in mc or nid(p) in ext_added:
                    dot.edge(nid(c), nid(p), arrowhead='empty', color='#333', penwidth='1.5')

    for prop in mg.subjects(RDF.type, OWL.ObjectProperty):
        if not isinstance(prop, rdflib.URIRef): continue
        domains = [d for d in mg.objects(prop, RDFS.domain) if isinstance(d, rdflib.URIRef)]
        ranges = [r for r in mg.objects(prop, RDFS.range) if isinstance(r, rdflib.URIRef)]
        for d in domains:
            for r in ranges:
                if d not in mc and nid(d) not in ext_added:
                    dot.node(nid(d), label=short(d), fillcolor='#EAECEE', color='#85929E')
                    ext_added.add(nid(d))
                if r not in mc and nid(r) not in ext_added:
                    dot.node(nid(r), label=short(r), fillcolor='#EAECEE', color='#85929E')
                    ext_added.add(nid(r))
                dot.edge(nid(d), nid(r), label=short(prop), fontsize='8', style='dashed',
                         color=BORDER.get(mod_name,'#888'), fontcolor=BORDER.get(mod_name,'#888'))

    n = {'core':4,'structure':5,'calculation':6,'provenance':7}[mod_name]
    dot.render(f'mdo_module_{mod_name}', cleanup=True)
    print(f'{n}/7 mdo_module_{mod_name}.png')

print('\nAll 7 visualizations generated!')
