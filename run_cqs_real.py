import rdflib
import json

g = rdflib.Graph()
for f in ['mdo-core.owl', 'mdo-structure.owl',
          'mdo-calculation.owl', 'mdo-provenance.owl']:
    g.parse(f'mdo/{f}')
g.parse('mdo/mapping_generator/MP-dataset/merged.ttl', format='turtle')
print(f"Total triples loaded: {len(g)}")

# Prefixes matching what merged.ttl actually uses
PREFIXES = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX core: <https://w3id.org/mdo/core/>
PREFIX structure: <https://w3id.org/mdo/structure/>
PREFIX calculation: <https://w3id.org/mdo/calculation/>
PREFIX provenance: <https://w3id.org/mdo/provenance/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX QUDT: <http://qudt.org/schema/qudt/>
"""

queries = {}

# CQ1: calculated properties and values
queries['CQ1'] = PREFIXES + """
SELECT ?calculation ?propName ?value WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputCalculatedProperty ?property .
  ?property core:hasPropertyName ?propName ;
            QUDT:quantityValue ?qv .
  ?qv QUDT:numericValue ?value .
} LIMIT 10"""

# CQ2: input and output structures
queries['CQ2'] = PREFIXES + """
SELECT ?calculation ?input ?output WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasInputStructure ?input ;
               core:hasOutputStructure ?output .
} LIMIT 10"""

# CQ3: space group of structure
queries['CQ3'] = PREFIXES + """
SELECT ?calculation ?output ?symbol WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputStructure ?output .
  ?output structure:hasSpaceGroup ?sg .
  ?sg structure:hasSpaceGroupSymbol ?symbol .
} LIMIT 10"""

# CQ4: lattice type
queries['CQ4'] = PREFIXES + """
SELECT ?calculation ?output ?type WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputStructure ?output .
  ?output structure:hasLattice ?lattice .
  ?lattice structure:hasLatticeType ?type .
} LIMIT 10"""

# CQ5: chemical formula
queries['CQ5'] = PREFIXES + """
SELECT ?calculation ?output ?formula WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputStructure ?output .
  ?output structure:hasComposition ?comp .
  ?comp structure:hasDescriptiveFormula ?formula .
} LIMIT 10"""

# CQ6: band_gap > 5 eV materials
queries['CQ6'] = PREFIXES + """
SELECT ?formula ?value WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputCalculatedProperty ?property ;
               core:hasOutputStructure ?output .
  ?property QUDT:quantityValue ?qv ;
            core:hasPropertyName ?name .
  ?qv QUDT:numericValue ?value .
  ?output structure:hasComposition ?comp .
  ?comp structure:hasDescriptiveFormula ?formula .
  FILTER (?value > 5 && ?name = "band_gap")
} ORDER BY DESC(?value)"""

# CQ7: band_gap > 5, show lattice type
queries['CQ7'] = PREFIXES + """
SELECT ?output ?value ?type WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputCalculatedProperty ?property ;
               core:hasOutputStructure ?output .
  ?property QUDT:quantityValue ?qv ;
            core:hasPropertyName ?name .
  ?qv QUDT:numericValue ?value .
  ?output structure:hasLattice ?lattice .
  ?lattice structure:hasLatticeType ?type .
  FILTER (?value > 5 && ?name = "band_gap")
}"""

# CQ8: band_gap for cubic structures
queries['CQ8'] = PREFIXES + """
SELECT ?output ?value ?type WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputCalculatedProperty ?property ;
               core:hasOutputStructure ?output .
  ?property QUDT:quantityValue ?qv ;
            core:hasPropertyName ?name .
  ?qv QUDT:numericValue ?value .
  ?output structure:hasLattice ?lattice .
  ?lattice structure:hasLatticeType ?type .
  FILTER (?name = "band_gap" && ?type = "cubic")
} LIMIT 10"""

# CQ9: computational method (not in merged.ttl - mapping doesn't include it)
queries['CQ9'] = PREFIXES + """
SELECT ?calculation ?method WHERE {
  ?calculation rdf:type core:Calculation ;
               calculation:hasComputationalMethod ?method .
} LIMIT 10"""

# CQ10: parameter values
queries['CQ10'] = PREFIXES + """
SELECT ?calculation ?method ?name ?value WHERE {
  ?calculation rdf:type core:Calculation ;
               calculation:hasComputationalMethod ?method .
  ?method calculation:hasParameter ?param .
  ?param calculation:ParameterName ?name ;
         calculation:ParameterValue ?value .
  FILTER (?name = "cutoff_energy")
} LIMIT 10"""

# CQ11: software
queries['CQ11'] = PREFIXES + """
SELECT ?calculation ?software WHERE {
  ?calculation rdf:type core:Calculation ;
               prov:wasAssociatedWith ?software .
} LIMIT 10"""

# CQ12: authors
queries['CQ12'] = PREFIXES + """
SELECT ?calculation ?author WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputStructure ?output .
  ?output prov:wasAttributedTo ?ref .
  ?ref provenance:hasAuthorName ?author .
} LIMIT 10"""

# CQ13: same as CQ11
queries['CQ13'] = PREFIXES + """
SELECT ?calculation ?software WHERE {
  ?calculation rdf:type core:Calculation ;
               prov:wasAssociatedWith ?software .
} LIMIT 10"""

# CQ14: publication datetime
queries['CQ14'] = PREFIXES + """
SELECT ?calculation ?datetime WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputStructure ?output .
  ?output prov:wasAttributedTo ?ref .
  ?ref provenance:hasPublicationDateTime ?datetime .
} LIMIT 10"""

results = {}
for name, q in sorted(queries.items(), key=lambda x: int(x[0][2:])):
    print(f"\n----- {name} -----")
    rows = list(g.query(q))
    n = len(rows)
    print(f"  Results: {n} rows")
    for row in rows[:3]:
        d = {str(k): str(v) for k, v in row.asdict().items()}
        print(f"  {d}")
    if n > 3:
        print(f"  ... ({n - 3} more)")
    results[name] = n

print(f"\n\n===== SUMMARY =====")
for name in sorted(results.keys(), key=lambda x: int(x[2:])):
    status = "PASS" if results[name] > 0 else "FAIL (0 rows)"
    print(f"  {name}: {results[name]} rows - {status}")

with open('cq_results_real.json', 'w') as f:
    json.dump(results, f, indent=2)
