"""
Flask Web Application for AutoGrader.
Minimalist, black-and-white local host UI for autonomous evaluation,
live metric visualization, and report downloads.
"""

from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort

from autograder.config import GradingRules
from autograder.coordinator import GradingCoordinator
from autograder.compiler import CCompiler

app = Flask(__name__)
BASE_DIR = Path(__file__).parent.resolve()
SUBMISSIONS_DIR = BASE_DIR / "submissions"
RULES_DIR = BASE_DIR / "rules"
REPORTS_DIR = BASE_DIR / "reports"
PDF_PATH = BASE_DIR / "agentic01.pdf"

# Initialize coordinator
compiler = CCompiler()
coordinator = GradingCoordinator(compiler=compiler)


@app.route("/")
def index():
    sample_files = sorted([f.name for f in SUBMISSIONS_DIR.glob("*.c")])
    rule_files = sorted([f.name for f in RULES_DIR.glob("*.json")])
    return render_template(
        "index.html",
        sample_files=sample_files,
        rule_files=rule_files,
    )


@app.route("/evaluate", methods=["POST"])
def evaluate():
    mode = request.form.get("submission_mode", "sample")
    rules_filename = request.form.get("rules_file", "add_two_integers.json")

    rules_path = RULES_DIR / rules_filename
    if not rules_path.is_file():
        return jsonify({"error": f"Rules file '{rules_filename}' not found."}), 404

    try:
        rules = GradingRules.load_from_file(rules_path)
    except Exception as e:
        return jsonify({"error": f"Failed to parse rules: {str(e)}"}), 400

    target_source_path = None
    cleanup_temp = False

    if mode == "sample":
        sample_name = request.form.get("sample_file", "add_student.c")
        target_source_path = SUBMISSIONS_DIR / sample_name
        if not target_source_path.is_file():
            return jsonify({"error": f"Sample '{sample_name}' not found."}), 404

    elif mode == "upload":
        if "upload_file" not in request.files:
            return jsonify({"error": "No file uploaded."}), 400
        uploaded = request.files["upload_file"]
        if not uploaded.filename:
            return jsonify({"error": "Empty filename."}), 400

        tmp = tempfile.NamedTemporaryFile("wb", suffix=".c", delete=False)
        uploaded.save(tmp.name)
        target_source_path = Path(tmp.name)
        cleanup_temp = True

    elif mode == "paste":
        code = request.form.get("code_text", "").strip()
        if not code:
            return jsonify({"error": "No C code provided."}), 400

        tmp = tempfile.NamedTemporaryFile("w", suffix=".c", delete=False, encoding="utf-8")
        tmp.write(code)
        tmp.close()
        target_source_path = Path(tmp.name)
        cleanup_temp = True

    else:
        return jsonify({"error": "Invalid submission mode."}), 400

    try:
        # Run autonomous grading
        report = coordinator.evaluate(
            submission_path=target_source_path,
            rules=rules,
            reports_dir=REPORTS_DIR,
        )
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": f"Evaluation exception: {str(e)}"}), 500
    finally:
        if cleanup_temp and target_source_path and target_source_path.is_file():
            try:
                target_source_path.unlink()
            except Exception:
                pass


@app.route("/batch-grade")
def batch_grade():
    rules_filename = request.args.get("rules", "add_two_integers.json")
    rules_path = RULES_DIR / rules_filename
    if not rules_path.is_file():
        return jsonify({"error": f"Rules file '{rules_filename}' not found."}), 404

    try:
        rules = GradingRules.load_from_file(rules_path)
    except Exception as e:
        return jsonify({"error": f"Failed to parse rules: {str(e)}"}), 400

    results = []
    c_files = sorted(list(SUBMISSIONS_DIR.glob("*.c")))
    for cf in c_files:
        try:
            rep = coordinator.evaluate(cf, rules, reports_dir=REPORTS_DIR)
            results.append({
                "submission": cf.name,
                "grade": rep["grade"],
                "first_pass": rep["first_pass"],
            })
        except Exception as e:
            results.append({
                "submission": cf.name,
                "grade": 0.0,
                "first_pass": {"compiled": False, "smoke_ok": False, "error": str(e)},
            })

    return jsonify(results)


@app.route("/rules-list")
def rules_list():
    rule_files = sorted([f.name for f in RULES_DIR.glob("*.json")])
    return jsonify({"rules": rule_files})


@app.route("/create-rule", methods=["POST"])
def create_rule_endpoint():
    from add_problem import create_problem
    data = request.get_json(silent=True) or request.form.to_dict()
    prob_name = data.get("problem_name", "").strip()
    if not prob_name:
        return jsonify({"error": "Problem name is required."}), 400

    try:
        time_limit = float(data.get("time_limit_s", 2.0))
        memory_limit = int(data.get("memory_limit_mb", 64))
        complexity = data.get("complexity", "O(N)")
        
        # Testcases
        testcases = []
        raw_tests = data.get("testcases", [])
        if isinstance(raw_tests, str):
            try:
                import json
                raw_tests = json.loads(raw_tests)
            except Exception:
                raw_tests = []
        if isinstance(raw_tests, list):
            for item in raw_tests:
                if isinstance(item, dict):
                    testcases.append((item.get("input", ""), item.get("output", "")))

        rule_path = create_problem(
            problem_name=prob_name,
            time_limit_s=time_limit,
            memory_limit_mb=memory_limit,
            complexity=complexity,
            test_cases=testcases if testcases else None,
        )
        return jsonify({
            "success": True,
            "problem": rule_path.stem,
            "rule_file": rule_path.name,
            "tests_dir": f"tests/{rule_path.stem}/",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/download/report/<filename>")
def download_report(filename):
    file_path = (REPORTS_DIR / filename).resolve()
    # Security check: must remain inside REPORTS_DIR
    if not str(file_path).startswith(str(REPORTS_DIR.resolve())):
        abort(403)
    if not file_path.is_file():
        abort(404)
    return send_file(file_path, as_attachment=True)


@app.route("/download/pdf")
def download_pdf():
    if not PDF_PATH.is_file():
        # Generate if missing
        from generate_report_pdf import build_pdf
        build_pdf(str(PDF_PATH))
    return send_file(PDF_PATH, as_attachment=True, download_name="agentic01.pdf")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting AutoGrader Web UI on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)

