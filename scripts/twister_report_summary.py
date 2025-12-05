#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import sys
import html
import re


def slugify(name: str) -> str:
    """Convert testcase name to safe HTML anchor ID."""
    return re.sub(r'[^a-zA-Z0-9\-]+', '-', name)


def summarize_status(status_counts):
    if status_counts["FAILED"] > 0:
        color = "red"
        text = "failing"
    elif status_counts["SKIPPED"] > 0:
        color = "yellow"
        text = "passing_with_skips"
    else:
        color = "brightgreen"
        text = "passing"
    return f"![status](https://img.shields.io/badge/tests-{text}-{color}.svg)"


def format_report(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    global_counts = {"PASS": 0, "FAILED": 0, "SKIPPED": 0}
    suites_summary = []

    out = []
    failure_logs = []  # All collapsible logs collected here

    out.append("# 🧪 Zephyr Twister Test Report\n")

    for ts in root.findall("testsuite"):
        suite_name = ts.get("name")
        suite_pass = suite_fail = suite_skip = 0

        out.append(f"## Testsuite: `{suite_name}`\n")
        out.append("| Testcase | Status | Duration | Details |")
        out.append("|----------|--------|----------|---------|")

        for tc in ts.findall("testcase"):
            name = tc.get("name")
            safe_id = slugify(name)
            duration = tc.get("time", "")
            status = "PASS"
            in_table_details = ""

            skipped = tc.find("skipped")
            failure = tc.find("failure")

            if skipped is not None:
                status = "SKIPPED"
                in_table_details = skipped.get("message", "")
                suite_skip += 1

            elif failure is not None:
                status = "FAILED"
                suite_fail += 1

                msg = html.escape(failure.get("message", ""))
                raw = html.escape(failure.text or "")

                # In-table item (1-line only)
                in_table_details = f"[View log](#log-{safe_id})"

                # Full block saved for later
                failure_logs.append(
                    f"<details id=\"log-{safe_id}\"><summary><strong>{name}</strong>: {msg}</summary>\n\n"
                    f"```\n{raw}\n```\n"
                    f"</details>\n"
                )

                # No duration for failed tests
                duration = ""

            else:
                suite_pass += 1
                in_table_details = ""
                # Duration kept for passing tests

            global_counts[status] += 1

            # Final table row
            out.append(
                f"| `{name}` | {status} | {duration} | {in_table_details} |"
            )

        suites_summary.append((suite_name, suite_pass, suite_fail, suite_skip))
        out.append("")  # blank line

    # --- Summary Section ---
    out.append("# 📊 Summary\n")
    out.append("| Testsuite | PASS | FAILED | SKIPPED |")
    out.append("|-----------|------|--------|---------|")

    for name, p, f, s in suites_summary:
        out.append(f"| `{name}` | {p} | {f} | {s} |")

    out.append("")
    out.append("## Totals\n")
    out.append(f"- **PASS**: {global_counts['PASS']}")
    out.append(f"- **FAILED**: {global_counts['FAILED']}")
    out.append(f"- **SKIPPED**: {global_counts['SKIPPED']}\n")

    # Badge
    out.append("## Status\n")
    out.append(summarize_status(global_counts))

    # Full logs AFTER tables
    if failure_logs:
        out.append("\n# 🔎 Failure Logs\n")
        out.extend(failure_logs)

    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_twister_comment.py twister_report.xml")
        sys.exit(1)

    print(format_report(sys.argv[1]))
