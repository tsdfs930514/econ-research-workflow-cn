#!/usr/bin/env python3
"""
Quality Scorer for Econ Research Workflow
=========================================

Scores a version directory on 6 dimensions (100 points total):
  - Code conventions    (15 pts)
  - Log cleanliness     (15 pts)
  - Output completeness (15 pts)
  - Cross-validation    (15 pts)
  - Documentation       (15 pts)
  - Method diagnostics  (25 pts)

Usage:
  python scripts/quality_scorer.py v1/
  python scripts/quality_scorer.py v1/ --json
  python scripts/quality_scorer.py v1/ --verbose
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def find_files(base: Path, pattern: str) -> list[Path]:
    """Recursively find files matching a glob pattern."""
    return sorted(base.rglob(pattern))


def read_text(path: Path) -> str:
    """Read file text, return empty string on failure."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return ""


# ---------------------------------------------------------------------------
# Dimension 1: Code Conventions (15 pts)
# ---------------------------------------------------------------------------

def score_code_conventions(base: Path, verbose: bool = False) -> dict:
    """Check .do file headers, set seed, naming, logging pattern, vce(cluster)."""
    do_files = find_files(base, "*.do")
    py_files = find_files(base / "code", "*.py") if (base / "code").exists() else []

    if not do_files and not py_files:
        return {"score": 0, "max": 15, "details": ["No code files found"]}

    checks = {
        "headers_present": {"pass": 0, "fail": 0, "details": []},
        "set_seed": {"pass": 0, "fail": 0, "details": []},
        "numbered_naming": {"pass": 0, "fail": 0, "details": []},
        "log_pattern": {"pass": 0, "fail": 0, "details": []},
        "vce_cluster": {"pass": 0, "fail": 0, "details": []},
    }

    for f in do_files:
        content = read_text(f)
        name = f.name

        # Header check
        if "Project:" in content and "Purpose:" in content:
            checks["headers_present"]["pass"] += 1
        else:
            checks["headers_present"]["fail"] += 1
            checks["headers_present"]["details"].append(f"Missing header: {name}")

        # set seed
        if "set seed" in content.lower():
            checks["set_seed"]["pass"] += 1
        else:
            checks["set_seed"]["fail"] += 1
            checks["set_seed"]["details"].append(f"No set seed: {name}")

        # Numbered naming
        if re.match(r"^\d{2}_", name) or name == "master.do":
            checks["numbered_naming"]["pass"] += 1
        else:
            checks["numbered_naming"]["fail"] += 1
            checks["numbered_naming"]["details"].append(f"Not numbered: {name}")

        # Log pattern
        has_cap_log = "cap log close" in content or "capture log close" in content
        has_log_using = "log using" in content
        if has_cap_log and has_log_using:
            checks["log_pattern"]["pass"] += 1
        else:
            checks["log_pattern"]["fail"] += 1
            checks["log_pattern"]["details"].append(f"Missing log pattern: {name}")

        # vce(cluster)
        if "vce(cluster" in content or "vce(cl " in content:
            checks["vce_cluster"]["pass"] += 1
        elif re.search(r"(reghdfe|regress|xtreg|ivreghdfe|ivreg2)", content):
            checks["vce_cluster"]["fail"] += 1
            checks["vce_cluster"]["details"].append(f"Regression without vce(cluster): {name}")
        else:
            checks["vce_cluster"]["pass"] += 1  # No regressions in this file

    # Score: 3 pts per check, weighted by pass rate
    total = 0
    details = []
    for check_name, check_data in checks.items():
        total_files = check_data["pass"] + check_data["fail"]
        if total_files > 0:
            rate = check_data["pass"] / total_files
            pts = round(rate * 3, 1)
        else:
            rate = 1.0
            pts = 3.0
        total += pts
        if verbose and check_data["details"]:
            details.extend(check_data["details"])

    return {"score": min(round(total), 15), "max": 15, "details": details}


# ---------------------------------------------------------------------------
# Dimension 2: Log Cleanliness (15 pts)
# ---------------------------------------------------------------------------

