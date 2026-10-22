"""
Generate Independent Multidisciplinary Holdout Benchmark Dataset for CiteGuard.

Dataset Properties:
  - 400 citations total.
  - 100 genuine citations (ground_truth = 0, error_type = 'valid').
  - 300 perturbed citations (ground_truth = 1), balanced across 5 error types:
      * corrupted_authors (60 citations, 15 per discipline)
      * wrong_venue (60 citations, 15 per discipline)
      * wrong_year (60 citations, 15 per discipline)
      * doi_mismatch (60 citations, 15 per discipline)
      * plausible_fabricated (60 citations, 15 per discipline)
  - 4 broad disciplines (100 citations per discipline = 25 valid + 75 perturbed):
      * computer_science
      * medicine_biomedical
      * natural_sciences
      * humanities_social_sciences
  - 100% disjoint from V1.0 and V2.0 benchmarks (zero overlapping DOIs or citation strings).
  - Provenance tracked for every citation: source_doi, donor_doi, original_field_value,
    mutated_field_value, mutation_rule, retrieval_date, provenance_source.
"""

import csv
import json
from pathlib import Path
import random
import re
from typing import Dict, List, Tuple


RANDOM_SEED = 20261015
random.seed(RANDOM_SEED)

HOLDOUT_DIR = Path(__file__).resolve().parent
SEEDS_FILE = HOLDOUT_DIR / "multidisciplinary_seed_papers.json"
DATASET_CSV = HOLDOUT_DIR / "independent_holdout_dataset.csv"

ERROR_TYPES = [
    "corrupted_authors",
    "wrong_venue",
    "wrong_year",
    "doi_mismatch",
    "plausible_fabricated",
]

