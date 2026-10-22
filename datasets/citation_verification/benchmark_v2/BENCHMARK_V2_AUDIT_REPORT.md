# CiteGuard Benchmark V2.0 Audit & Delta Report

**Generated**: Automated controlled comparison against frozen V1.0 baseline.

## 1. Summary of Changes
- **Total Benchmark Records**: 600
- **Unchanged Records from V1.0**: 576 (96.0%)
- **Repaired No-Op Records**: 24 (Exact 1-to-1 match with the 24 audited no-op records)
- **Cross-Label Collisions in V2.0**: 0 (eliminated)
- **No-Op Perturbations in V2.0**: 0 (eliminated)

## 2. Row-Level Delta Table (The 24 Repaired Records)

| V2 ID | V1 ID | Category | Source DOI | Donor DOI | Original Field | Mutated Field | Mutation Rule |
|:---:|:---:|:---:|:---|:---|:---|:---|:---|
| 2 | 258 | `corrupted_authors` | `10.1007/979-8-8688-1017-6_6` | `10.1201/9781032690742-9` | Abdelaziz Testas | Mehdi Ghayoumi | `first_author_substitution (offset=2)` |
| 16 | 252 | `corrupted_authors` | `10.1007/978-1-4842-6431-7_2` | `10.1007/978-1-4842-5364-9_8` | Thimira Amaratunga | Nikhil Ketkar | `first_author_substitution (offset=2)` |
| 362 | 209 | `corrupted_authors` | `10.1023/a:1022647305786` | `10.1023/a:1022817027844` | Pat Langley | David Haussler | `first_author_substitution (offset=2)` |
| 387 | 267 | `corrupted_authors` | `10.1006/cviu.2000.0835` | `10.1016/j.nlp.2022.100001` | Azriel Rosenfeld | Xieling Chen | `first_author_substitution (offset=2)` |
| 399 | 219 | `corrupted_authors` | `10.1023/a:1022689616458` | `10.5772/9374` | Pat Langley | Taiwo Oladipupo | `first_author_substitution (offset=2)` |
| 407 | 287 | `corrupted_authors` | `10.1007/978-981-97-9739-4_20` | `10.5715/jnlp.27.963` | Huaping Zhang; Jianyun Sh | Daichi Mochihashi; Jianyu | `first_author_substitution (offset=2)` |
| 494 | 208 | `corrupted_authors` | `10.1023/a:1022603230145` | `10.1023/a:1022817027844` | Pat Langley | David Haussler | `first_author_substitution (offset=3)` |
| 39 | 498 | `wrong_venue` | `10.1016/0004-3702(76)90004-7` | `10.1093/oso/9780198828044.003.0003` | Artificial Intelligence | Fundamentals of Machine L | `venue_substitution (offset=3)` |
| 177 | 487 | `wrong_venue` | `10.1007/978-981-97-9739-4_20` | `10.5715/jnlp.27.963` | Natural Language Processi | Journal of Natural Langua | `venue_substitution (offset=2)` |
| 194 | 404 | `wrong_venue` | `10.1023/a:1022896407371` | `10.1201/9781003606055-5` | Machine Learning | Soft Computing and Machin | `venue_substitution (offset=9)` |
| 218 | 467 | `wrong_venue` | `10.1006/cviu.2000.0835` | `10.1016/j.nlp.2022.100001` | Computer Vision and Image | Natural Language Processi | `venue_substitution (offset=2)` |
| 241 | 499 | `wrong_venue` | `10.1016/s0004-3702(03)00055-9` | `10.1093/oso/9780198828044.003.0003` | Artificial Intelligence | Fundamentals of Machine L | `venue_substitution (offset=2)` |
| 252 | 405 | `wrong_venue` | `10.1023/a:1022665512030` | `10.1201/9781003606055-5` | Machine Learning | Soft Computing and Machin | `venue_substitution (offset=8)` |
| 258 | 406 | `wrong_venue` | `10.1023/a:1022854429410` | `10.1201/9781003606055-5` | Machine Learning | Soft Computing and Machin | `venue_substitution (offset=7)` |
| 331 | 494 | `wrong_venue` | `10.1016/0004-3702(86)90034-2` | `10.1186/s40364-024-00557-1` | Artificial Intelligence | Biomarker Research | `venue_substitution (offset=2)` |
| 378 | 458 | `wrong_venue` | `10.1007/979-8-8688-1017-6_6` | `10.1201/9781032690742-9` | Building Scalable Deep Le | Mathematical Foundations  | `venue_substitution (offset=2)` |
| 403 | 479 | `wrong_venue` | `10.1016/j.nlp.2025.100137` | `10.1093/oxfordhb/9780199276349.013.0037` | Natural Language Processi | Oxford Handbooks Online | `venue_substitution (offset=2)` |
| 411 | 411 | `wrong_venue` | `10.1023/a:1022817027844` | `10.1201/9781003606055-5` | Machine Learning | Soft Computing and Machin | `venue_substitution (offset=2)` |
| 432 | 452 | `wrong_venue` | `10.1007/978-1-4842-6431-7_2` | `10.1007/978-1-4842-5364-9_8` | Deep Learning on Windows | Deep Learning with Python | `venue_substitution (offset=2)` |
| 472 | 408 | `wrong_venue` | `10.1023/a:1022603230145` | `10.1201/9781003606055-5` | Machine Learning | Soft Computing and Machin | `venue_substitution (offset=5)` |
| 474 | 407 | `wrong_venue` | `10.1023/a:1022661713654` | `10.1201/9781003606055-5` | Machine Learning | Soft Computing and Machin | `venue_substitution (offset=6)` |
| 513 | 419 | `wrong_venue` | `10.1023/a:1022689616458` | `10.5772/9374` | Machine Learning | New Advances in Machine L | `venue_substitution (offset=2)` |
| 543 | 410 | `wrong_venue` | `10.1023/a:1022840627593` | `10.1201/9781003606055-5` | Machine Learning | Soft Computing and Machin | `venue_substitution (offset=3)` |
| 550 | 409 | `wrong_venue` | `10.1023/a:1022647305786` | `10.1201/9781003606055-5` | Machine Learning | Soft Computing and Machin | `venue_substitution (offset=4)` |

## 3. Invariance & Preservation Audit
- **Category 1 (Valid)**: 100/100 records identical to V1.0.
- **Category 2 (DOI Mismatch)**: 100/100 records identical to V1.0.
- **Category 4 (Wrong Year)**: 100/100 records identical to V1.0.
- **Category 6 (Plausible Fabricated)**: 100/100 records identical to V1.0.
- **Category 3 (Corrupted Authors)**: Exactly 93 records identical, exactly 7 no-ops repaired.
- **Category 5 (Wrong Venue)**: Exactly 83 records identical, exactly 17 no-ops repaired.

## 4. Hard Path Guard Certification
- No V1.0 camera-ready files were accessed in write mode.
- All outputs strictly confined to `datasets/citation_verification/benchmark_v2/`.