def score_log_cleanliness(base: Path, verbose: bool = False) -> dict:
    """Check .log files for r(xxx) errors, variable not found, command not found."""
    log_files = find_files(base, "*.log")

    if not log_files:
        return {"score": 0, "max": 15, "details": ["No .log files found"]}

    error_patterns = [
        (r"r\(\d+\)", "Stata error"),
        (r"variable .+ not found", "Variable not found"),
        (r"command .+ is unrecognized", "Command not recognized"),
        (r"no observations", "No observations"),
    ]

    clean_logs = 0
    total_logs = len(log_files)
    details = []

    for f in log_files:
        content = read_text(f)
        errors_found = []
        for pattern, label in error_patterns:
            matches = re.findall(pattern, content)
            if matches:
                errors_found.append(f"{label}: {len(matches)} occurrence(s)")
        if errors_found:
            details.append(f"{f.name}: {'; '.join(errors_found)}")
        else:
            clean_logs += 1

    if total_logs > 0:
        rate = clean_logs / total_logs
        score = round(rate * 15)
    else:
        score = 0

    return {"score": score, "max": 15, "details": details}


# ---------------------------------------------------------------------------
# Dimension 3: Output Completeness (15 pts)
# ---------------------------------------------------------------------------

def score_output_completeness(base: Path, verbose: bool = False) -> dict:
    """Check that expected tables, figures, and logs exist and are non-empty."""
    tables_dir = base / "output" / "tables"
    figures_dir = base / "output" / "figures"
    logs_dir = base / "output" / "logs"

    checks = {"tables": 0, "figures": 0, "logs": 0}
    details = []

    # Tables: .tex files exist and non-empty
    if tables_dir.exists():
        tex_files = find_files(tables_dir, "*.tex")
        non_empty = [f for f in tex_files if f.stat().st_size > 0]
        if non_empty:
            checks["tables"] = 5
        else:
            details.append("No non-empty .tex files in output/tables/")
    else:
        details.append("output/tables/ directory not found")

    # Figures: .pdf or .png files exist
    if figures_dir.exists():
        fig_files = find_files(figures_dir, "*.pdf") + find_files(figures_dir, "*.png")
        if fig_files:
            checks["figures"] = 5
        else:
            details.append("No .pdf/.png files in output/figures/")
    else:
        details.append("output/figures/ directory not found")

    # Logs: .log files exist
    if logs_dir.exists():
        log_files = find_files(logs_dir, "*.log")
        if log_files:
            checks["logs"] = 5
        else:
            details.append("No .log files in output/logs/")
    else:
        # Also check root for logs (Stata generates them in CWD)
        root_logs = find_files(base, "*.log")
        if root_logs:
            checks["logs"] = 3  # Partial credit — logs exist but not in output/logs/
            details.append("Logs found in root but not in output/logs/")
        else:
            details.append("No log files found")

    score = checks["tables"] + checks["figures"] + checks["logs"]
    return {"score": score, "max": 15, "details": details}


# ---------------------------------------------------------------------------
# Dimension 4: Cross-Validation (15 pts)
# ---------------------------------------------------------------------------

def score_cross_validation(base: Path, verbose: bool = False) -> dict:
    """Check for Python cross-validation script and result documentation."""
    details = []
    score = 0

    # Check for cross-validation script
    py_dir = base / "code" / "python"
    crossval_scripts = []
    if py_dir.exists():
        crossval_scripts = [f for f in find_files(py_dir, "*.py")
                           if "cross" in f.name.lower() or "crossval" in f.name.lower()
                           or "validate" in f.name.lower()]

    if not crossval_scripts:
        # Also check for any .py file containing pyfixest
        all_py = find_files(base, "*.py")
        for f in all_py:
            content = read_text(f)
            if "pyfixest" in content or "cross" in content.lower():
                crossval_scripts.append(f)
                break

    if crossval_scripts:
        score += 5
        content = read_text(crossval_scripts[0])

        # Check for coefficient comparison
        if "diff" in content.lower() or "compare" in content.lower() or "match" in content.lower():
            score += 5
        else:
            details.append("Cross-validation script found but no comparison logic detected")

        # Check for pass/fail threshold
        if "0.1" in content or "0.001" in content or "PASS" in content or "FAIL" in content:
            score += 5
        else:
            details.append("No pass/fail threshold found in cross-validation script")
    else:
        details.append("No Python cross-validation script found")

    return {"score": score, "max": 15, "details": details}


