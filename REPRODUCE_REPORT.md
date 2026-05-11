# MDO 复现报告

## 1. 论文与仓库版本

- 主论文: Li, Armiento, Lambrix, "An Ontology for the Materials Design Domain", ISWC 2020 (arXiv:2006.07712)
- 扩展版: Aameri et al., Semantic Web Journal 2024 (https://doi.org/10.3233/SW-233340)
- 仓库: https://github.com/LiUSemWeb/Materials-Design-Ontology
- 仓库 commit: `0a7983308359f398ac5902190b489ca773c0db7f`
- 复现日期: 2026-05-11

## 2. 环境

- OS: macOS (Darwin 25.4.0, aarch64)
- Python: 3.14.3
- Java: OpenJDK 25.0.1 (JVM crash, 未能用于 SPARQL-Generate — 使用预生成的 output 文件)
- 关键包版本: rdflib==7.0.0, owlready2==0.46, SPARQLWrapper==2.0.0, pyshacl==0.28.1

## 3. 本体模块概览

| 模块 | Triples | Named Classes | Object Properties | Imports |
|---|---|---|---|---|
| core | 150 | 10 | 10 | 无 |
| structure | 530 | 14 | 17 | core/1.1 |
| calculation | 119 | 12 | 3 | core/1.1 |
| provenance | 105 | 4 | 2 | core/1.1 |
| full | 23 | 0 | 0 | 4 个 owl:imports |

`mdo-full.owl` 只包含 4 个 import 声明。rdflib 不会自动跟踪 imports，需手动加载各模块。

## 4. CQ 复现结果对照表

### 4.1 测试 ABox (手写单条 Cs2TlInF6 数据)

| CQ | 描述 | 结果 | 状态 |
|---|---|---|---|
| CQ1 | 计算输出的属性及值 | band_gap = 4.0079 | PASS |
| CQ2 | 输入输出结构 | struct_in_001, struct_out_001 | PASS |
| CQ3 | 空间群 | Fm-3m | PASS |
| CQ4 | 晶格类型 | cubic | PASS |
| CQ5 | 化学式 | Cs2TlInF6 | PASS |
| CQ6 | band_gap > 3 eV 的材料 | Cs2TlInF6 (4.0079) | PASS |
| CQ7 | band_gap > 3 + 晶格类型 | 4.0079, cubic | PASS |
| CQ8 | cubic 结构的 band_gap | 4.0079 | PASS |
| CQ9 | 计算方法 | method_001 (DFT) | PASS |
| CQ10 | 方法参数 (cutoff_energy) | 520 | PASS |
| CQ11 | 软件 | sw_vasp | PASS |
| CQ12 | 作者 | Persson, Kristin | PASS |
| CQ13 | 软件 (同 CQ11) | sw_vasp | PASS |
| CQ14 | 发布时间 | 2020-01-15T00:00:00 | PASS |

**14/14 PASS** (需修正官方 SPARQL 中的属性名，详见第 5 节)

### 4.2 真实 MP 数据 (85 个 Calculation, 43,835 triples)

| CQ | 结果行数 | 状态 | 说明 |
|---|---|---|---|
| CQ1 | 425+ | PASS | 每个 Calculation 输出 5 个属性 |
| CQ2 | 85 | PASS | 每个 Calculation 有 input/output structure |
| CQ3 | 85 | PASS | 所有 85 个都是 Fm-3m |
| CQ4 | 85 | PASS | 所有 85 个都是 cubic |
| CQ5 | 85 | PASS | 85 个不同化学式 |
| CQ6 | 7 | PASS | band_gap > 5 eV: Cs2K1Ga1F6 (6.04) 最高 |
| CQ7 | 7 | PASS | 全部为 cubic |
| CQ8 | 85 | PASS | 所有 cubic 结构的 band_gap |
| CQ9 | 0 | **FAIL** | 映射未包含 computational method |
| CQ10 | 0 | **FAIL** | 映射未包含 method parameters |
| CQ11 | 0 | **FAIL** | 映射未包含 prov:wasAssociatedWith |
| CQ12 | 456 | PASS | 多作者展开 |
| CQ13 | 0 | **FAIL** | 同 CQ11 |
| CQ14 | 85 | PASS | 均有发布时间 |

**10/14 PASS, 4/14 FAIL** — 失败原因为 mp-mappings.rqg 未映射计算方法和软件信息。

### 4.3 CQ6 完整结果: band_gap > 5 eV 的材料

| 化学式 | Band Gap (eV) |
|---|---|
| Cs2K1Ga1F6 | 6.0426 |
| Cs2Rb1Ga1F6 | 5.9393 |
| Rb2Na1Ga1F6 | 5.9026 |
| Cs1Rb2Ga1F6 | 5.5428 |
| Cs2K1In1F6 | 5.4629 |
| Cs2Rb1In1F6 | 5.3760 |
| Rb2Na1In1F6 | 5.2687 |

全部为含 Ga 或 In 的氟化物双钙钛矿。

## 5. 发现的不一致 (Documentation–Implementation Drift)

这是本次复现最重要的发现之一。MDO 存在**三层命名不一致**:

### 5.1 OWL 定义 vs 官方 SPARQL 查询文件

| 位置 | SPARQL 文件写法 | OWL 实际定义 | 涉及 CQ |
|---|---|---|---|
| 属性值路径 | `core:hasPropertyValue` | 不存在。应走 `qudt:quantityValue` → `qudt:numericalValue` | CQ1, CQ7, CQ8 |
| 属性名 | `core:hasPropertyName` | `core:PropertyName` (DataProperty, 无 has 前缀) | CQ1, CQ6-CQ8 |
| 计算方法 | `calculation:hascomputationalMethod` | `calculation:hasComputationalMethod` (大写 C) | CQ9, CQ10 |
| 参数值/名 | `calculation:hasParameterValue/Name` (挂在 method 上) | `calculation:ParameterValue/ParameterName` (无 has, 挂在 Parameter 上) | CQ10 |
| 作者名 | `provenance:hasAuthorName` | `provenance:AuthorName` (无 has 前缀) | CQ12 |
| 发布时间 | `provenance:hasPublicationDateTime` | `provenance:PublicationDateTime` (无 has 前缀) | CQ14 |

### 5.2 OWL 定义 vs 实际映射输出 (merged.ttl)

| 属性 | OWL 定义 | merged.ttl 实际使用 |
|---|---|---|
| 属性名 | `core:PropertyName` | `core:hasPropertyName` |
| 数值 | `qudt:numericalValue` | `QUDT:numericValue` |
| 作者 | `provenance:AuthorName` | `provenance:hasAuthorName` |
| 数据库名 | `provenance:DatabaseName` | `provenance:hasDatabaseName` |
| DOI | `provenance:DOI` | `provenance:hasDOI` |
| 发布时间 | `provenance:PublicationDateTime` | `provenance:hasPublicationDateTime` |
| QUDT 前缀 | `qudt:` (小写) | `QUDT:` (大写, 同一 namespace) |

### 5.3 映射覆盖缺口

mp-mappings.rqg 从 75 个 JSON 字段中选取了约 15 个进行映射:

**已映射:** band_gap, final_energy, final_energy_per_atom, formation_energy_per_atom, density, full_formula, anonymous_formula, lattice (matrix/angles/lengths), sites (fractional/cartesian coordinates), spacegroup (symbol/number/point_group/crystal_system), authors, doi, created_at

**未映射但 CQ 需要:**
- computational method / software → CQ9, CQ10, CQ11, CQ13 失败
- encut, kpoints 等计算参数 → CQ10 失败

**未映射且 CQ 不涉及:** e_above_hull, efermi, is_hubbard, hubbards, magnetic_type, total_magnetization, is_compatible, decomposes_to, cohesive_energy, cpu_time 等约 60 个字段

### 5.4 CQ13 与 CQ11 重复

官方 SPARQL 文件中 CQ13 和 CQ11 的查询完全相同 (都查 `prov:wasAssociatedWith`)，但 requirements.md 中 CQ13 问的是 "When was the calculation data published"，应对应 CQ14 的查询。这可能是文件编号错位。

## 6. 我对 MDO 设计的评价

### 6.1 优点

1. **模块化设计清晰**: core/structure/calculation/provenance 四模块单向 import core，耦合度低
2. **PROV-O 复用**: 用 W3C 标准本体处理出处信息，是教科书级的 ontology reuse 实践
3. **QUDT 复用**: 物理量用 QUDT 表示 (QuantityValue + unit + numericValue)，语义标准化
4. **可执行映射**: 14 个 CQ + 4 个数据库的 SPARQL-Generate 映射，极少本体项目做到全链路可跑
5. **数据集随仓库发布**: 85 个 MP JSON + 预生成 TTL，降低复现门槛

### 6.2 弱点

1. **命名不一致严重**: OWL 定义、SPARQL 查询、映射输出三层属性名不统一 (详见第 5 节)，阻碍直接复现
2. **calculation 模块覆盖窄**: 只有 DFT 和 Hartree-Fock 两个分支，缺少 MD、Monte Carlo、微磁等方法
3. **structure 模块缺少缺陷描述**: 只能表达完美晶体，无法描述空位、间隙、位错等 (CMSO 在此处更强)
4. **无 SHACL 约束**: 只有 OWL axioms，没有 shape validation，无法在数据摄入时自动校验
5. **映射 vs CQ 覆盖不匹配**: 4 个 CQ (9/10/11/13) 在真实数据上跑不通，因为映射根本没生成对应三元组
6. **数据集偏窄**: 85 个材料全是 cubic Fm-3m 双钙钛矿，不能代表材料科学的多样性

### 6.3 给磁性扩展工作的启示

1. 属性命名必须在 OWL 定义阶段就和 mapping 对齐，避免三层 drift
2. mag-calculation 需要从一开始就映射 computational method 和 software，不能像 MDO 一样留空
3. 磁性属性 (Ms, Hc, Tc, MAE) 应沿用 QUDT 的 QuantityValue 模式
4. 应加入 SHACL shapes 做数据校验
5. 测试数据应覆盖多种晶体结构，不能只用一种空间群

## 7. 复现耗时

| 阶段 | 内容 | 耗时 |
|---|---|---|
| 0 | 环境搭建 | 10 分钟 |
| 1 | 加载浏览 4 个模块 | 15 分钟 |
| 2 | 14 个 CQ (测试 ABox) | 40 分钟 |
| 3 | 检查 mp-mappings.rqg + merged.ttl | 20 分钟 |
| 4 | 真实 MP 数据 CQ (rdflib 替代 Blazegraph) | 30 分钟 |
| 5 | Protege (待手动完成) | — |
| 6 | 本报告 | 30 分钟 |
| **总计** | | **约 2.5 小时** (不含 Protege) |

最大坑: 三层属性名不一致，需要反复对照 OWL 定义、SPARQL 文件、merged.ttl 实际数据来修正查询。

## 8. 文件清单

```
mdo-repro/
├── mdo/                          # clone 的 MDO 仓库
├── venv/                         # Python 虚拟环境
├── explore_modules.py            # 阶段 1: 模块骨架探索
├── test_abox.ttl                 # 阶段 2: 手写测试数据
├── run_cqs.py                    # 阶段 2: 14 个 CQ 跑批 (测试 ABox)
├── cq_results.json               # 阶段 2: 测试 ABox 查询结果
├── run_cqs_real.py               # 阶段 4: 14 个 CQ 跑批 (真实 MP 数据)
├── cq_results_real.json          # 阶段 4: 真实数据查询结果
├── REPRODUCE_REPORT.md           # 本报告
└── MDO_Reproduction_Handbook.md  # 操作手册
```
