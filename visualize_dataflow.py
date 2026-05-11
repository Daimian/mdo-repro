import graphviz

d = graphviz.Digraph('dataflow', format='png', engine='dot')
d.attr(rankdir='TB', label='MDO Data Flow: From Raw Database to Semantic Query',
       fontsize='18', labelloc='t', fontname='Helvetica-Bold',
       bgcolor='white', nodesep='0.6', ranksep='0.8', dpi='150', pad='0.5')

# ============================================================
# LAYER 1: External Data Sources
# ============================================================
with d.subgraph(name='cluster_sources') as s:
    s.attr(label='Layer 1: External Data Sources (Raw JSON/API)',
           style='rounded,filled', fillcolor='#FEF9E7', color='#F39C12',
           fontname='Helvetica-Bold', fontsize='12', fontcolor='#7D6608')
    s.attr('node', shape='cylinder', style='filled', fontname='Helvetica', fontsize='10')
    s.node('mp', 'Materials\nProject\n(85 JSON)', fillcolor='#F9E79F', color='#F39C12')
    s.node('aflow', 'AFLOW\n(JSON)', fillcolor='#F9E79F', color='#F39C12')
    s.node('nomad', 'NOMAD\n(JSON)', fillcolor='#F9E79F', color='#F39C12')
    s.node('optimade', 'OPTIMADE\n(JSON)', fillcolor='#F9E79F', color='#F39C12')

# ============================================================
# LAYER 2: Mapping (SPARQL-Generate)
# ============================================================
with d.subgraph(name='cluster_mapping') as s:
    s.attr(label='Layer 2: Mapping (JSON → RDF)',
           style='rounded,filled', fillcolor='#FDEBD0', color='#E67E22',
           fontname='Helvetica-Bold', fontsize='12', fontcolor='#784212')
    s.attr('node', shape='component', style='filled', fontname='Helvetica', fontsize='10')
    s.node('rqg_mp', 'mp-mappings.rqg\n(SPARQL-Generate)', fillcolor='#FAD7A0', color='#E67E22')
    s.node('rqg_aflow', 'aflow-mappings.rqg', fillcolor='#FAD7A0', color='#E67E22')
    s.node('rqg_nomad', 'nomad-mappings.rqg', fillcolor='#FAD7A0', color='#E67E22')
    s.node('rqg_opt', 'optimade-mappings.rqg', fillcolor='#FAD7A0', color='#E67E22')

    s.node('jsonpath', 'fun:JSONPath\n$.band_gap\n$.spacegroup.symbol\n$.snl_final.sites[*]\n...',
           shape='note', fillcolor='#FDEBD0', color='#E67E22', fontsize='9')

# ============================================================
# LAYER 3: TBox (Ontology Definition)
# ============================================================
with d.subgraph(name='cluster_tbox') as s:
    s.attr(label='Layer 3: TBox (OWL Ontology — 4 Modules)',
           style='rounded,filled', fillcolor='#D6EAF8', color='#2E86C1',
           fontname='Helvetica-Bold', fontsize='12', fontcolor='#1B4F72')
    s.attr('node', shape='box', style='filled,rounded', fontname='Helvetica', fontsize='10')
    s.node('core', 'mdo-core.owl\n\nCalculation, Structure,\nProperty, Material',
           fillcolor='#AED6F1', color='#2E86C1')
    s.node('struct', 'mdo-structure.owl\n\nLattice, SpaceGroup,\nComposition, Site, Atom',
           fillcolor='#A9DFBF', color='#28B463')
    s.node('calc', 'mdo-calculation.owl\n\nComputationalMethod,\nDFT, HF, XC Functional',
           fillcolor='#FAD7A0', color='#E67E22')
    s.node('prov', 'mdo-provenance.owl\n\nReferenceAgent,\nSoftwareAgent (PROV-O)',
           fillcolor='#D7BDE2', color='#8E44AD')

    # imports
    s.edge('struct', 'core', label='owl:imports', style='dotted', color='#2E86C1',
           fontsize='8', fontcolor='#2E86C1', arrowhead='vee')
    s.edge('calc', 'core', label='owl:imports', style='dotted', color='#E67E22',
           fontsize='8', fontcolor='#E67E22', arrowhead='vee')
    s.edge('prov', 'core', label='owl:imports', style='dotted', color='#8E44AD',
           fontsize='8', fontcolor='#8E44AD', arrowhead='vee')

    # external vocabs
    s.node('qudt', 'QUDT\n(units & values)', shape='box', style='filled,rounded,dashed',
           fillcolor='#EAECEE', color='#717D7E', fontsize='9')
    s.node('provo', 'W3C PROV-O\n(provenance)', shape='box', style='filled,rounded,dashed',
           fillcolor='#EAECEE', color='#717D7E', fontsize='9')
    s.edge('core', 'qudt', label='reuses', style='dotted', color='#717D7E',
           fontsize='8', fontcolor='#717D7E', arrowhead='vee')
    s.edge('prov', 'provo', label='reuses', style='dotted', color='#717D7E',
           fontsize='8', fontcolor='#717D7E', arrowhead='vee')