# ---------------------------------------------------------------------------
# Dimension 5: Documentation (15 pts)
# ---------------------------------------------------------------------------

def score_documentation(base: Path, verbose: bool = False) -> dict:
    """Check REPLICATION.md, _VERSION_INFO.md, data source documentation."""
    details = []
    score = 0

    # REPLICATION.md exists with non-template content
    repl = base / "REPLICATION.md"
    if repl.exists():
        content = read_text(repl)
        if len(content) > 200 and "[Dataset 1]" not in content:
            score += 6  # Full credit — has real content
        elif len(content) > 100:
            score += 3  # Partial — still has template placeholders
            details.append("REPLICATION.md has template placeholders")
        else:
            score += 1
            details.append("REPLICATION.md exists but is mostly empty")
    else:
        details.append("REPLICATION.md not found")

    # _VERSION_INFO.md exists
    vinfo = base / "_VERSION_INFO.md"
    if vinfo.exists():
        content = read_text(vinfo)
        if len(content) > 50:
            score += 5
        else:
            score += 2
            details.append("_VERSION_INFO.md exists but is sparse")
    else:
        details.append("_VERSION_INFO.md not found")

    # Data sources documented (check REPLICATION.md or docs/)
    docs_dir = base / "docs"
    has_data_docs = False
    if repl.exists():
        content = read_text(repl)
        if "Source" in content and ("raw" in content.lower() or "data" in content.lower()):
            has_data_docs = True
    if docs_dir.exists():
        doc_files = find_files(docs_dir, "*.md")
        if doc_files:
            has_data_docs = True

    if has_data_docs:
        score += 4
    else:
        details.append("No data source documentation found")

    return {"score": min(score, 15), "max": 15, "details": details}


# ---------------------------------------------------------------------------
# Dimension 6: Method Diagnostics (25 pts)
# ---------------------------------------------------------------------------

def detect_methods(base: Path) -> list[str]:
    """Auto-detect econometric methods from .do file content."""
    do_files = find_files(base, "*.do")
    methods = set()

    for f in do_files:
        content = read_text(f).lower()
        if any(kw in content for kw in ["csdid", "did_multiplegt", "did_imputation",
                                         "bacondecomp", "event_study", "eventstudyinteract",
                                         "parallel trend"]):
            methods.add("DID")
        if any(kw in content for kw in ["ivreghdfe", "ivreg2", "2sls", "instrument",
                                         "first.stage", "first stage", "endogenous"]):
            methods.add("IV")
        if any(kw in content for kw in ["rdrobust", "rddensity", "rdplot", "cutoff",
                                         "bandwidth", "discontinuity"]):
            methods.add("RDD")
        if any(kw in content for kw in ["xtset", "xtreg", "xtabond2", "hausman",
                                         "panel"]):
            methods.add("Panel")

    return sorted(methods)


