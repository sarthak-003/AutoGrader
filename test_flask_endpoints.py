from app import app

client = app.test_client()

# 1. Test GET /
res = client.get('/')
assert res.status_code == 200, f"GET / failed: {res.status_code}"
assert b"theme-btn" in res.data, "Theme toggle button missing"
assert b"toggleTheme" in res.data, "toggleTheme function missing"
assert b"THEME:" in res.data, "Theme button text missing"
print("[+] GET / passed: Dark/Light toggle HTML found")

# 2. Test POST /evaluate for two_sum_optimal.c
res_eval = client.post('/evaluate', data={
    "submission_mode": "sample",
    "sample_file": "two_sum_optimal.c",
    "rules_file": "two_sum_sorted.json"
})
assert res_eval.status_code == 200, f"POST /evaluate failed: {res_eval.status_code}"
data = res_eval.get_json()
grade = data.get("grade")
assert grade == 95.0, f"Expected 95.0, got {grade}"
deductions = data.get("deductions", [])
assert len(deductions) > 0, "Deductions list missing"
assert "two_sum_sorted" in data.get("usefulness_limitations", {}).get("problem", ""), "Problem-specific profile missing"
print(f"[+] POST /evaluate passed: Grade = {grade}/100")
for d in deductions:
    print(f"    Deduction: {d}")

# 3. Test GET /download/pdf
res_pdf = client.get('/download/pdf')
assert res_pdf.status_code == 200, f"GET /download/pdf failed: {res_pdf.status_code}"
assert res_pdf.mimetype == "application/pdf", f"Expected pdf, got {res_pdf.mimetype}"
print(f"[+] GET /download/pdf passed: Content-Length = {len(res_pdf.data)} bytes")

# 4. Test GET /download/report/binary_search_optimal.txt
res_rep = client.get('/download/report/binary_search_optimal.txt')
assert res_rep.status_code == 200, f"GET report failed: {res_rep.status_code}"
assert b"binary_search_optimal.c" in res_rep.data
print("[+] GET /download/report passed: binary_search_optimal.txt served correctly")

# 5. Test POST /create-rule
res_create = client.post('/create-rule', json={
    "problem_name": "matrix_transpose",
    "complexity": "O(N^2)",
    "time_limit_s": 2.0,
    "memory_limit_mb": 64,
    "testcases": [
        {"input": "2 2\n1 2\n3 4\n", "output": "1 3\n2 4\n"}
    ]
})
assert res_create.status_code == 200, f"POST /create-rule failed: {res_create.status_code}"
create_data = res_create.get_json()
assert create_data.get("success") is True
print(f"[+] POST /create-rule passed: Created {create_data.get('rule_file')}")

# 6. Test GET /rules-list
res_list = client.get('/rules-list')
assert res_list.status_code == 200
rules_arr = res_list.get_json().get("rules", [])
assert "matrix_transpose.json" in rules_arr
print(f"[+] GET /rules-list passed: Found {len(rules_arr)} rules including matrix_transpose.json")

print("\n[*] ALL FLASK WEB SERVER VERIFICATION TESTS PASSED WITH 100% SUCCESS!")
