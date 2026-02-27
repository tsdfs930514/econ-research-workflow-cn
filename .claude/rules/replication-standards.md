---
paths:
  - "**/REPLICATION.md"
  - "**/master.do"
  - "**/docs/**"
---

# Replication Standards

Standards for creating reproducible research following AEA Data Editor guidelines and TOP5 journal best practices.

---

## Data Provenance

### Data Availability Statement

Every replication package must include a clear statement:
- Which data are publicly available and where
- Which data are restricted and how to obtain access
- Which data are confidential and cannot be shared

### Data Documentation

For each raw data file, document in REPLICATION.md:

| Element | Description |
|---------|-------------|
| **File name** | Exact filename in `data/raw/` |
| **Source** | Original provider (e.g., NBER, Census, firm website) |
| **Date accessed** | When the file was downloaded |
| **DOI/URL** | Persistent identifier or direct download link |
| **License** | Usage restrictions (public domain, academic use only, etc.) |
| **MD5/SHA256** | File hash to verify integrity |
| **Size** | File size (for planning storage) |

### Data Processing Documentation

Create a `data_dictionary.md` documenting:
- Variable names and descriptions
- Units of measurement
- Coding schemes (e.g., 1=male, 2=female)
- Missing value codes
- Known data quality issues

---

## Code Organization

### Directory Structure

```
vN/
├── code/
│   ├── stata/
│   │   ├── master.do           # Entry point — runs everything
│   │   ├── 01_clean_data.do    # Data preparation
│   │   ├── 02_desc_stats.do    # Descriptive statistics
│   │   ├── 03_main_analysis.do # Main results
│   │   ├── 04_robustness.do    # Robustness checks
│   │   └── 05_tables_figures.do # Output generation
│   └── python/
│       └── cross_validation.py  # Validates Stata results
├── data/
│   ├── raw/                    # Original data (READ-ONLY)
│   └── clean/                  # Processed data
├── output/
│   ├── tables/                 # LaTeX tables
│   ├── figures/                # PDF figures
│   └── logs/                   # Execution logs
└── REPLICATION.md              # Instructions
```

### Master Script Pattern

The `master.do` file must:
1. Set all paths via globals
2. Create output directories if they don't exist
3. Install required packages (commented out, with instructions)
4. Run all scripts in correct order
5. Verify that expected outputs were created

See `init-project.md` for the full template.

### Script Numbering

Use numbered prefixes to indicate execution order:
- `01_` — Data cleaning and preparation
- `02_` — Descriptive statistics
- `03_` — Main analysis
- `04_` — Robustness checks
- `05_` — Tables and figures export
- `06_` — Cross-validation (Python)

---

## Software Environment

### Stata Requirements

Document in REPLICATION.md:
- Stata version (e.g., "Stata 18/MP")
- Required packages with installation commands
- Approximate runtime

```stata
* Required Stata packages:
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
* ... (full list in econometrics-standards.md)
```

### Python Requirements

Create `requirements.txt`:

```
pandas==2.1.0
pyfixest==0.18.0
numpy==1.26.0
matplotlib==3.8.0
```

### Version Pinning

Pin exact versions for critical packages to ensure reproducibility. Update versions only after testing.

---

## Output Verification

### Table-to-Script Mapping

In REPLICATION.md, create a table mapping each output to its generating script:

| Table/Figure | Script | Output File | Line in Script |
|-------------|--------|-------------|----------------|
| Table 1 | `02_desc_stats.do` | `output/tables/tab_descriptive.tex` | Line 45 |
| Table 2 | `03_main_analysis.do` | `output/tables/tab_main_results.tex` | Line 78 |
| Figure 1 | `05_tables_figures.do` | `output/figures/fig_event_study.pdf` | Line 120 |

### Output Checksums

For critical outputs, record MD5 hashes to detect unintended changes:

```bash
md5sum output/tables/*.tex output/figures/*.pdf > output_checksums.txt
```

---

## Cross-Platform Compatibility

### Path Handling

Use forward slashes in Stata (works on all platforms):
```stata
save "data/clean/panel.dta", replace  ✓
save "data\clean\panel.dta", replace  ✗
```

### Random Seeds

Always set seeds for reproducibility:
```stata
set seed 12345
```

### Sorting

When results depend on sort order (e.g., `by` operations), explicitly sort:
```stata
sort panel_id year
by panel_id: gen lag_y = y[_n-1]
```

---

## Confidential Data Handling

### When Data Cannot Be Shared

If data are confidential:
1. Provide detailed synthetic data that mimics the structure
2. Document exactly how to obtain the real data
3. Provide code that runs on both real and synthetic data
4. In README, clearly state: "This replication package uses synthetic data. Real data available under [conditions]."

### Synthetic Data Generation

Use `syn` package in Stata or Python's `synthpop` to generate synthetic data that preserves:
- Variable distributions
- Correlation structure
- Panel structure (if applicable)

Do NOT preserve:
- Exact values (to protect confidentiality)
- Rare combinations that could identify individuals

---

## README Template

Every replication package should have a top-level README.md:

```markdown
# Replication Package for "[Paper Title]"

## Authors
[Author names]

## Paper Abstract
[2-3 sentence abstract]

## Data Availability
[Which data are public/restricted/confidential]

## Computational Requirements
- Stata 18/MP (required)
- Python 3.10+ with packages listed in requirements.txt (optional, for cross-validation)

## Runtime
Approximately [X] minutes on [machine description]

## Instructions
1. Install required Stata packages (see code/stata/master.do header)
2. Place raw data files in data/raw/ (see REPLICATION.md for sources)
3. Run code/stata/master.do
4. Check output/logs/ for any errors

## Output
All tables and figures from the paper are generated in output/tables/ and output/figures/

## Contact
[Corresponding author email]
```

---

## Quality Checklist

Before submitting a replication package, verify:

- [ ] All raw data documented with sources and access dates
- [ ] master.do runs from start to finish without errors
- [ ] All expected output files are created
- [ ] Output files match the paper's tables/figures
- [ ] README.md and REPLICATION.md are complete
- [ ] Code is commented and follows naming conventions
- [ ] Random seeds are set for all stochastic operations
- [ ] No absolute paths in code (use globals)
- [ ] No passwords or API keys in code
- [ ] Data dictionary documents all variables
- [ ] Synthetic data provided if real data are confidential

---

## AEA Data Editor Best Practices

Following the American Economic Association Data Editor's guidelines:

1. **One command to run everything**: A single master script should reproduce all results.
2. **Clean separation**: Raw data should never be modified; all outputs go to clean/temp folders.
3. **Minimal manual intervention**: No "uncomment this line" or "run sections 1-3 first" instructions.
4. **Complete documentation**: Every data source, every assumption, every transformation documented.
5. **Test on a clean machine**: Before submission, test the replication package on a fresh computer.
