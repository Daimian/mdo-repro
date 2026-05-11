import rdflib
import json

# Load full ontology + test ABox
g = rdflib.Graph()
for f in ['mdo-core.owl', 'mdo-structure.owl',
          'mdo-calculation.owl', 'mdo-provenance.owl']:
    g.parse(f'mdo/{f}')
g.parse('test_abox.ttl', format='turtle')
print(f"Total triples loaded: {len(g)}")

PREFIXES = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX core: <https://w3id.org/mdo/core/>
PREFIX structure: <https://w3id.org/mdo/structure/>
PREFIX calculation: <https://w3id.org/mdo/calculation/>
PREFIX provenance: <https://w3id.org/mdo/provenance/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX qudt: <http://qudt.org/schema/qudt/>
"""

queries = {}

# CQ1: What are the calculated properties and their values produced by a calculation?
# FIX: official uses core:hasPropertyValue (doesn't exist) -> use qudt:quantityValue + qudt:numericalValue
# FIX: official uses core:hasPropertyName -> actual is core:PropertyName
queries['CQ1'] = PREFIXES + """
SELECT ?calculation ?propName ?value WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputCalculatedProperty ?property .
  ?property core:PropertyName ?propName ;
            qudt:quantityValue ?qv .
  ?qv qudt:numericalValue ?value .
}"""

# CQ2: What are the input and output structures of a calculation?
queries['CQ2'] = PREFIXES + """
SELECT ?calculation ?input_structure ?output_structure WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasInputStructure ?input_structure ;
               core:hasOutputStructure ?output_structure .
}"""

# CQ3: What is the space group type of a structure?
queries['CQ3'] = PREFIXES + """
SELECT ?calculation ?output_structure ?symbol WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputStructure ?output_structure .
  ?output_structure rdf:type core:Structure ;
                    structure:hasSpaceGroup ?spacegroup .
  ?spacegroup rdf:type structure:SpaceGroup ;
              structure:hasSpaceGroupSymbol ?symbol .
}"""

# CQ4: What is the lattice type of a structure?
queries['CQ4'] = PREFIXES + """
SELECT ?calculation ?output_structure ?type WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputStructure ?output_structure .
  ?output_structure rdf:type core:Structure ;
                    structure:hasLattice ?lattice .
  ?lattice rdf:type structure:Lattice ;
           structure:hasLatticeType ?type .
}"""

# CQ5: What is the chemical formula of a structure?
queries['CQ5'] = PREFIXES + """
SELECT ?calculation ?output_structure ?formula WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputStructure ?output_structure .
  ?output_structure structure:hasComposition ?composition .
  ?composition structure:hasDescriptiveFormula ?formula .
}"""

# CQ6: Compositions of materials with band_gap in a specific range
# FIX: official CQ6 uses qudt path (correct), but core:hasPropertyName -> core:PropertyName
# FIX: qudt:numericValue -> qudt:numericalValue
queries['CQ6'] = PREFIXES + """
SELECT ?formula ?value WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputCalculatedProperty ?property ;
               core:hasOutputStructure ?output_structure .
  ?property qudt:quantityValue ?qv ;
            core:PropertyName ?name .
  ?qv rdf:type qudt:QuantityValue ;
      qudt:numericalValue ?value .
  ?output_structure structure:hasComposition ?composition .
  ?composition structure:hasDescriptiveFormula ?formula .
  FILTER (?value > 3 && ?name = "band_gap")
}"""

# CQ7: For a specific material and given band_gap range, what is the lattice type?
# FIX: same as CQ1 - hasPropertyValue doesn't exist, use qudt path
queries['CQ7'] = PREFIXES + """
SELECT ?output_structure ?value ?type WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputCalculatedProperty ?property ;
               core:hasOutputStructure ?output_structure .
  ?property qudt:quantityValue ?qv ;
            core:PropertyName ?name .
  ?qv qudt:numericalValue ?value .
  ?output_structure structure:hasLattice ?lattice .
  ?lattice structure:hasLatticeType ?type .
  FILTER (?value > 3 && ?name = "band_gap")
}"""

# CQ8: For a specific material and expected lattice type, what are calculated property values?
# FIX: same as CQ7
queries['CQ8'] = PREFIXES + """
SELECT ?output_structure ?value ?type WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputCalculatedProperty ?property ;
               core:hasOutputStructure ?output_structure .
  ?property qudt:quantityValue ?qv ;
            core:PropertyName ?name .
  ?qv qudt:numericalValue ?value .
  ?output_structure structure:hasLattice ?lattice .
  ?lattice structure:hasLatticeType ?type .
  FILTER (?name = "band_gap" && ?type = "cubic")
}"""

# CQ9: What is the computational method used in a calculation?
# FIX: hascomputationalMethod (lowercase c) -> hasComputationalMethod (uppercase C)
queries['CQ9'] = PREFIXES + """
SELECT ?calculation ?method WHERE {
  ?calculation rdf:type core:Calculation ;
               calculation:hasComputationalMethod ?method .
}"""

# CQ10: What is the value for a specific parameter of the method?
# FIX: hascomputationalMethod -> hasComputationalMethod
# FIX: hasParameterValue/hasParameterName on method -> ParameterValue/ParameterName on parameter
queries['CQ10'] = PREFIXES + """
SELECT ?calculation ?method ?name ?value WHERE {
  ?calculation rdf:type core:Calculation ;
               calculation:hasComputationalMethod ?method .
  ?method calculation:hasParameter ?parameter .
  ?parameter calculation:ParameterName ?name ;
             calculation:ParameterValue ?value .
  FILTER (?name = "cutoff_energy")
}"""

# CQ11: Which software produced the result of a calculation?
queries['CQ11'] = PREFIXES + """
SELECT ?calculation ?software WHERE {
  ?calculation rdf:type core:Calculation ;
               prov:wasAssociatedWith ?software .
}"""

# CQ12: Who are the authors of the calculation?
# FIX: provenance:hasAuthorName -> provenance:AuthorName
queries['CQ12'] = PREFIXES + """
SELECT ?calculation ?author_name WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputStructure ?output_structure .
  ?output_structure rdf:type core:Structure ;
                    prov:wasAttributedTo ?reference .
  ?reference rdf:type provenance:ReferenceAgent ;
             provenance:AuthorName ?author_name .
}"""

# CQ13: (duplicate of CQ11 in official file - same query)
queries['CQ13'] = PREFIXES + """
SELECT ?calculation ?software WHERE {
  ?calculation rdf:type core:Calculation ;
               prov:wasAssociatedWith ?software .
}"""

# CQ14: When was the calculation data published?
# FIX: provenance:hasPublicationDateTime -> provenance:PublicationDateTime
queries['CQ14'] = PREFIXES + """
SELECT ?calculation ?datetime WHERE {
  ?calculation rdf:type core:Calculation ;
               core:hasOutputStructure ?output_structure .
  ?output_structure rdf:type core:Structure ;
                    prov:wasAttributedTo ?reference .
  ?reference rdf:type provenance:ReferenceAgent ;
             provenance:PublicationDateTime ?datetime .
}"""

results = {}
for name, q in sorted(queries.items(), key=lambda x: int(x[0][2:])):
    print(f"\n----- {name} -----")
    rows = list(g.query(q))
    print(f"  Results: {len(rows)} rows")
    for row in rows:
        d = {str(k): str(v) for k, v in row.asdict().items()}
        print(f"  {d}")
    results[name] = {
        'row_count': len(rows),
        'data': [{str(k): str(v) for k, v in row.asdict().items()} for row in rows]
    }

print(f"\n\n===== SUMMARY =====")
all_pass = True
for name in sorted(results.keys(), key=lambda x: int(x[2:])):
    status = "PASS" if results[name]['row_count'] > 0 else "FAIL (0 rows)"
    if results[name]['row_count'] == 0:
        all_pass = False
    print(f"  {name}: {results[name]['row_count']} rows - {status}")

print(f"\nOverall: {'ALL PASS' if all_pass else 'SOME FAILED'}")

with open('cq_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nResults saved to cq_results.json")
