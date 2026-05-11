# MDO 复现操作手册

**目标:** 从零跑通 Materials Design Ontology (Li, Armiento, Lambrix 2020/2024) 的全部 pipeline——加载 4 个 OWL 模块,跑 14 个 Competency Questions 的 SPARQL,把 Materials Project 真实 JSON 数据通过 SPARQL-Generate 映射成 RDF,最后做交叉查询。

**预期总耗时:** 12–15 小时分布在 3 周(每周 4–5 小时)
**前置技能:** Python 基础、命令行、对 RDF 三元组有基本概念
**软件需求:** Python 3.9+,Java 8+,8 GB 内存够用

---

## 总览:你将依次完成的事

| 阶段 | 内容 | 预计时间 |
|---|---|---|
| **阶段 0** | 环境与仓库 | 0.5 小时 |
| **阶段 1** | 单独加载与浏览 4 个模块 | 1.5 小时 |
| **阶段 2** | 用 rdflib 跑 14 个 CQ(纯 Python,无 Java) | 3 小时 |
| **阶段 3** | 用 SPARQL-Generate 把 MP JSON → RDF | 2 小时 |
| **阶段 4** | 在 Blazegraph(或 Apache Jena)里运行真实数据 SPARQL | 2 小时 |
| **阶段 5** | 用 Protégé 可视化与推理 | 1.5 小时 |
| **阶段 6** | 编写复现笔记 + 准备迁移到磁性 | 2 小时 |

---

## 阶段 0 — 环境搭建 (30 分钟)

### 0.1 操作系统

任何 Linux / macOS / Windows WSL2 都行。下面命令以 Ubuntu 风格写,Mac 把 `apt` 换成 `brew`,Windows 直接用 WSL2。

### 0.2 安装系统依赖

```bash
# Python 3.9+ 一般系统自带
python3 --version           # 应该 ≥ 3.9

# Java 8+ (SPARQL-Generate 需要)
sudo apt install default-jdk
java -version               # 应该 ≥ 8

# Git
sudo apt install git
```

### 0.3 创建工作目录与 Python 虚拟环境

```bash
mkdir -p ~/mdo-repro && cd ~/mdo-repro
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 0.4 安装 Python 包

```bash
pip install rdflib==7.0.0 owlready2==0.46 SPARQLWrapper==2.0.0 \
            jupyter pandas matplotlib pyshacl
```

### 0.5 Clone MDO 主仓库

```bash
cd ~/mdo-repro
git clone https://github.com/LiUSemWeb/Materials-Design-Ontology.git mdo
cd mdo
ls
```

预期输出:
```
LICENSE  README.md  catalog-v001.xml  mapping_generator/
mdo-calculation.owl  mdo-core.owl  mdo-full.owl
mdo-provenance.owl  mdo-structure.owl  requirements.md  sparql_query/
```

> **注意:** 旧仓库 `huanyu-li/Materials-Design-Ontology` 已经不再维护(README 第一行明说迁移到 LiUSemWeb)。务必克隆新地址。

### 阶段 0 验收

执行下面这一行,如果输出 `7 modules ready`,环境就 OK 了:

```bash
python3 -c "
import rdflib, owlready2, SPARQLWrapper, pyshacl, jupyter, pandas, matplotlib
print('7 modules ready')
"
```

---

## 阶段 1 — 单独加载并理解 4 个模块 (1.5 小时)

### 1.1 检查每个 OWL 文件的"骨架"

新建文件 `~/mdo-repro/explore_modules.py`:

```python
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
        print(f"  {c_short:35s} ⊂ {', '.join(p_strs) or 'owl:Thing'}")
```

跑一下:

```bash
cd ~/mdo-repro && python3 explore_modules.py
```

**预期输出**(关键数据):
```
===== CORE =====
Triples: 150     Imports: []          Named classes: 5    Object properties: 7

===== STRUCTURE =====  
Triples: 530     Imports: [core/1.0]  Named classes: 12   Object properties: 17

===== CALCULATION =====
Triples: 119     Imports: [core/1.0]  Named classes: 11   Object properties: 3