FABRICATED_TEMPLATES = {
    "computer_science": [
        ("Scalable Zero-Knowledge Rollups for Distributed State Machine Replication",
         ["Marcus Vance", "Elena Rostova", "Hiroshi Tanaka"],
         2022, "IEEE Transactions on Dependable and Secure Computing"),
        ("Optimizing Distributed Consensus in Asynchronous High-Throughput Networks",
         ["Arthur Pendelton", "Siddharth Verma"],
         2021, "ACM Transactions on Computer Systems"),
        ("Formal Verification of Cryptographic Hardware Accelerators Against Side-Channel Attacks",
         ["Claire Dubois", "Julian Richter", "Wei Zhang"],
         2023, "IEEE Transactions on Information Forensics and Security"),
        ("Decentralized Key Exchange Protocols with Post-Quantum Forward Secrecy",
         ["Nadia Al-Mansoor", "Lukas Meyer"],
         2020, "Journal of Cryptology"),
        ("Adaptive Query Execution for Heterogeneous Multi-Cloud Relational Databases",
         ["Gabriel Santos", "Chloe Bennett", "Faisal Karim"],
         2021, "ACM Transactions on Database Systems"),
        ("Static Analysis of Concurrent Memory Models in Modern Systems Programming Languages",
         ["Thomas Lindqvist", "Priya Nair"],
         2022, "IEEE Transactions on Software Engineering"),
        ("Fault-Tolerant Byzantine State Replication with Dynamic Validator Reconfiguration",
         ["Dmitri Volkov", "Sarah Jenkins"],
         2019, "Distributed Computing"),
        ("Automated Synthesis of Provably Secure Microarchitectural Isolation Enclaves",
         ["Kenji Sato", "Hannah Abbott", "Matthias Becker"],
         2023, "IEEE Micro"),
        ("Energy-Efficient Packet Scheduling in Multi-Hop Wireless Edge Mesh Architectures",
         ["Rashid Khan", "Ananya Sen"],
         2020, "IEEE Transactions on Mobile Computing"),
        ("Provable Confidentiality in Cloud-Native Serverless Computing Fabrics",
         ["Benjamin Clark", "Yael Cohen"],
         2022, "Journal of Systems Architecture"),
        ("Dynamic Graph Indexing for Sub-Second Path Queries on Planetary-Scale Knowledge Networks",
         ["Zhiqiang Wu", "Miriam Goldstein"],
         2021, "VLDB Journal"),
        ("Resilient Cross-Chain Interoperability Protocols under Asynchronous Adversaries",
         ["Oliver Queen", "Stefan Novak"],
         2023, "IEEE Transactions on Network and Service Management"),
        ("Automated Detection of Speculative Execution Side Channels in Cryptographic Libraries",
         ["Fatima Zahra", "Geoffrey Hayes"],
         2022, "ACM Transactions on Privacy and Security"),
        ("High-Performance Columnar Compression for Distributed Analytical Workloads",
         ["Lucas Rossi", "Kavita Rao"],
         2020, "Information Systems"),
        ("Hierarchical Multi-Party Computation for Privacy-Preserving Collaborative Auditing",
         ["Patrick O'Connor", "Sunita Sharma", "Jonas Lind"],
         2021, "IEEE Transactions on Services Computing"),
    ],
    "medicine_biomedical": [
        ("Multi-Targeted Kinase Inhibition in Refractory Pancreatic Adenocarcinoma: A Phase III Trial",
         ["Eleanor Campbell", "David Rosenbaum", "Beatriz Morales"],
         2021, "The Lancet Oncology"),
        ("Long-Term Clinical Outcomes of SGLT2 Inhibition in Advanced Heart Failure with Preserved Ejection Fraction",
         ["Gareth Edwards", "Sunita Patel", "Fritz Schneider"],
         2022, "New England Journal of Medicine"),
        ("Genome-Wide Epigenetic Profiling Identifies Novel Therapeutic Vulnerabilities in Glioblastoma Multiforme",
         ["Maria S. Rodriguez", "Christian Hoffmann"],
         2020, "Cancer Cell"),
        ("Safety and Efficacy of Dual Immune Checkpoint Blockade in Recurrent Metastatic Melanoma",
         ["Alexander Wright", "Jasmine Taylor", "Li Wei"],
         2023, "Journal of Clinical Oncology"),
        ("Monoclonal Antibody Targeting Tau Aggregation in Mild Cognitive Impairment: A Randomized Controlled Trial",
         ["Robert Sterling", "Katarina Novak"],
         2021, "JAMA Neurology"),
        ("Early Coronary Intravascular Lithotripsy versus Rotational Atherectomy in Severely Calcified Lesions",
         ["Matteo Moretti", "Grace Kelly", "Hassan Farouk"],
         2022, "Circulation"),
        ("Single-Cell Transcriptomics Reveals Lineage Plasticity in Acquired Chemoresistance of Small Cell Lung Cancer",
         ["Dominic Shaw", "Ying Chen"],
         2023, "Nature Medicine"),
        ("Comparative Effectiveness of Direct Oral Anticoagulants in Cirrhotic Portal Vein Thrombosis",
         ["Claire Fontaine", "Rajesh Gupta"],
         2020, "Hepatology"),
        ("Metabolic Reprogramming and T-Cell Exhaustion in the Chronic Autoimmune Microenvironment",
         ["Hannah Davies", "Lars Sorensen", "Mei-Ling Zhou"],
         2021, "Journal of Experimental Medicine"),
        ("Efficacy of Oral Janus Kinase-1 Inhibitors in Refractory Moderate-to-Severe Atopic Dermatitis",
         ["Simon Fletcher", "Amara Okonkwo"],
         2022, "British Journal of Dermatology"),
        ("Precision Antimicrobial Stewardship Guided by Rapid Multiplex Metagenomic Sequencing in Sepsis",
         ["Paulina Vega", "Tobias Krause"],
         2021, "Critical Care Medicine"),
        ("Endoscopic Submucosal Dissection versus Laparoscopic Resection for Early Gastric Neoplasms",
         ["Kenichi Takahashi", "Sophie Martin"],
         2020, "Gastrointestinal Endoscopy"),
        ("Biological Biomarkers of Acute Kidney Injury Following Cardiopulmonary Bypass in Neonatal Surgery",
         ["Nils Lindgren", "Amina El-Sayed"],
         2023, "Pediatric Nephrology"),
        ("Therapeutic Efficacy of Engineered Allogeneic CAR-NK Cells in Relapsed B-Cell Lymphoma",
         ["Victoria Adams", "Javier Hernandez"],
         2022, "Blood"),
        ("Systemic Microvascular Dysfunction and Cerebral Perfusion Heterogeneity in Post-Viral Fatigue Syndromes",
         ["Gregory Bell", "Rachel Zimmerman"],
         2023, "Annals of Internal Medicine"),
    ],
    "natural_sciences": [
        ("High-Pressure Synthesis and Superconducting Properties of Ternary Lanthanum-Yttrium Superhydrides",
         ["Viktor Petrov", "Svetlana Ivanova", "Heinrich Weber"],
         2022, "Physical Review Letters"),
        ("Spectroscopic Characterization of Hydrothermal Vent Geochemistry on Saturnian Moon Enceladus",
         ["Evelyn Marsh", "Alan Sterling", "Cynthia Vance"],
         2021, "The Astrophysical Journal"),
        ("Atomically Precise Synthesis of Graphene Nanoribbons with Tailored Topological Boundary States",
         ["Maximilian Braun", "Linette Dubois"],
         2020, "Nature Chemistry"),
        ("Centennial Dynamics of Antarctic Ice Shelf Calving Driven by Sub-Surface Ocean Thermal Forcing",
         ["Einar Thorne", "Kristin Hansen"],
         2022, "Nature Climate Change"),
        ("Chiral Phonon-Induced Spin Polarization in Two-Dimensional Halide Perovskite Superlattices",
         ["Takeshi Okamoto", "Darren Hughes"],
         2023, "Journal of the American Chemical Society"),
        ("High-Energy Neutrino Emission Associated with Extreme Tidal Disruption Events in Active Galaxies",
         ["Laura Castelli", "Felix Baumgartner"],
         2021, "Monthly Notices of the Royal Astronomical Society"),
        ("Catalytic Cleavage of Carbon-Oxygen Bonds in Lignin Models via Single-Site Ruthenium Pincer Complexes",
         ["Guillaume Laurent", "Yuki Morita"],
         2020, "Inorganic Chemistry"),
        ("Topological Quantum Phase Transitions in Frustrated Kitaev Quantum Spin Liquids",
         ["Bjoern Lindberg", "Anika Patel"],
         2022, "Physical Review B"),
        ("Isotopic Fractionation of Magnesium in Ancient Zircon Crystals and Early Crustal Differentiation",
         ["Samuel Higgins", "Fiona Gallagher"],
         2021, "Geochimica et Cosmochimica Acta"),
        ("Ultrafast Dynamics of Exciton-Plasmon Polaritons in Atomically Thin Transition Metal Dichalcogenides",
         ["Andrea Vitali", "Mei-Chun Huang"],
         2023, "ACS Nano"),
        ("Atmospheric Photochemical Production of Reactive Nitrogen Intermediates in Tropical Rainforest Canopies",
         ["Oliver Vance", "Ingrid Bergman"],
         2020, "Atmospheric Chemistry and Physics"),
        ("Non-Equilibrium Phase Separation in Synthetic Multicomponent Coacervate Micro-Droplets",
         ["Antoine Dupont", "Clara Schmidt"],
         2022, "Macromolecules"),
        ("Constraining Dark Matter Halo Profiles in Dwarf Spheroidal Galaxies with Stellar Kinematic Tracer Dispersion",
         ["Declan Fraser", "Tara Campbell"],
         2021, "Astronomy & Astrophysics"),
        ("Mechanistic Insights into Low-Temperature Electrochemical Carbon Dioxide Reduction on Bimetallic Catalysts",
         ["Soren Kierkegaard", "Zhenyu Liu"],
         2023, "Energy & Environmental Science"),
        ("Deep Hydrogeological Cycling and Noble Gas Signatures in Cratonic Crystalline Basements",
         ["Morgan Reese", "Leila Hosseini"],
         2020, "Earth and Planetary Science Letters"),
    ],
    "humanities_social_sciences": [
        ("Monetary Shocks, Heterogeneous Wealth Portfolios, and Inequality in Post-Crisis Economies",
         ["Julian Sterling", "Mathilde Caron"],
         2021, "Quarterly Journal of Economics"),
        ("Executive Function, Working Memory Depletion, and Moral Decision-Making across the Lifespan",
         ["Clara Van Der Meer", "Richard Alvarez"],
         2022, "Cognitive Psychology"),
        ("Labor Market Polarization, Automation Vulnerability, and Populist Voting Behavior in Post-Industrial Regions",
         ["Stephen H. Miller", "Annette Dubois"],
         2020, "American Sociological Review"),
        ("Phonological Salience and Morphosyntactic Restructuring in Contact-Induced Creolization",
         ["Valerie Beaumont", "Kofi Mensah"],
         2021, "Language"),
        ("Institutional Persistence, Land Tenure Reform, and Long-Term Educational Attainment in Post-Colonial States",
         ["Carlos M. Ramirez", "Gillian Fletcher"],
         2022, "Journal of Development Economics"),
        ("Cognitive Biases in Algorithmic Decision-Making: Anchoring Effects in Judicial Risk Assessment Tools",
         ["Daphne Robinson", "Nils Lindqvist"],
         2023, "Behavioral Science & Policy"),
        ("Social Capital Networks and Intergenerational Income Mobility in Metropolitan Statistical Areas",
         ["Jonathan P. Vance", "Elena Rossi"],
         2020, "American Economic Journal: Applied Economics"),
        ("The Rhetoric of Parliamentary Sovereign Immunity: Constitutional Discourse in Late-Eighteenth Century Britain",
         ["Alistair Ward", "Madeleine Lefebvre"],
         2021, "The Historical Journal"),
        ("Grammatical Aspect and Event Representation: Cross-Linguistic Evidence from Eye-Tracking in Visual Narratives",
         ["Svetlana Popova", "Marc Dupuis"],
         2022, "Journal of Memory and Language"),
        ("Bureaucratic Discretion and Welfare Sanctioning: An Audit Study of Frontline Caseworker Evaluations",
         ["Hanneke De Vries", "Liam O'Connor"],
         2023, "Journal of Public Administration Research and Theory"),
        ("Spatial Sorting and Residential Segregation under Heterogeneous School Choice Mechanisms",
         ["Eduardo Silva", "Miriam Cohen"],
         2020, "Journal of Urban Economics"),
        ("The Psychological Consequences of Precarious Employment: A Ten-Year Multi-Wave Longitudinal Cohort Study",
         ["Brigitte Schneider", "Aaron Patel"],
         2021, "Journal of Applied Psychology"),
        ("Linguistic Distance, Trade Friction, and Cultural Affinity in Bilateral Services Offshoring",
         ["Pascal Girard", "Chen-Yu Lin"],
         2022, "World Development"),
        ("Collective Memory and Institutional Commemoration of Traumatic Historical Events in Transitional Societies",
         ["Teresa Mendez", "Boris Krumov"],
         2023, "Theory and Society"),
        ("Temporal Discounting and Environmental Conservation Decisions under Knightian Uncertainty",
         ["Duncan Forbes", "Yael Ben-David"],
         2020, "Journal of Environmental Economics and Management"),
    ],
}


