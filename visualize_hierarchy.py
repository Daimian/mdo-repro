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
        ('calc:', 'https://w3id.org/mdo/calculation/'),
        ('prov:', 'https://w3id.org/mdo/provenance/'),
        ('w3prov:', 'http://www.w3.org/ns/prov#'),
        ('qudt:', 'http://qudt.org/schema/qudt/'),
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
BORDER = {'core':'#2E86C1','structure':'#28B463','calculation':'#E67E22',
          'provenance':'#8E44AD','prov':'#A569BD','qudt':'#717D7E','other':'#ABB2B9'}

all_classes = {c for c in g.subjects(RDF.type, OWL.Class) if isinstance(c, rdflib.URIRef)}

# Approach: use dot engine with cluster per module to force vertical stacking
d = graphviz.Digraph('hierarchy', format='png', engine='dot')
d.attr(rankdir='LR',
       label='MDO Class Hierarchy (color = module, arrows = rdfs:subClassOf)',
       fontsize='16', labelloc='t', fontname='Helvetica-Bold',
       bgcolor='white', nodesep='0.15', ranksep='1.0',
       dpi='150', size='16,20')
d.attr('node', shape='box', style='filled,rounded', fontname='Helvetica',
       fontsize='10', margin='0.10,0.05', height='0.25')
d.attr('edge', arrowhead='empty', color='#666666', penwidth='1.0')

# Group by module in clusters - this forces vertical stacking within each module
module_classes = {}
for c in all_classes:
    module_classes.setdefault(get_module(c), []).append(c)

MODULE_ORDER = ['core', 'structure', 'calculation', 'provenance', 'prov', 'qudt']
MODULE_LABELS = {'core': 'mdo-core (10 classes)', 'structure': 'mdo-structure (14 classes)',
                 'calculation': 'mdo-calculation (12 classes)',
                 'provenance': 'mdo-provenance (4 classes)',
                 'prov': 'W3C PROV-O (reused)', 'qudt': 'QUDT (reused)'}

for mod in MODULE_ORDER:
    classes = module_classes.get(mod, [])
    if not classes:
        continue
    with d.subgraph(name=f'cluster_{mod}') as sg:
        sg.attr(label=MODULE_LABELS.get(mod, mod),
                style='rounded,filled',
                color=BORDER.get(mod, '#AAA'),
                fillcolor=FILL.get(mod, '#F8F8F8') + '30',
                fontname='Helvetica-Bold', fontsize='12',
                fontcolor=BORDER.get(mod, '#AAA'))
        for c in sorted(classes, key=lambda x: short(x)):
            sg.node(nid(c), label=short(c),
                    fillcolor=FILL.get(mod, '#F2F3F4'),
                    color=BORDER.get(mod, '#AAA'), penwidth='1.5')

# subClassOf edges
for c in all_classes:
    for p in g.objects(c, RDFS.subClassOf):
        if isinstance(p, rdflib.URIRef) and p in all_classes:
            d.edge(nid(c), nid(p))

d.render('mdo_class_hierarchy', cleanup=True)

# Check size
from PIL import Image
img = Image.open('mdo_class_hierarchy.png')
print(f'Generated: mdo_class_hierarchy.png ({img.size[0]}x{img.size[1]})')

d.format = 'pdf'
d.render('mdo_class_hierarchy', cleanup=True)
print('Generated: mdo_class_hierarchy.pdf')
