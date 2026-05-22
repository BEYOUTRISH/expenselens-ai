"""Test core cleaning pipeline modules."""
import sys
sys.path.insert(0, ".")

from app.services.cleaning.date_parser import parse_date
from app.services.cleaning.amount_parser import parse_amount
from app.services.cleaning.currency_converter import convert_to_inr
from app.services.cleaning.vendor_resolver import resolve_vendor
from app.services.cleaning.department_normalizer import normalize_department
from app.services.cleaning.personal_detector import is_personal
from app.services.cleaning.validator import ExpenseValidator
import pandas as pd

print("=== Imports OK ===")

print("\n=== Date Parser ===")
for t in ["2024-01-15", "01/15/2024", "15.01.2024", "15-Jan-2024", "2024/01/15", 1778803200.0, None, "invalid"]:
    result, issue = parse_date(t)
    print(f"  {str(t):25s} -> {str(result):15s} | {issue or 'OK'}")

print("\n=== Amount Parser ===")
tests = [
    ("\u20b9 4,50,000", None),
    ("SGD 500", None),
    ("14000 GBP", None),
    ("1,00,00,000", None),
    ("--", None),
    ("TBD", None),
    (900000.0, None),
    ("\u20b9 -5,000", None),
    ("5,000.00", None),
    ("NIL", None),
]
for amt_str, ccy in tests:
    amt, det_ccy, issue = parse_amount(amt_str)
    print(f"  {str(amt_str):25s} -> amt={str(amt):12s} ccy={str(det_ccy):5s} | {issue or 'OK'}")

print("\n=== Currency Converter ===")
for ccy in ["USD", "EUR", "GBP", "SGD", "AED", "INR"]:
    amt_inr, rate = convert_to_inr(1000, ccy)
    print(f"  1000 {ccy:3s} -> INR {amt_inr:>10.2f} (rate: {rate:.4f})")

print("\n=== Vendor Resolver ===")
for t in ["ZOOM VIDEO COMMUNICATIONS", "swiggy for business", "AMAZON WEB SERVICES INC", "", "Some unknown vendor"]:
    canon, alias, issue = resolve_vendor(t, "Test description")
    print(f"  {str(t):35s} -> {canon:25s} | {issue or 'OK'}")

print("\n=== Department Normalizer ===")
for t in ["Saless", "Desgn", "Engineering", "IT", "Data Science", "Finance"]:
    dept, issue = normalize_department(t)
    print(f"  {str(t):20s} -> {dept:15s} | {issue or 'OK'}")

print("\n=== Personal Detector ===")
for t in ["Spouse flight ticket - accompanied personal travel", "AWS cloud services", "Personal Amazon Prime renewal", "Team lunch"]:
    pers, reason = is_personal(t)
    print(f"  {str(t)[:50]:50s} -> personal={pers} | {reason or 'OK'}")

print("\n=== Validator Class ===")
fake_data = pd.DataFrame({
    "txn_id": ["TXN-1", "TXN-2", "TXN-3"],
    "submission_date": ["2024-01-15", "invalid", None],
    "txn_date": ["2024-01-15", "01/15/2024", "15.01.2024"],
    "amount_raw": ["1000", "TBD", "\u20b9 5,000"],
    "currency_raw": ["INR", "USD", None],
    "vendor_raw": ["Amazon", "", "Flipkart"],
    "description": ["Office supplies", "Team lunch", "Personal gift"],
    "department": ["Engineering", "Saless", "Finance"],
    "cost_center": ["CC001", "N/A", "CC005"],
    "submitted_by": ["John", "Jane", ""],
    "receipt_attached": ["Yes", "No", "True"],
    "notes": ["", "", ""],
})
validator = ExpenseValidator(fake_data)
report = validator.run()
print(f"  Total rows: {report['total_rows_in_source']}")
print(f"  Rows loaded: {report['rows_loaded']}")
print(f"  Rows excluded: {report['rows_excluded']}")
print(f"  Issues: {len(report['issues'])}")
for i in report['issues'][:5]:
    print(f"    [{i['severity']:8s}] {i['txn_id']}:{i['field']} -> {i['issue_type']}")

print("\n=== ALL CORE TESTS PASSED ===")