# ============================================================
# LAYER 4: ABox (RDF Instances)
# ============================================================
with d.subgraph(name='cluster_abox') as s:
    s.attr(label='Layer 4: ABox (RDF Instance Data)',
           style='rounded,filled', fillcolor='#D5F5E3', color='#28B463',
           fontname='Helvetica-Bold', fontsize='12', fontcolor='#1D8348')
    s.attr('node', shape='box3d', style='filled', fontname='Helvetica', fontsize='10')
    s.node('ttl', 'output*.ttl\n(85 files, per-entry)', fillcolor='#A9DFBF', color='#28B463')
    s.node('merged', 'merged.ttl\n(71K lines,\n43,835 triples)', fillcolor='#82E0AA', color='#1E8449')

# ============================================================
# LAYER 5: Triple Store & Query
# ============================================================
with d.subgraph(name='cluster_query') as s:
    s.attr(label='Layer 5: Query & Application',
           style='rounded,filled', fillcolor='#E8DAEF', color='#8E44AD',
           fontname='Helvetica-Bold', fontsize='12', fontcolor='#4A235A')
    s.attr('node', shape='box', style='filled,rounded', fontname='Helvetica', fontsize='10')
    s.node('store', 'Triple Store\n(Blazegraph / rdflib)',
           shape='cylinder', fillcolor='#D7BDE2', color='#8E44AD')
    s.node('cq', '14 Competency Questions\n(SPARQL SELECT)',
           fillcolor='#D7BDE2', color='#8E44AD')
    s.node('results', 'Query Results\n\nCQ6: 7 materials with\nband_gap > 5 eV\nCQ12: 456 author records\n...',
           shape='note', fillcolor='#F5EEF8', color='#8E44AD', fontsize='9')

# ============================================================
# EDGES: Data Flow
# ============================================================
edge_style = dict(penwidth='2.0', arrowhead='vee', arrowsize='0.8')

# Sources → Mapping
d.edge('mp', 'rqg_mp', label='  85 JSON files  ', fontsize='9', color='#E67E22',
       fontcolor='#784212', **edge_style)
d.edge('aflow', 'rqg_aflow', fontsize='9', color='#E67E22', **edge_style)
d.edge('nomad', 'rqg_nomad', fontsize='9', color='#E67E22', **edge_style)
d.edge('optimade', 'rqg_opt', fontsize='9', color='#E67E22', **edge_style)

# JSONPath detail
d.edge('rqg_mp', 'jsonpath', style='dashed', color='#E67E22', arrowhead='none')

# Mapping → ABox (uses TBox as template)
d.edge('rqg_mp', 'ttl', label='  GENERATE { triples }  ', fontsize='9',
       color='#28B463', fontcolor='#1D8348', **edge_style)
d.edge('rqg_aflow', 'ttl', color='#28B463', **edge_style)
d.edge('rqg_nomad', 'ttl', color='#28B463', **edge_style)
d.edge('rqg_opt', 'ttl', color='#28B463', **edge_style)

# TBox guides mapping
d.edge('core', 'rqg_mp', label='  defines classes\n  & properties  ', fontsize='8',
       color='#2E86C1', fontcolor='#1B4F72', style='dashed', arrowhead='vee')

# ABox merge
d.edge('ttl', 'merged', label='  merge.py  ', fontsize='9',
       color='#1E8449', fontcolor='#1D8348', **edge_style)

# ABox + TBox → Store
d.edge('merged', 'store', label='  LOAD  ', fontsize='9',
       color='#8E44AD', fontcolor='#4A235A', **edge_style)
d.edge('core', 'store', label='  LOAD OWL  ', fontsize='8',
       color='#8E44AD', fontcolor='#4A235A', style='dashed', arrowhead='vee')

# Store → Query → Results
d.edge('store', 'cq', label='  SPARQL endpoint  ', fontsize='9',
       color='#8E44AD', fontcolor='#4A235A', **edge_style)
d.edge('cq', 'results', color='#8E44AD', **edge_style)

# ============================================================
# DRIFT annotation
# ============================================================
d.node('drift', '⚠ Documentation–Implementation Drift\n\n'
       'OWL defines: core:PropertyName\n'
       'Mapping outputs: core:hasPropertyName\n'
       'SPARQL file uses: core:hasPropertyValue (nonexistent)\n\n'
       '→ Query must match ABox, not TBox',
       shape='note', style='filled', fillcolor='#FDEDEC', color='#E74C3C',
       fontname='Helvetica', fontsize='9', fontcolor='#922B21')
d.edge('rqg_mp', 'drift', style='dashed', color='#E74C3C', arrowhead='none')
d.edge('drift', 'cq', style='dashed', color='#E74C3C', arrowhead='none',
       label='  fix property names  ', fontsize='8', fontcolor='#922B21')

d.render('mdo_dataflow', cleanup=True)

from PIL import Image
img = Image.open('mdo_dataflow.png')
print(f'Generated: mdo_dataflow.png ({img.size[0]}x{img.size[1]})')

d.format = 'pdf'
d.render('mdo_dataflow', cleanup=True)
print('Generated: mdo_dataflow.pdf')
