import requests
import argparse
import sys
import os
import time
import json

def setup_test_files():
    """Create a set of temporary files for testing search."""
    cwd = os.getcwd()
    files = {
        "verify_json_alpha.txt": "content alpha",
        "verify_json_beta.txt": "content beta",
        "verify_json_gamma.txt": "content gamma",
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

def test_json_search_api(base_url):
    print(f"Testing JSON Search API at {base_url}")
    
    # 1. Basic JSON Structure & json=1
    print("\n[Test 1] Basic JSON Structure (json=1)")
    params = {"search": "verify_json_alpha.txt", "json": 1}
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
        # print(resp.text[:500])
        return False
        
    if "totalResults" not in data or "results" not in data:
        print(f"FAIL: Missing 'totalResults' or 'results' in JSON: {data.keys()}")
        return False
        
    print(f"PASS: Got valid JSON with totalResults={data['totalResults']}")
    
    # Check content
    found = False
    for item in data["results"]:
        if item.get("name") == "verify_json_alpha.txt":
            found = True
            break
    if found:
        print("PASS: Found expected file in results.")
    else:
        print("FAIL: Expected file not found in results.")
        return False


    # 2. Count, Offset, Sort
    print("\n[Test 2] Count, Offset, Sort")
    params = {
        "search": "verify_json_", 
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
    
    if "verify_json_alpha.txt" in names and "verify_json_beta.txt" in names:
        if "verify_json_gamma.txt" not in names:
             print("PASS: Count limit works.")
        else:
             print("FAIL: Count limit issue (found gamma).")
             return False
    else:
        print("FAIL: Sorting or finding issue.")
        return False

    # Offset
    params["offset"] = 2
    resp = requests.get(f"{base_url}/", params=params)
    data = resp.json()
    names_offset = [x.get("name") for x in data.get("results", [])]
    if "verify_json_gamma.txt" in names_offset:
        print("PASS: Offset works.")
    else:
        print(f"FAIL: Offset did not return expected gamma. Got: {names_offset}")
        return False


    # 3. Columns (path, size, date_modified)
    print("\n[Test 3] Columns (path, size, date_modified)")
    # Request extra columns
    params = {
        "search": "verify_json_alpha.txt", 
        "json": 1,
        "path_column": 1,
        "size_column": 1,
        "date_modified_column": 1,
        "date_created_column": 1 # Check if server supports it or ignores it
    }
    resp = requests.get(f"{base_url}/", params=params)
    data = resp.json()
    if not data["results"]:
        print("FAIL: No results for column test.")
        return False
        
    item = data["results"][0]
    print(f"DEBUG: Item keys: {item.keys()}")
    
    if "path" in item:
        print("PASS: 'path' column present.")
    else:
        print("FAIL: 'path' column missing.")
        return False

    if "size" in item:
        val = item["size"]
        # Schema says it might be string or int found in wild, but schema defines oneOf string/int.
        # My schema note says "observed as string".
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

    # date_created check
    if "date_created" in item:
        print(f"INFO: 'date_created' IS supported! Value: {item['date_created']}")
    else:
        print("INFO: 'date_created' not returned (as expected per schema notes).")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Everything JSON Search API")
    parser.add_argument("--url", default="http://127.160.164.78:8000", help="Base URL")
    args = parser.parse_args()
    
    created_files = setup_test_files()
    try:
        if test_json_search_api(args.url):
            print("\nAll JSON Search API tests passed!")
        else:
            print("\nSome tests failed.")
            sys.exit(1)
    finally:
        teardown_test_files(created_files)