def score_method_diagnostics(base: Path, verbose: bool = False) -> dict:
    """Score method-specific diagnostics based on auto-detected methods."""
    methods = detect_methods(base)
    if not methods:
        return {"score": 0, "max": 25, "details": ["No econometric methods detected in .do files"],
                "methods": []}

    do_files = find_files(base, "*.do")
    all_content = "\n".join(read_text(f) for f in do_files).lower()
    log_files = find_files(base, "*.log")
    all_logs = "\n".join(read_text(f) for f in log_files).lower()
    combined = all_content + "\n" + all_logs

    details = []
    method_scores = {}

    if "DID" in methods:
        did_score = 0
        did_max = 25

        # Pre-trend F-test
        if "testparm" in combined or "pre-trend" in combined or "pretrend" in combined:
            did_score += 5
        else:
            details.append("DID: No pre-trend F-test found")

        # Event study
        if "event" in combined and ("coefplot" in combined or "csdid_plot" in combined or "event_plot" in combined):
            did_score += 5
        else:
            details.append("DID: No event study plot found")

        # Robust estimator alongside TWFE
        if "csdid" in combined or "did_multiplegt" in combined or "did_imputation" in combined:
            did_score += 5
        else:
            details.append("DID: No robust DID estimator (CS-DiD, dCDH, BJS) found alongside TWFE")

        # Goodman-Bacon decomposition
        if "bacondecomp" in combined:
            did_score += 5
        else:
            details.append("DID: No Goodman-Bacon decomposition found")

        # HonestDiD or wild cluster bootstrap
        if "honestdid" in combined or "boottest" in combined:
            did_score += 5
        else:
            details.append("DID: No HonestDiD sensitivity or wild cluster bootstrap found")

        method_scores["DID"] = {"score": did_score, "max": did_max}

    if "IV" in methods:
        iv_score = 0
        iv_max = 25

        # First-stage F reported
        if "first" in combined and ("f(" in combined or "f =" in combined or "f-stat" in combined
                                    or "f stat" in combined):
            iv_score += 6
        else:
            details.append("IV: First-stage F-statistic not clearly reported")

        # KP F reported
        if "kleibergen" in combined or "kp" in combined:
            iv_score += 5
        else:
            details.append("IV: Kleibergen-Paap F not reported")

        # LIML comparison
        if "liml" in combined:
            iv_score += 5
        else:
            details.append("IV: No LIML comparison found")

        # Density/exclusion discussion
        if "exclusion" in combined or "instrument validity" in combined:
            iv_score += 4
        else:
            details.append("IV: No exclusion restriction discussion found")

        # Over-identification or AR test
        if "hansen" in combined or "sargan" in combined or "anderson-rubin" in combined or "weakiv" in combined:
            iv_score += 5
        else:
            details.append("IV: No over-identification or weak-IV robust test found")

        method_scores["IV"] = {"score": iv_score, "max": iv_max}

    if "RDD" in methods:
        rdd_score = 0
        rdd_max = 25

        # Density test
        if "rddensity" in combined or "mccrary" in combined:
            rdd_score += 6
        else:
            details.append("RDD: No density test (CJM/McCrary) found")

        # Bandwidth sensitivity
        bw_keywords = ["0.5", "0.75", "1.25", "1.5", "2.0", "bwselect"]
        bw_count = sum(1 for kw in bw_keywords if kw in combined)
        if bw_count >= 3:
            rdd_score += 6
        elif bw_count >= 1:
            rdd_score += 3
            details.append("RDD: Limited bandwidth sensitivity analysis")
        else:
            details.append("RDD: No bandwidth sensitivity analysis found")

        # Polynomial sensitivity
        if "p(1)" in combined or "p(2)" in combined or "p(3)" in combined:
            rdd_score += 5
        else:
            details.append("RDD: No polynomial order sensitivity found")

        # Placebo cutoffs
        if "placebo" in combined or "fake" in combined:
            rdd_score += 4
        else:
            details.append("RDD: No placebo cutoff tests found")

        # Covariate balance
        if "balance" in combined or "covariate" in combined:
            rdd_score += 4
        else:
            details.append("RDD: No covariate balance test at cutoff found")

        method_scores["RDD"] = {"score": rdd_score, "max": rdd_max}

    if "Panel" in methods:
        panel_score = 0
        panel_max = 25

        # Hausman test
        if "hausman" in combined:
            panel_score += 7
        else:
            details.append("Panel: No Hausman test found")

        # Serial correlation
        if "xtserial" in combined or "wooldridge" in combined or "serial" in combined:
            panel_score += 6
        else:
            details.append("Panel: No serial correlation test found")

        # Appropriate clustering
        if "vce(cluster" in combined or "cluster(" in combined:
            panel_score += 6
        else:
            details.append("Panel: No clustered standard errors found")

        # Within R-squared or dynamic panels
        if "r2_within" in combined or "within r" in combined or "xtabond2" in combined:
            panel_score += 6
        else:
            details.append("Panel: No within R-squared reported or dynamic panel considered")

        method_scores["Panel"] = {"score": panel_score, "max": panel_max}

    # Combine: if multiple methods, average and scale to 25
    if method_scores:
        total_score = sum(ms["score"] for ms in method_scores.values())
        total_max = sum(ms["max"] for ms in method_scores.values())
        normalized = round(total_score / total_max * 25) if total_max > 0 else 0
    else:
        normalized = 0

    return {
        "score": normalized,
        "max": 25,
        "details": details,
        "methods": methods,
        "method_scores": method_scores,
    }


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