def clean_text(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", str(s))
    return " ".join(s.replace("\n", " ").replace("\r", " ").split()).strip()


def normalize_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = str(doi).strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi.strip().lower()


def format_authors(authors: List[str]) -> str:
    return "; ".join(authors)


def format_citation(title: str, authors: List[str], year: int, venue: str, doi: str) -> str:
    return (
        f'Title: "{title}"\n'
        f"Authors: {format_authors(authors)}\n"
        f"Year: {year}\n"
        f"Venue: {venue}\n"
        f"DOI: {doi}"
    )


def generate_holdout_dataset():
    with open(SEEDS_FILE, "r", encoding="utf-8") as f:
        all_seeds = json.load(f)

    # Group seeds by discipline
    seeds_by_disc = {}
    for seed in all_seeds:
        disc = seed["discipline"]
        seeds_by_disc.setdefault(disc, []).append(seed)

    records = []
    current_id = 1

    disciplines = [
        "computer_science",
        "medicine_biomedical",
        "natural_sciences",
        "humanities_social_sciences",
    ]

    for disc in disciplines:
        disc_seeds = seeds_by_disc[disc]
        assert len(disc_seeds) == 25, f"Discipline {disc} must have exactly 25 seeds, got {len(disc_seeds)}"

        # 1. Generate 25 Genuine (valid) Citations
        for seed in disc_seeds:
            citation_str = format_citation(
                seed["title"], seed["authors"], seed["year"], seed["venue"], seed["doi"]
            )
            records.append({
                "id": current_id,
                "discipline": disc,
                "citation": citation_str,
                "ground_truth": 0,
                "error_type": "valid",
                "source_doi": seed["doi"],
                "donor_doi": "",
                "original_field_value": "",
                "mutated_field_value": "",
                "mutation_rule": "genuine_traceable_seed",
                "retrieval_date": seed["retrieval_date"],
                "provenance_source": seed["source"],
            })
            current_id += 1

        # 2. Generate 75 Perturbed Citations across the 5 Error Categories
        # Each seed gets exactly 3 perturbations: (i)%5, (i+1)%5, (i+2)%5
        # Each error category will appear exactly 15 times per discipline.
        fab_templates = FABRICATED_TEMPLATES[disc]
        fab_idx = 0

        for seed_idx, seed in enumerate(disc_seeds):
            assigned_errors = [
                ERROR_TYPES[(seed_idx + 0) % 5],
                ERROR_TYPES[(seed_idx + 1) % 5],
                ERROR_TYPES[(seed_idx + 2) % 5],
            ]

            for err in assigned_errors:
                if err == "corrupted_authors":
                    # Donor search within discipline
                    donor_found = False
                    for offset in range(1, 25):
                        donor = disc_seeds[(seed_idx + offset) % 25]
                        source_first = clean_text(seed["authors"][0]) if seed["authors"] else ""
                        donor_first = clean_text(donor["authors"][0]) if donor["authors"] else ""
                        if source_first.lower() != donor_first.lower():
                            mutated_authors = list(seed["authors"])
                            mutated_authors[0] = donor_first
                            orig_str = format_authors(seed["authors"])
                            mut_str = format_authors(mutated_authors)
                            assert orig_str != mut_str
                            cit = format_citation(seed["title"], mutated_authors, seed["year"], seed["venue"], seed["doi"])
                            records.append({
                                "id": current_id,
                                "discipline": disc,
                                "citation": cit,
                                "ground_truth": 1,
                                "error_type": "corrupted_authors",
                                "source_doi": seed["doi"],
                                "donor_doi": donor["doi"],
                                "original_field_value": orig_str,
                                "mutated_field_value": mut_str,
                                "mutation_rule": f"first_author_substitution (donor={donor['doi']})",
                                "retrieval_date": seed["retrieval_date"],
                                "provenance_source": seed["source"],
                            })
                            current_id += 1
                            donor_found = True
                            break
                    assert donor_found, f"Could not find author donor for {seed['doi']}"

                elif err == "wrong_venue":
                    donor_found = False
                    for offset in range(1, 25):
                        donor = disc_seeds[(seed_idx + offset) % 25]
                        source_v = clean_text(seed["venue"])
                        donor_v = clean_text(donor["venue"])
                        if source_v.lower() != donor_v.lower():
                            cit = format_citation(seed["title"], seed["authors"], seed["year"], donor_v, seed["doi"])
                            records.append({
                                "id": current_id,
                                "discipline": disc,
                                "citation": cit,
                                "ground_truth": 1,
                                "error_type": "wrong_venue",
                                "source_doi": seed["doi"],
                                "donor_doi": donor["doi"],
                                "original_field_value": source_v,
                                "mutated_field_value": donor_v,
                                "mutation_rule": f"venue_substitution (donor={donor['doi']})",
                                "retrieval_date": seed["retrieval_date"],
                                "provenance_source": seed["source"],
                            })
                            current_id += 1
                            donor_found = True
                            break
                    assert donor_found, f"Could not find venue donor for {seed['doi']}"

                elif err == "wrong_year":
                    orig_year = seed["year"]
                    if orig_year % 2 == 0:
                        mut_year = orig_year + 5
                    else:
                        mut_year = orig_year - 5
                    if mut_year < 1995:
                        mut_year = orig_year + 6
                    if mut_year > 2024:
                        mut_year = orig_year - 6
                    assert mut_year != orig_year

                    cit = format_citation(seed["title"], seed["authors"], mut_year, seed["venue"], seed["doi"])
                    records.append({
                        "id": current_id,
                        "discipline": disc,
                        "citation": cit,
                        "ground_truth": 1,
                        "error_type": "wrong_year",
                        "source_doi": seed["doi"],
                        "donor_doi": "",
                        "original_field_value": str(orig_year),
                        "mutated_field_value": str(mut_year),
                        "mutation_rule": "year_shift_plus_minus_five",
                        "retrieval_date": seed["retrieval_date"],
                        "provenance_source": seed["source"],
                    })
                    current_id += 1

                elif err == "doi_mismatch":
                    donor_found = False
                    for offset in range(1, 25):
                        donor = disc_seeds[(seed_idx + offset) % 25]
                        if donor["doi"] != seed["doi"]:
                            cit = format_citation(seed["title"], seed["authors"], seed["year"], seed["venue"], donor["doi"])
                            records.append({
                                "id": current_id,
                                "discipline": disc,
                                "citation": cit,
                                "ground_truth": 1,
                                "error_type": "doi_mismatch",
                                "source_doi": seed["doi"],
                                "donor_doi": donor["doi"],
                                "original_field_value": seed["doi"],
                                "mutated_field_value": donor["doi"],
                                "mutation_rule": f"doi_substitution (donor={donor['doi']})",
                                "retrieval_date": seed["retrieval_date"],
                                "provenance_source": seed["source"],
                            })
                            current_id += 1
                            donor_found = True
                            break
                    assert donor_found, f"Could not find DOI donor for {seed['doi']}"

                elif err == "plausible_fabricated":
                    t_title, t_authors, t_year, t_venue = fab_templates[fab_idx % len(fab_templates)]
                    fab_doi = f"10.9999/citeguard.holdout.{disc}.{fab_idx + 1:03d}"
                    fab_idx += 1
                    cit = format_citation(t_title, t_authors, t_year, t_venue, fab_doi)
                    records.append({
                        "id": current_id,
                        "discipline": disc,
                        "citation": cit,
                        "ground_truth": 1,
                        "error_type": "plausible_fabricated",
                        "source_doi": fab_doi,
                        "donor_doi": "",
                        "original_field_value": "",
                        "mutated_field_value": "completely_fabricated_citation",
                        "mutation_rule": "discipline_tailored_plausible_fabrication",
                        "retrieval_date": seed["retrieval_date"],
                        "provenance_source": "synthetic_generation",
                    })
                    current_id += 1

    # Final sanity checks
    assert len(records) == 400, f"Expected 400 records, got {len(records)}"

    fieldnames = [
        "id",
        "discipline",
        "citation",
        "ground_truth",
        "error_type",
        "source_doi",
        "donor_doi",
        "original_field_value",
        "mutated_field_value",
        "mutation_rule",
        "retrieval_date",
        "provenance_source",
    ]

    with open(DATASET_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"\n[SUCCESS] Generated independent holdout dataset: {DATASET_CSV}")
    print(f"Total Records: {len(records)}")


if __name__ == "__main__":
    generate_holdout_dataset()