===== PROVENANCE =====
Triples: 105     Imports: [core/1.0]  Named classes: 1    Object properties: 0
```

### 1.2 加载 full 模块,验证 imports 都解析得到

```bash
python3 -c "
import rdflib
g = rdflib.Graph()
g.parse('mdo/mdo-full.owl')
print('Full triples (before resolving imports):', len(g))
"
```

只会显示 24 triples,因为 `mdo-full.owl` 几乎只有 4 个 `owl:imports` 语句。

**关键认知:** rdflib 默认**不会自动跟踪 imports**。你必须自己手动 `g.parse()` 所有 4 个模块,或者用 `owlready2` 来自动解析。

### 1.3 阅读 `requirements.md` 中的 14 个 CQ

```bash
cat mdo/requirements.md
```

**强制任务:** 把 14 个 CQ 用自己的话翻译一遍写到笔记里。这是后面 SPARQL 调试的"答案 key"。

样例:
- CQ1 = "对每个 Calculation,把它的 output property 和数值都列出来"
- CQ6 = "找所有带隙 > 5 eV 的材料"
- CQ11 = "每个 Calculation 是用哪个软件跑的?"

### 1.4 阅读 4 个 use cases (UC) 和 9 个 additional restrictions (AR)

UC 告诉你"这本体能用来干什么",AR 是 OWL 中的硬约束。
特别注意 **AR2 "一个 Calculation 必有且仅有一个 ComputationalMethod"**,因为它对应 OWL 里的一个 cardinality restriction,后面 reasoner 会用上。

### 阶段 1 验收

回答这三个问题:
1. core 模块的 5 个类是哪 5 个,为什么"Property 分两类"是好设计?
2. structure 模块如何把一个晶体表达完整(从 Structure 走到 CoordinateVector 经过几个对象属性)?
3. provenance 只有 1 个自定义类,它怎么撑起 4 个 CQ?

---

## 阶段 2 — 用 rdflib 跑 14 个 Competency Questions (3 小时)

不用 Java、不用 Blazegraph,完全在 Python 里就能验证 SPARQL。这一阶段先用**手工构造的小 ABox**,后面阶段 4 再换真实 MP 数据。

### 2.1 构建测试数据 ABox

新建 `~/mdo-repro/test_abox.ttl`:

```turtle
@prefix core: <https://w3id.org/mdo/core/> .
@prefix structure: <https://w3id.org/mdo/structure/> .
@prefix calculation: <https://w3id.org/mdo/calculation/> .
@prefix provenance: <https://w3id.org/mdo/provenance/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix qudt: <http://qudt.org/schema/qudt/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix : <http://example.org/data/> .

# A calculation on Cs2TlInF6 (mimicking real MP entry)
:calc_001 a core:Calculation ;
    core:hasInputStructure :struct_in_001 ;
    core:hasOutputStructure :struct_out_001 ;
    calculation:hasComputationalMethod :method_001 ;
    prov:wasAssociatedWith :sw_vasp ;
    prov:wasAttributedTo :ref_001 .

:method_001 a calculation:DensityFunctionalTheoryMethod ;
    calculation:hasXCFunctional :gga_001 ;
    calculation:hasParameter :param_encut .

:gga_001 a calculation:GeneralizedGradientApproximation .

:param_encut a calculation:ComputationalMethodParameter ;
    calculation:hasParameterName "cutoff_energy" ;
    calculation:hasParameterValue "520" .

:struct_out_001 a core:Structure ;
    structure:hasComposition :comp_001 ;
    structure:hasLattice :lat_001 ;
    structure:hasSpaceGroup :sg_225 ;
    core:hasOutputCalculatedProperty :prop_bandgap_001 .

:struct_in_001 a core:Structure .

:comp_001 a structure:Composition ;
    structure:hasDescriptiveFormula "Cs2TlInF6" .

:lat_001 a structure:Lattice ;
    structure:hasLatticeType "cubic" .

:sg_225 a structure:SpaceGroup ;
    structure:hasSpaceGroupSymbol "Fm-3m" .

:prop_bandgap_001 a core:CalculatedProperty ;
    core:hasPropertyName "band_gap" ;
    qudt:quantityValue [
        a qudt:QuantityValue ;
        qudt:numericValue "4.0079"^^xsd:double ;
        qudt:unit <http://qudt.org/vocab/unit/EV>
    ] .

:sw_vasp a prov:SoftwareAgent ;
    provenance:SoftwareName "VASP" .

:ref_001 a provenance:ReferenceAgent ;
    provenance:AuthorName "Persson, Kristin" ;
    provenance:DatabaseName "Materials Project" ;
    provenance:DOI "10.17188/1316836" .