def score_directory(base_path: str, verbose: bool = False) -> dict:
    """Score a version directory on all 6 dimensions."""
    base = Path(base_path)
    if not base.exists():
        print(f"Error: Directory '{base_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    results = {
        "target": str(base),
        "dimensions": {},
        "total": 0,
        "max_total": 100,
    }

    scorers = [
        ("Code Conventions", score_code_conventions),
        ("Log Cleanliness", score_log_cleanliness),
        ("Output Completeness", score_output_completeness),
        ("Cross-Validation", score_cross_validation),
        ("Documentation", score_documentation),
        ("Method Diagnostics", score_method_diagnostics),
    ]

    for name, scorer in scorers:
        result = scorer(base, verbose)
        results["dimensions"][name] = result
        results["total"] += result["score"]

    # Status
    total = results["total"]
    if total >= 95:
        results["status"] = "PUBLICATION READY"
    elif total >= 90:
        results["status"] = "MINOR REVISIONS"
    elif total >= 80:
        results["status"] = "MAJOR REVISIONS"
    else:
        results["status"] = "REDO"

    return results


def print_text_report(results: dict, verbose: bool = False) -> None:
    """Print human-readable report."""
    print(f"\nQuality Score Report for {results['target']}")
    print("=" * 50)
    print()

    for name, dim in results["dimensions"].items():
        score = dim["score"]
        max_score = dim["max"]
        bar_len = 15
        filled = round(score / max_score * bar_len) if max_score > 0 else 0
        bar = "#" * filled + "." * (bar_len - filled)
        print(f"  {name:<22s} {score:>2d}/{max_score:<2d}  [{bar}]")

        if verbose and dim.get("details"):
            for detail in dim["details"]:
                print(f"    - {detail}")

        if "methods" in dim and dim["methods"]:
            print(f"    Methods detected: {', '.join(dim['methods'])}")
            if verbose and "method_scores" in dim:
                for method, ms in dim["method_scores"].items():
                    print(f"      {method}: {ms['score']}/{ms['max']}")

    print()
    print(f"  {'TOTAL':<22s} {results['total']:>2d}/{results['max_total']}")
    print()
    print(f"  Status: {results['status']}")

    if results["total"] < 80:
        print()
        print("  Priority fixes:")
        for name, dim in results["dimensions"].items():
            if dim["score"] < dim["max"] * 0.6:
                print(f"    [{name}] Score {dim['score']}/{dim['max']} — needs attention")
                if dim.get("details"):
                    for detail in dim["details"][:3]:
                        print(f"      - {detail}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Score an economics research version directory on 6 quality dimensions."
    )
    parser.add_argument("directory", help="Path to the version directory (e.g., v1/)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed findings")

    args = parser.parse_args()

    results = score_directory(args.directory, verbose=args.verbose)

    if args.json:
        # Clean up non-serializable items
        output = {
            "target": results["target"],
            "total": results["total"],
            "max_total": results["max_total"],
            "status": results["status"],
            "dimensions": {},
        }
        for name, dim in results["dimensions"].items():
            output["dimensions"][name] = {
                "score": dim["score"],
                "max": dim["max"],
                "details": dim.get("details", []),
            }
            if "methods" in dim:
                output["dimensions"][name]["methods"] = dim["methods"]
            if "method_scores" in dim:
                output["dimensions"][name]["method_scores"] = {
                    k: {"score": v["score"], "max": v["max"]}
                    for k, v in dim["method_scores"].items()
                }
        print(json.dumps(output, indent=2))
    else:
        print_text_report(results, verbose=args.verbose)


if __name__ == "__main__":
    main()
