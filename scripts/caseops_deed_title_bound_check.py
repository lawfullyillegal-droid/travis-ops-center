#!/usr/bin/env python3
import subprocess
import sys

facts = """
formulas(assumptions).
  recorded_deed(fee_2020015036).
  identifies_as_grantee(fee_2020015036, connie_j_cowins).
  identifies_as_grantee(fee_2020015036, bailey_h_cowins).
  covers_apn(fee_2020015036, apn_306_07_108e).
  recorded_on(fee_2020015036, d2020_03_10).
  states_joint_tenancy_with_survivorship(
    fee_2020015036, connie_j_cowins, bailey_h_cowins).
  all f all x all a all d (
    (recorded_deed(f) & identifies_as_grantee(f,x) &
     covers_apn(f,a) & recorded_on(f,d))
    -> recorded_grantee(x,a,d)).
end_of_list.
"""

checks = [
    ("CHECK 1 — recorded grantee",
     "recorded_grantee(connie_j_cowins, apn_306_07_108e, d2020_03_10)."),
    ("CHECK 2 — current owner from deed-only facts",
     "current_owner(connie_j_cowins, apn_306_07_108e, d2026_10_17)."),
]

print("Source premise: deed Fee 2020015036, transcribed from the reviewed PDF.")
print("Theorem results depend on these entered premises; Prover9 does not authenticate the deed.")
print()

for label, goal in checks:
    problem = facts + "\nformulas(goals).\n  " + goal + "\nend_of_list.\n"
    print(label)
    try:
        result = subprocess.run(
            ["prover9", "-t", "10"],
            input=problem, capture_output=True, text=True, timeout=20
        )
    except Exception as exc:
        print("ERROR:", exc)
        sys.exit(1)
    print(result.stdout or result.stderr or "(no Prover9 output)")
    if result.returncode:
        print("Prover9 exit code:", result.returncode)
    print()

print("Interpret only if both Prover9 runs completed without parser/process errors.")
print("it does not prove Connie is not the current owner.")