```

### 2.2 写一个 SPARQL 跑批脚本

新建 `~/mdo-repro/run_cqs.py`:

```python
import rdflib
import sys

# Load full ontology + test ABox
g = rdflib.Graph()
for f in ['mdo-core.owl', 'mdo-structure.owl', 
          'mdo-calculation.owl', 'mdo-provenance.owl']:
    g.parse(f'mdo/{f}')
g.parse('test_abox.ttl', format='turtle')

# Common prefixes
PREFIXES = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX core: <https://w3id.org/mdo/core/>
PREFIX structure: <https://w3id.org/mdo/structure/>
PREFIX calculation: <https://w3id.org/mdo/calculation/>
PREFIX provenance: <https://w3id.org/mdo/provenance/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX qudt: <http://qudt.org/schema/qudt/>
"""

# === CQ1: output property and value ===
cq1 = PREFIXES + """
SELECT ?calc ?propName ?value WHERE {
  ?calc a core:Calculation ;
        core:hasOutputCalculatedProperty ?prop .
  ?prop core:hasPropertyName ?propName ;
        qudt:quantityValue ?qv .
  ?qv qudt:numericValue ?value .
}"""

# === CQ6: materials with band_gap > X ===
cq6 = PREFIXES + """
SELECT ?formula ?value WHERE {
  ?prop core:hasPropertyName ?name ;
        qudt:quantityValue ?qv .
  ?qv qudt:numericValue ?value .
  ?structure core:hasOutputCalculatedProperty ?prop ;
             structure:hasComposition ?comp .
  ?comp structure:hasDescriptiveFormula ?formula .
  FILTER (?value > 3 && ?name = "band_gap")
}"""

# === CQ11: software used ===
cq11 = PREFIXES + """
SELECT ?calc ?softwareName WHERE {
  ?calc a core:Calculation ;
        prov:wasAssociatedWith ?software .
  ?software provenance:SoftwareName ?softwareName .
}"""

queries = {'CQ1': cq1, 'CQ6': cq6, 'CQ11': cq11}

for name, q in queries.items():
    print(f"\n----- {name} -----")
    for row in g.query(q):
        print(f"  {dict(row.asdict())}")
```

跑:
```bash
cd ~/mdo-repro && python3 run_cqs.py
```

预期看到 3 个 query 都有非空输出。

### 2.3 把所有 14 个 CQ 都翻译并跑通

`mdo/sparql_query/README.md` 里有官方 SPARQL,但有 **3 处实际问题**,这是论文复现里你必然会踩的坑——也是值得在报告里指出的发现:

| CQ | 文件里的写法 | 实际数据里的写法 | 怎么处理 |
|---|---|---|---|
| CQ1 | `core:hasPropertyValue` | `qudt:quantityValue` + `qudt:numericValue` | 用 qudt 路径 |
| CQ9 | `calculation:hascomputationalMethod`(小写 c) | `calculation:hasComputationalMethod`(大写 C) | 文件里有 typo,改成驼峰 |
| CQ6 | `core:relatesToStructure`(主语→结构) | `core:hasOutputCalculatedProperty`(结构→属性) | 真实 mapping 用了反向 |

**这些不一致本身就是一个有意思的发现**,在你的复现报告里专门写一节 "Documentation–implementation drift" 是个加分项。

### 2.4 写完 14 个 CQ 后,用一个 `assert` 套件验证

```python
# verify_cqs.py
expected = {
    'CQ1':  ('band_gap', 4.0079),
    'CQ6':  ('Cs2TlInF6',),
    'CQ9':  ('method_001',),
    'CQ11': ('VASP',),
}
# ... 每个 CQ 跑完后用 assert 比对预期值
```

### 阶段 2 验收

提交一个 `cq_results.json`,里面有 14 个 CQ 的:
- 我的 SPARQL 文本(可能修复了 typo)
- 测试 ABox 上的输出
- 一句话评价"这个 CQ 反映了 MDO 的哪个建模决策"

---

## 阶段 3 — 把真实 Materials Project JSON 映射成 RDF (2 小时)

这是 MDO 论文最有价值的部分:它**不只是定义本体,还提供了数据从 4 个真实数据库到 RDF 的可执行映射**。

### 3.1 理解 SPARQL-Generate

SPARQL-Generate 是 SPARQL 1.1 的扩展,核心新语法是 `GENERATE { ... } WHERE { ... }`,它把 JSON/CSV/XML 等任意数据"读进"成 SPARQL 变量,再 GENERATE 出 RDF triples。

参考文档:https://sparql-generate.github.io/

### 3.2 跑通 MP 数据集的映射

仓库已经把 SPARQL-Generate JAR 打包好了,直接跑:

```bash
cd ~/mdo-repro/mdo/mapping_generator
ls MP-dataset/ | head      # 应该看到 mp-989XXX_*.json
python3 rdf-generator.py MP
```

这会读所有 MP-dataset/*.json,通过 mp-mappings.rqg 映射成 output{N}.ttl 文件。

> **坑提示:** 仓库**已经包含 85 个预生成的 output*.ttl 文件**!所以即使你不跑 Java,只要看 `MP-dataset/output2.ttl` 就能理解映射输出。但建议至少跑一次完整的 pipeline,确认环境完整。

### 3.3 阅读 mp-mappings.rqg

```bash
less ~/mdo-repro/mdo/mapping_generator/sparql-generate/mp-mappings.rqg
```

这个 `.rqg` 文件是整套复现里**信息密度最高的文件**。重点关注:
- 它如何用 `fun:JSONPath` 函数从 MP JSON 里取字段(如 `$.band_gap`)
- 嵌套的 `GENERATE { ... GENERATE { ... } }` 块——这是为了构造"composition → site → coordinate"这种深层级
- 怎么用 `BIND` 把字符串拼接成新的 IRI

### 3.4 合并多个 output 文件

```bash
# 需要先下载 Apache Jena
cd ~/mdo-repro/mdo/mapping_generator
wget https://archive.apache.org/dist/jena/binaries/apache-jena-3.14.0.tar.gz
tar -xzf apache-jena-3.14.0.tar.gz
python3 merge.py MP
# 产出 MP-dataset/merged.ttl
```

### 3.5 检查结果规模

```bash
wc -l MP-dataset/merged.ttl     # 大约 10K-20K 行
grep -c "core:Calculation" MP-dataset/merged.ttl    # 大约 85
```

### 阶段 3 验收

回答:
1. 一个 MP 的 JSON 包含约 50 个字段,但 mp-mappings.rqg 只用了其中约 15 个。它**选了哪些、丢了哪些**?这反映了 MDO 的"什么是核心信息"的判断。
2. 如果让你加入 `incar` 里的 ENCUT、KPOINTS,你会怎么扩展 mapping?(这是阶段 6 迁移工作的预演)

---

## 阶段 4 — 在 Blazegraph 上跑真实数据 SPARQL (2 小时)

### 4.1 下载 Blazegraph

```bash
cd ~/mdo-repro
wget https://github.com/blazegraph/database/releases/download/BLAZEGRAPH_2_1_6_RC/blazegraph.jar
java -server -Xmx4g -jar blazegraph.jar
```

打开浏览器访问 `http://localhost:9999/bigdata/`

### 4.2 UPDATE tab 加载数据

依次 LOAD 这 5 个文件(用 `LOAD <file:///full/path/to/file>` 语法):
1. `mdo-core.owl`
2. `mdo-structure.owl`
3. `mdo-calculation.owl`
4. `mdo-provenance.owl`
5. `mapping_generator/MP-dataset/merged.ttl`

加载后总应该有约 8000–12000 triples。

### 4.3 在 QUERY tab 跑你阶段 2 修复过的 14 个 CQ

特别有意义的几个查询:

**CQ6 真实版**——所有 band_gap > 3 eV 的材料及其化学式:
```sparql
PREFIX core: <https://w3id.org/mdo/core/>
PREFIX structure: <https://w3id.org/mdo/structure/>
PREFIX qudt: <http://qudt.org/schema/qudt/>

SELECT DISTINCT ?formula ?value WHERE {
  ?property a core:CalculatedProperty ;
            core:hasPropertyName "band_gap" ;
            qudt:quantityValue ?qv .
  ?qv qudt:numericValue ?value .
  ?structure core:hasOutputCalculatedProperty ?property ;
             structure:hasComposition ?comp .
  ?comp structure:hasDescriptiveFormula ?formula .
  FILTER (?value > 3.0)
} ORDER BY DESC(?value)
```

**预期返回约 5–10 行**,包括 Cs2TlInF6 (4.0 eV)、Na1Tl2Ga1F6 (4.4 eV) 等。

### 4.4 提交一个"跨数据库交叉查询"挑战题

如果你也跑了 AFLOW 或 NOMAD 的 mapping,合并所有 merged.ttl 之后试试:

```sparql
# 找在 MP 和 AFLOW 都存在的相同化学式,看 band_gap 是否一致
SELECT ?formula 
       (SAMPLE(?val1) AS ?mp_bg) 
       (SAMPLE(?val2) AS ?aflow_bg) WHERE {
  # ... 用 BIND 区分来自不同数据库的 graph
} GROUP BY ?formula
```

这是 MDO 最有商业价值的应用场景。

### 阶段 4 验收

把 Blazegraph 截图(显示 14 个 CQ 跑通的真实 MP 数据结果)放到复现笔记里。

---

## 阶段 5 — Protégé 可视化与推理 (1.5 小时)

### 5.1 安装 Protégé

下载 https://protege.stanford.edu/ → Desktop Protégé 5.6+
免费,Java 应用。

### 5.2 打开 mdo-full.owl,确认 imports 都解析

`File → Open → mdo/mdo-full.owl`

弹窗会问"是否解析远程 imports"——选 **Yes**。
或者如果你想完全离线,改 `catalog-v001.xml` 把 imports 重定向到本地文件。

### 5.3 跑 HermiT reasoner

`Reasoner → HermiT → Start Reasoner`

看 inferred 后:
- 是否有 inconsistent class?(应该没有)
- "Inferred ontology" 视图里多出来的 subclass 关系
- `core:Calculation` 的 inferred property 列表

### 5.4 OntoGraf 可视化

`Window → Tabs → OntoGraf`

把 4 个核心类拖出来:`Calculation, Structure, Property, ComputationalMethod`,逐步展开。

截图保存为 `mdo_class_diagram.png`,贴到笔记里。

### 5.5 用 OOPS! 自动检测 pitfalls

打开 https://oops.linkeddata.es/,粘贴 mdo-full.owl 的内容,跑自动诊断。

记录下来:
- 哪些 critical pitfalls(P10/P19/P31 等)
- 哪些 minor warnings

**这是给你复现报告增分的重要素材**——批评性地评价 MDO 而不是单纯复述。

### 阶段 5 验收

输出 `mdo_oops_report.md`,把 OOPS 输出的每条 pitfall 都用一两句中文解释,说明你是否同意。

---

## 阶段 6 — 复现报告 + 迁移到磁性的设计草稿 (2 小时)

### 6.1 复现报告模板(写成 `REPRODUCE_REPORT.md`)

```markdown
# MDO 复现报告

## 1. 论文与仓库版本
- 主论文: Li, Armiento, Lambrix, ISWC 2020
- 扩展版: Aameri et al., Semantic Web Journal 2024
- 仓库 commit: <git rev-parse HEAD>
- 复现日期: 2026-XX-XX

## 2. 环境
- OS: ...
- Python: 3.X.X
- 关键包版本: rdflib==7.0.0, owlready2==0.46, ...

## 3. 复现结果对照表
| CQ | 我的结果 | 论文说应该得到的 | 状态 |
|----|---------|-----------------|------|
| CQ1 | 5 个属性返回 | "all properties" | ✓ |
| CQ6 | Cs2TlInF6 (4.0eV), Na1Tl2Ga1F6 (4.4eV) | "wide gap materials" | ✓ |
...

## 4. 发现的不一致(documentation-implementation drift)
- CQ9 SPARQL 文件中 `hascomputationalMethod` 小写,但实际谓词是 `hasComputationalMethod`
- CQ6 文件中用 `relatesToStructure` 但 mp-mappings.rqg 用 `hasOutputCalculatedProperty` 反向
- ...

## 5. 我对 MDO 设计的批评性评价
### 5.1 优点
- 模块化清晰,单向 import core
- PROV-O 复用是教科书级实践
- 14 个 CQ + 4 个 mapping 全可执行,极少 ontology 项目做到这点

### 5.2 弱点
- mdo-calculation 只覆盖 DFT 和 HF,没有 MD/相场/微磁等其他方法
- mdo-structure 没有缺陷描述(CMSO 在此处更强)
- 无 SHACL 约束,只有 OWL axioms

### 5.3 给我自己工作的启示
...

## 6. 复现耗时
- 总时间: XX 小时
- 最大坑: SPARQL 文件与实际数据的预期不匹配,花 X 小时调试
```

### 6.2 设计磁性版本的草稿——`mag-mdo.md`

```markdown
# Magnetic Material Design Ontology (mag-MDO) — Draft

## 沿用 MDO 的什么

- 4 模块架构: mag-core / mag-structure / mag-calculation / mag-provenance
- 单向 import core 的设计
- PROV-O 用于出处
- ChEBI 用于化学元素
- SPARQL-Generate 用于数据库 → RDF

## 必须扩展的部分

### mag-core 新增
- `MagneticCalculation` ⊂ `core:Calculation` 
- `MagneticProperty` ⊂ `core:Property`
- `MagneticStructure` ⊂ `core:Structure`(包含磁结构信息)

### mag-structure 新增
- `MagneticSpaceGroup`(1651 个 Shubnikov 群)
- `SpinConfiguration`(描述 FM/AFM/FiM)
- `MagneticMoment`(每个 Site 的磁矩矢量)
- 关系: Site --hasSpin--> SpinValue

### mag-calculation 新增分支(并列于 DFT)
- `MicromagneticSimulation`(LLG 方程)
- `SpinDynamicsSimulation`(原子级自旋动力学,UppASD/Spirit)
- `MonteCarloSimulation`(经典/量子 Monte Carlo)
- 每个都有自己的 Parameter 类(damping、temperature 等)

### mag-provenance 新增
- 磁性数据库的 ReferenceAgent 子类: MAGNDATA、Bilbao MGENPOS、SuperConDB 等

## CQ 草稿(参照 MDO 14 个)
- mag-CQ1: 所有计算输出的磁性属性(Ms, Hc, K1, MAE) 
- mag-CQ2: 居里温度 > 600 K 的材料
- mag-CQ3: 哪些 Shubnikov 群在 AFM 计算里最常见?
- mag-CQ4: 给定方法(micromagnetic),其参数(damping)的取值分布
- mag-CQ5: 同一材料在 DFT 和 micromagnetic 两层的 MAE 值一致性
- ...

## 数据来源候选
- MaMMoS 数据(直接对接)
- Materials Project magnetic info(部分有 magmom)
- MAGNDATA 磁结构库
- 自己组的微磁仿真输出
```

### 阶段 6 验收

把这两份 .md 文档发给导师审阅,作为下一步工作的提纲。

---

## 常见错误与排查

| 错误 | 原因 | 解决 |
|---|---|---|
| `rdflib.exceptions.ParserError: invalid token` | OWL 文件其实是 turtle 格式,文件名误导 | 加 `format='turtle'` 参数 |
| Blazegraph 内存不够 | 默认堆 1G | 用 `-Xmx4g` 启动 |
| SPARQL-Generate 报 JSONPath 错误 | rqg 里 path 拼错 | 用 jq 先手工提取确认 path |
| owlready2 找不到 imports | 没有联网 | 用 catalog-v001.xml 重定向到本地路径 |
| OOPS! 返回空 | 文件太大或网络超时 | 分模块单独检测 |

## 关键资源

- **论文 (ISWC 2020):** arXiv:2006.07712  
- **论文 (SWJ 2024):** https://doi.org/10.3233/SW-233340  
- **代码:** https://github.com/LiUSemWeb/Materials-Design-Ontology
- **作者:** Patrick Lambrix (patrick.lambrix@liu.se), Rickard Armiento, Huanyu Li  
- **HermiT reasoner:** http://www.hermit-reasoner.com/  
- **SPARQL-Generate 文档:** https://sparql-generate.github.io/  
- **Blazegraph:** https://blazegraph.com/  
- **Protégé:** https://protege.stanford.edu/  
- **OOPS!:** https://oops.linkeddata.es/  

## 进度自查清单

- [ ] 阶段 0:`pip list` 显示 7 个核心包
- [ ] 阶段 1:能口述 4 个模块各自的核心类
- [ ] 阶段 2:14 个 CQ 在 rdflib 上跑通
- [ ] 阶段 3:rdf-generator.py 跑通 MP 数据集
- [ ] 阶段 4:Blazegraph 加载完整数据,14 个 CQ 重跑成功
- [ ] 阶段 5:Protégé 跑 HermiT 无报错,OOPS 报告输出
- [ ] 阶段 6:REPRODUCE_REPORT.md 与 mag-mdo.md 草稿完成
