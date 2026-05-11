# MDO Reproduction

Reproduction of the **Materials Design Ontology** (Li, Armiento, Lambrix, ISWC 2020 / SWJ 2024).

## Quick Start

```bash
# 1. Clone this repo
git clone https://github.com/mian-dai/mdo-repro.git
cd mdo-repro

# 2. Clone the MDO ontology (required dependency)
git clone https://github.com/LiUSemWeb/Materials-Design-Ontology.git mdo

# 3. Set up Python environment
python3 -m venv venv && source venv/bin/activate
pip install rdflib==7.0.0 owlready2==0.46 SPARQLWrapper==2.0.0 jupyter pandas matplotlib pyshacl graphviz

# 4. Run the reproduction scripts
python3 explore_modules.py       # Phase 1: explore ontology modules
python3 run_cqs.py               # Phase 2: 14 CQs on test ABox (all PASS)
python3 run_cqs_real.py          # Phase 4: 14 CQs on real MP data (10/14 PASS)
python3 visualize_mdo.py         # Phase 5: generate ontology diagrams
python3 visualize_hierarchy.py   # Phase 5: class hierarchy diagram
python3 visualize_dataflow.py    # Phase 5: data flow diagram
```

## Repository Structure

```
├── MDO_Reproduction_Handbook.md   # Step-by-step reproduction guide
├── REPRODUCE_REPORT.md            # Reproduction report with findings
├── test_abox.ttl                  # Hand-crafted test data (1 Cs2TlInF6 entry)
├── explore_modules.py             # Explore 4 OWL module skeletons
├── run_cqs.py                     # Run 14 CQs against test ABox
├── run_cqs_real.py                # Run 14 CQs against real MP data
├── cq_results.json                # Test ABox query results
├── cq_results_real.json           # Real MP data query results
├── visualize_mdo.py               # Generate ontology diagrams
├── visualize_hierarchy.py         # Generate class hierarchy diagram
├── visualize_dataflow.py          # Generate data flow diagram
├── mdo_class_hierarchy.png/pdf    # Class hierarchy (40 classes, 4 modules)
├── mdo_ontograf.png               # Full ontology graph
├── mdo_property_map.png           # Object properties (domain → range)
├── mdo_module_*.png               # Per-module detail diagrams
└── mdo_dataflow.png/pdf           # End-to-end data flow diagram
```

## Key Findings

- **14/14 CQs pass** on hand-crafted test data (after fixing property name mismatches)
- **10/14 CQs pass** on real MP data; 4 fail because the mapping omits computational method and software info
- **Three-layer naming drift** between OWL definitions, SPARQL query files, and actual mapping output — documented in detail in `REPRODUCE_REPORT.md`

## References

- Paper (ISWC 2020): [arXiv:2006.07712](https://arxiv.org/abs/2006.07712)
- Paper (SWJ 2024): [doi:10.3233/SW-233340](https://doi.org/10.3233/SW-233340)
- MDO Repository: [github.com/LiUSemWeb/Materials-Design-Ontology](https://github.com/LiUSemWeb/Materials-Design-Ontology)
