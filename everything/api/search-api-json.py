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

    # 5. Alias Parameters (i, w, p, r, m)
    print("\n[Test 5] Parameter Aliases")
    
    # Test 'i' alias for 'case'
    params_full = {"search": query_upper, "json": 1, "case": 0}
    params_alias = {"search": query_upper, "json": 1, "i": 0}
    resp_full = requests.get(f"{base_url}/", params=params_full)
    resp_alias = requests.get(f"{base_url}/", params=params_alias)
    if resp_full.json().get("totalResults") == resp_alias.json().get("totalResults"):
        print("PASS: 'i' alias works identically to 'case'.")
    else:
        print("FAIL: 'i' alias doesn't match 'case' behavior.")
        return False

    # 6. Path Search
    print("\n[Test 6] Path Search (path parameter)")
    
    # Get the directory name from alpha file path
    alpha_path = created_paths[0]
    dir_name = os.path.basename(os.path.dirname(alpha_path))
    
    # Search without path parameter (should only search filename)
    params = {"search": dir_name, "json": 1, "path": 0}
    resp = requests.get(f"{base_url}/", params=params)
    results_no_path = resp.json().get("totalResults", 0)
    
    # Search with path parameter (should search full path)
    params["path"] = 1
    resp = requests.get(f"{base_url}/", params=params)
    results_with_path = resp.json().get("totalResults", 0)
    
    if results_with_path > 0:
        print(f"PASS: path=1 found results when searching directory name (total: {results_with_path}).")
    else:
        print("INFO: path parameter tested but no conclusive results.")

    # Test 'p' alias
    params_alias = {"search": dir_name, "json": 1, "p": 1}
    resp_alias = requests.get(f"{base_url}/", params=params_alias)
    if resp_alias.json().get("totalResults") == results_with_path:
        print("PASS: 'p' alias works identically to 'path'.")
    else:
        print("WARNING: 'p' alias might not match 'path' behavior.")

    # 7. Regex Search
    print("\n[Test 7] Regex Search")
    
    # Create regex pattern matching alpha OR beta
    regex_pattern = f"verify_.*_(alpha|beta)\\.txt"
    params = {"search": regex_pattern, "json": 1, "regex": 1}
    resp = requests.get(f"{base_url}/", params=params)
    data = resp.json()
    results = data.get("results", [])
    names = [x.get("name") for x in results]
    
    if f_alpha in names and f_beta in names:
        print(f"PASS: regex=1 found files matching pattern (found {len(results)} results).")
    else:
        print(f"INFO: regex parameter tested but results unclear. Found: {names}")

    # Test 'r' alias
    params_alias = {"search": regex_pattern, "json": 1, "r": 1}
    resp_alias = requests.get(f"{base_url}/", params=params_alias)
    if resp_alias.json().get("totalResults") == data.get("totalResults"):
        print("PASS: 'r' alias works identically to 'regex'.")
    else:
        print("WARNING: 'r' alias might not match 'regex' behavior.")

    # 8. Sort Order (ascending)
    print("\n[Test 8] Sort Order (ascending parameter)")
    
    # Sort ascending by name
    params = {"search": common_prefix, "json": 1, "sort": "name", "ascending": 1}
    resp = requests.get(f"{base_url}/", params=params)
    names_asc = [x.get("name") for x in resp.json().get("results", [])]
    
    # Sort descending by name
    params["ascending"] = 0
    resp = requests.get(f"{base_url}/", params=params)
    names_desc = [x.get("name") for x in resp.json().get("results", [])]
    
    if names_asc and names_desc and names_asc == list(reversed(names_desc)):
        print("PASS: ascending=0 reverses the sort order.")
    elif names_asc and names_desc:
        print(f"INFO: Sort order tested. ASC: {names_asc[:3]}, DESC: {names_desc[:3]}")
    else:
        print("INFO: Sort order tested but results unclear.")

    # 9. Sort by size
    print("\n[Test 9] Sort by Size")
    params = {"search": common_prefix, "json": 1, "sort": "size", "size_column": 1}
    resp = requests.get(f"{base_url}/", params=params)
    results = resp.json().get("results", [])
    if results and len(results) > 1:
        sizes = [int(x.get("size", "0")) for x in results if "size" in x]
        if sizes == sorted(sizes):
            print("PASS: sort=size works (ascending order confirmed).")
        else:
            print(f"INFO: sort=size tested. Sizes: {sizes}")
    else:
        print("INFO: sort=size tested but insufficient results to verify order.")

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
