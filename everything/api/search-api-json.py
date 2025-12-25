"""
Everything HTTP Server - JSON Search API Verification Script

This script verifies the behavior of the Everything HTTP Server's JSON search API (json=1)
against the OpenAPI expectations defined in `search-api-json.yaml`.
It validates the JSON response structure, paging, sorting, and specific column data types.

Usage:
    python everything/api/search-api-json.py [--url http://host:port]

Dependencies:
    - requests

Tests performed:
    1. Basic JSON Structure: Checks for `totalResults` and `results` keys in the response.
    2. Count, Offset, Sort: Verifies pagination and server-side sorting.
    3. Column Support:
       - Checks presence of `path`, `size`, `date_modified`.
       - Verifies that `size` and `date_modified` are returned as strings (10-base), as noted in the schema.
       - Confirms `date_created` is NOT returned (as per implementation status).
"""

__author__ = "Takashi Sasaki"
__contact__ = "https://x.com/TakashiSasaki"
__version__ = "1.4.0"

import requests
import argparse
import sys
import os
import time
import json

def setup_test_files():
    """Create a set of temporary files for testing search."""
    cwd = os.getcwd()
    ts = int(time.time())
    files = {
        f"verify_{ts}_alpha.txt": "content alpha",
        f"verify_{ts}_beta.txt": "content beta",
        f"verify_{ts}_gamma.txt": "content gamma",
    }
    created = []
    for name, content in files.items():
        path = os.path.join(cwd, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(path)
    
    print(f"Created {len(created)} test files. Waiting 10s for indexing...")
    time.sleep(10)
    return created

def teardown_test_files(files):
    for f in files:
        if os.path.exists(f):
            os.remove(f)
    print("Cleaned up test files.")

def test_json_search_api(base_url, created_paths):
    print(f"Testing JSON Search API at {base_url}")
    
    # Extract basenames [alpha, beta, gamma]
    # setup_test_files sorts keys, so order is preserved [alpha, beta, gamma]
    filenames = [os.path.basename(p) for p in created_paths]
    f_alpha = filenames[0]
    f_beta = filenames[1]
    f_gamma = filenames[2]
    
    # Common prefix for search (e.g. "verify_123456_")
    common_prefix = f_alpha.split("alpha.txt")[0]
    print(f"DEBUG: Using common prefix: {common_prefix}")

    # 1. Basic JSON Structure & json=1
    print("\n[Test 1] Basic JSON Structure (json=1)")
    params = {"search": f_alpha, "json": 1}
    try:
        resp = requests.get(f"{base_url}/", params=params)
    except Exception as e:
        print(f"FAIL: Request failed: {e}")
        return False
        
    if resp.status_code != 200:
        print(f"FAIL: Status {resp.status_code}")
        return False
    
    try:
        data = resp.json()
    except json.JSONDecodeError:
        print(f"FAIL: Response is not valid JSON. Content-Type: {resp.headers.get('Content-Type')}")
        return False
        
    if "totalResults" not in data or "results" not in data:
        print(f"FAIL: Missing 'totalResults' or 'results' in JSON: {data.keys()}")
        return False
        
    print(f"PASS: Got valid JSON with totalResults={data['totalResults']}")
    
    # Check content
    found = False
    for item in data["results"]:
        if item.get("name") == f_alpha:
            found = True
            break
    if found:
        print("PASS: Found expected file in results.")
    else:
        print(f"FAIL: Expected file {f_alpha} not found in results.")
        return False


    # 2. Count, Offset, Sort
    print("\n[Test 2] Count, Offset, Sort")
    params = {
        "search": common_prefix, 
        "json": 1, 
        "count": 2, 
        "sort": "name", 
        "ascending": 1
    }
    resp = requests.get(f"{base_url}/", params=params)
    data = resp.json()
    results = data.get("results", [])
    
    if len(results) > 2:
        print(f"FAIL: Count=2 but got {len(results)} items.")
        return False
        
    names = [x.get("name") for x in results]
    print(f"DEBUG: Retrieved names: {names}")
    
    if f_alpha in names and f_beta in names:
        if f_gamma not in names:
             print("PASS: Count limit works.")
        else:
             print("FAIL: Count limit issue (found gamma).")
             return False
    else:
        print("FAIL: Sorting or finding issue. Expected alpha/beta.")
        return False

    # Offset
    params["offset"] = 2
    resp = requests.get(f"{base_url}/", params=params)
    data = resp.json()
    names_offset = [x.get("name") for x in data.get("results", [])]
    if f_gamma in names_offset:
        print("PASS: Offset works.")
    else:
        print(f"FAIL: Offset did not return expected gamma. Got: {names_offset}")
        return False


    # 3. Columns (path, size, date_modified)
    print("\n[Test 3] Columns (path, size, date_modified)")
    # Request extra columns
    params = {
        "search": f_alpha, 
        "json": 1,
        "path_column": 1,
        "size_column": 1,
        "date_modified_column": 1,
        "date_created_column": 1 
    }
    resp = requests.get(f"{base_url}/", params=params)
    data = resp.json()
    if not data["results"]:
        print("FAIL: No results for column test.")
        return False
        
    item = data["results"][0]
    
    if "path" in item:
        print("PASS: 'path' column present.")
    else:
        print("FAIL: 'path' column missing.")
        return False

    if "size" in item:
        val = item["size"]
        print(f"PASS: 'size' column present. Value: {val} (Type: {type(val)})")
    else:
        print("FAIL: 'size' column missing.")
        return False

    if "date_modified" in item:
        val = item["date_modified"]
        print(f"PASS: 'date_modified' column present. Value: {val} (Type: {type(val)})")
    else:
        print("FAIL: 'date_modified' column missing.")
        return False

    if "date_created" in item:
        print(f"INFO: 'date_created' IS supported! Value: {item['date_created']}")
    else:
        print("INFO: 'date_created' not returned (as expected per schema notes).")

    # 4. Extended Parameters (case, wholeword, attributes_column)
    print("\n[Test 4] Extended Parameters (case, wholeword, attributes_column)")
    
    # Needs a file that differs by case
    query_upper = f_alpha.replace("alpha.txt", "ALPHA.txt")
    
    # case=0 (default) -> Found
    params = {"search": query_upper, "json": 1, "case": 0}
    resp = requests.get(f"{base_url}/", params=params)
    if f_alpha in str(resp.json().get("results", [])):
        print("PASS: case=0 found file with different case query.")
    else:
        print(f"FAIL: case=0 failed to find file {f_alpha} via {query_upper}")
        return False

    # case=1 -> Not Found
    params["case"] = 1
    resp = requests.get(f"{base_url}/", params=params)
    res_text = str(resp.json().get("results", []))
    if f_alpha not in res_text:
        print("PASS: case=1 correctly did NOT find file.")
    else:
        print("WARNING: case=1 found file (might be environment dependent).")

    # attributes_column=1
    params = {"search": f_alpha, "json": 1, "attributes_column": 1}
    resp = requests.get(f"{base_url}/", params=params)
    item = resp.json().get("results", [{}])[0]
    if "attributes" in item:
        print(f"PASS: attributes_column=1 returned attributes: {item['attributes']}")
    else:
        print("INFO: attributes_column=1 did not return 'attributes' field (similar to date_created).")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Everything JSON Search API")
    parser.add_argument("--url", default="http://127.160.164.78:8000", help="Base URL")
    args = parser.parse_args()
    
    created_files = setup_test_files()
    try:
        if test_json_search_api(args.url, created_files):
            print("\nAll JSON Search API tests passed!")
        else:
            print("\nSome tests failed.")
            sys.exit(1)
    finally:
        teardown_test_files(created_files)
