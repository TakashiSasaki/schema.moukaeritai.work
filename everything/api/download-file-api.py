"""
Everything HTTP Server - Download API Verification Script

This script verifies the behavior of the Everything HTTP Server's file download API
against the OpenAPI expectations. It performs a series of tests to ensure that
file downloads, path encoding, and special character handling work as expected.

Usage:
    python everything/api/download-file-api.py [--url http://host:port]

Dependencies:
    - requests
    - beautifulsoup4 (implied for HTML parsing in other scripts, though this script uses regex/strings mostly)

Tests performed:
    1. Browser Style Path (e.g., /C%3A/Windows/win.ini)
    2. Single Segment Path (e.g., /C%3A%2FWindows%2Fwin.ini)
    3. Range Requests (Partial Content 206)
    4. Non-existent file handling (404)
    5. Special characters in filenames
    6. Space encoding (percent-encoded vs literal)
    7. Multi-byte/Non-ASCII filenames (Japanese), including:
       - Direct access via UTF-8 encoded URL
       - Discovery via Search API to confirm server-generated link format
"""

__author__ = "Takashi Sasaki"
__contact__ = "https://x.com/TakashiSasaki"
__version__ = "1.4.0"

import requests
import argparse
import sys
import os
import time

def test_everything_api(base_url):
    """
    Run the full suite of verification tests against the given base_url.
    
    Args:
        base_url (str): The base URL of the Everything HTTP Server (e.g., "http://127.0.0.1:80").
    """
    print(f"Testing Everything API at {base_url}")
    
    # Ensure standard Windows file exists for testing
    test_file_path = r"C:\Windows\win.ini"
    if not os.path.exists(test_file_path):
        print(f"Warning: {test_file_path} not found locally. Verification comparisons might fail if server is running on this same machine.")
    else:
        with open(test_file_path, 'rb') as f:
            local_content = f.read()

    # Test 1: Download existing file (Browser Style)
    # /C%3A/Windows/win.ini
    path_1 = "/C%3A/Windows/win.ini"
    url_1 = f"{base_url}{path_1}"
    print(f"\n[Test 1] GET {url_1} (Browser Style)")
    try:
        resp_1 = requests.get(url_1)
        print(f"Status: {resp_1.status_code}")
        if resp_1.status_code == 200:
            print("Success: Got 200 OK")
            if 'local_content' in locals() and resp_1.content == local_content:
                print("Success: Content matches local file")
            elif 'local_content' in locals():
                print("Failure: Content verification failed!")
                print(f"Local len: {len(local_content)}, Remote len: {len(resp_1.content)}")
        else:
            print(f"Failure: Expected 200, got {resp_1.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Download existing file (Single Segment Style)
    # /C%3A%2FWindows%2Fwin.ini
    path_2 = "/C%3A%2FWindows%2Fwin.ini"
    url_2 = f"{base_url}{path_2}"
    print(f"\n[Test 2] GET {url_2} (Single Segment Style)")
    try:
        resp_2 = requests.get(url_2)
        print(f"Status: {resp_2.status_code}")
        if resp_2.status_code == 200:
            print("Success: Got 200 OK")
            if 'local_content' in locals() and resp_2.content == local_content:
                print("Success: Content matches local file")
            elif 'local_content' in locals():
                print("Failure: Content verification failed!")
        else:
            print(f"Failure: Expected 200, got {resp_2.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 3: Range Request
    print(f"\n[Test 3] GET {url_1} with Range: bytes=0-4")
    try:
        headers = {"Range": "bytes=0-4"}
        resp_3 = requests.get(url_1, headers=headers)
        print(f"Status: {resp_3.status_code}")
        if resp_3.status_code == 206:
            print("Success: Got 206 Partial Content")
            print(f"Content-Length: {resp_3.headers.get('Content-Length')}")
            print(f"Content-Range: {resp_3.headers.get('Content-Range')}")
            if len(resp_3.content) == 5:
                print("Success: Received exactly 5 bytes")
            else:
                print(f"Failure: Received {len(resp_3.content)} bytes, expected 5")
        elif resp_3.status_code == 200:
            print("Warning: Server returned 200 OK (Range ignored?)")
        else:
            print(f"Failure: Expected 206, got {resp_3.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 4: Non-existent file
    # /C%3A/Windows/non_existent_file_12345.txt
    path_4 = "/C%3A/Windows/non_existent_file_12345.txt"
    url_4 = f"{base_url}{path_4}"
    print(f"\n[Test 4] GET {url_4} (Non-existent)")
    try:
        resp_4 = requests.get(url_4)
        print(f"Status: {resp_4.status_code}")
        if resp_4.status_code == 404:
            print("Success: Got 404 Not Found")
        else:
            print(f"Failure: Expected 404, got {resp_4.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # --- Extended Tests for Encoding Rules ---
    print("\n--- Extended Encoding Tests ---")
    
    # helper to create a test file
    def create_test_file(filename, content=b"test content"):
        full_path = os.path.join(os.getcwd(), filename)
        with open(full_path, "wb") as f:
            f.write(content)
        return full_path

    # Test 5: Special characters allowed as-is
    # Spec says: '-', '_', '.', '!', '~', '*', "'", '(', ')' are valid as-is.
    # We will create a file with these chars.
    special_filename = "test_specials_!~'()_.txt"
    create_test_file(special_filename)
    
    # Construct path: Current dir + filename. 
    # Current dir needs to be encoded. We know current dir is straightforward usually, 
    # but let's handle it carefully. 
    # Ideally we just test the filename part if we can, but Everything serves absolute paths.
    # Let's verify where we are.
    # simplistic "browser style" encoding for the common CWD parts
    cwd = os.getcwd()
    print(f"DEBUG: CWD is {cwd}")
    
    # Force uppercase drive letter just in case Everything is picky
    if len(cwd) > 1 and cwd[1] == ':':
        cwd = cwd[0].upper() + cwd[1:]

    cwd_enc = cwd.replace(":", "%3A").replace("\\", "/")
    
    # Wait for Everything to index the new files?
    print("Waiting 15 seconds for filesystem events...")
    time.sleep(15)
    
    # Should work without encoding the specials
    # URL = Base + / + Cwd_Enc + / + SpecialFilename
    path_5 = f"/{cwd_enc}/{special_filename}"
    url_5 = f"{base_url}{path_5}"
    print(f"\n[Test 5] GET {url_5} (Specials as-is)")
    try:
        resp_5 = requests.get(url_5)
        print(f"Status: {resp_5.status_code}")
        if resp_5.status_code == 200:
            print("Success: Got 200 OK for special chars")
        else:
            print(f"Failure: Expected 200, got {resp_5.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 6: Space encoding
    # Space becomes %20.
    space_filename = "test space.txt"
    create_test_file(space_filename)
    path_6_enc = f"/{cwd_enc}/{space_filename.replace(' ', '%20')}"
    url_6_enc = f"{base_url}{path_6_enc}"
    print(f"\n[Test 6A] GET {url_6_enc} (Space manually encoded as %20)")
    try:
        resp_6 = requests.get(url_6_enc)
        print(f"Sent URL: {resp_6.url}") # Verify what requests sent
        print(f"Status: {resp_6.status_code}")
        if resp_6.status_code == 200:
            print("Success: Got 200 OK for space encoded as %20")
        else:
            print(f"Failure: Expected 200, got {resp_6.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 6B: Space literal
    path_6_lit = f"/{cwd_enc}/{space_filename}" # literal space
    url_6_lit = f"{base_url}{path_6_lit}"
    print(f"\n[Test 6B] GET .../{space_filename} (Space literal - let requests encode)")
    try:
        resp_6b = requests.get(url_6_lit)
        print(f"Sent URL: {resp_6b.url}") 
        print(f"Status: {resp_6b.status_code}")
        if resp_6b.status_code == 200:
            print("Success: Got 200 OK for literal space")
        else:
            print(f"Failure: Expected 200, got {resp_6b.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 7: Non-ASCII (Japanese)
    # Spec says: Non-ASCII bytes (>= 128) are treated as valid by implementation
    jp_filename = "日本語.txt"
    create_test_file(jp_filename)
    
    # Python requests will encode unicode in URL.
    path_7 = f"/{cwd_enc}/{jp_filename}"
    url_7 = f"{base_url}{path_7}"
    print(f"\n[Test 7] GET {url_7} (Japanese/Unicode)")
    print(f"DEBUG: Requesting URL which likely encodes '日本語' to UTF-8 percent sequences")
    try:
        resp_7 = requests.get(url_7)
        print(f"Sent URL: {resp_7.url}")
        print(f"Status: {resp_7.status_code}")
        if resp_7.status_code == 200:
            print("Success: Got 200 OK for Japanese filename")
        else:
            print(f"Failure: Expected 200, got {resp_7.status_code}")
            # Try debugging if existing works
            print("Trying to list text file content if possible (debug step skipped)")
    except Exception as e:
        print(f"Error: {e}")

    # Test 7B: Japanese with CP932 (Shift-JIS) encoding?
    # Windows native apps often use CP932.
    try:
        from urllib.parse import quote
        jp_filename_bytes_cp932 = jp_filename.encode("cp932")
        jp_enc_cp932 = quote(jp_filename_bytes_cp932)
        
        path_7b = f"/{cwd_enc}/{jp_enc_cp932}"
        url_7b = f"{base_url}{path_7b}"
        print(f"\n[Test 7B] GET {url_7b} (Japanese/CP932)")
        resp_7b = requests.get(url_7b)
        print(f"Sent URL: {resp_7b.url}")
        print(f"Status: {resp_7b.status_code}")
        if resp_7b.status_code == 200:
            print("Success: Got 200 OK for Japanese filename (CP932)")
        else:
            print(f"Failure: Expected 200, got {resp_7b.status_code}")
    except Exception as e:
        print(f"Error 7B: {e}")

    # Test 7C: Discover correct link via Search
    print(f"\n[Test 7C] Discovery: Search for '{jp_filename}' to find server-generated link")
    
    # First, verify search works at all using win.ini
    print("Verifying search with 'win.ini'...")
    try:
        r_win = requests.get(f"{base_url}/", params={"search": "win.ini"})
        if r_win.status_code == 200 and "win.ini" in r_win.text.lower():
            print("Search functionality verified (win.ini found).")
        else:
            print("Warning: Search for win.ini failed or returned 0 results. Is Everything running/indexing?")
    except:
        pass

    # Retry loop for the new file
    found_html = ""
    for attempt in range(6):
        print(f"Searching for '{jp_filename}' (Attempt {attempt+1}/6)...")
        try:
            params = {"search": jp_filename} 
            resp_search = requests.get(f"{base_url}/", params=params)
            html_text = resp_search.text
            if "合計 0 件" not in html_text and "0 results" not in html_text:
                 # It seems we have results (or at least not explicit 0)
                 # Check if our filename is in the result list (heuristic)
                 if jp_filename in html_text:
                     print("File seems to be found!")
                     found_html = html_text
                     break
        except Exception as e:
            print(f"Search request failed: {e}")
        
        time.sleep(5)
    
    if found_html:
        try:
            # Simple regex to find the link. 
            # Simple regex to find the link. 
            # Looking for <a href="/C%3A/...">...</a>
            # The file is in cwd.
            # We look for the filename in the href.
            import re
            
            # The href will likely start with / and contain encoded parts.
            # We search for the specific filename's presence in the href, 
            # or just look for the row corresponding to our file.
            # Let's just print all hrefs that look like file downloads.
            
            # Pattern: href="(/[^"]+日本語[^"]*)" 
            # Wait, if it's encoded, it won't be "日本語" in the href string.
            # We need to look for the path we expect (cwd) + filename.
            
            print("HTML snippet (first 1000 chars):")
            print(found_html[:1000])
            
            # Let's look for hrefs containing the drive letter start
            import re
            found_links = re.findall(r'href="(/[A-Za-z]%3A/[^"]+)"', found_html)
            
            target_link = None
            print(f"Found {len(found_links)} download links in search results.")
            for link in found_links:
                # Check if this link corresponds to our file.
                # naive check: does it end with .txt? and maybe checking decoding matches?
                # or just use the last one if we assume unique text?
                # We created a unique file "日本語.txt", but maybe user has others.
                # Let's filter by checking if it ends with our extension and seems relevant.
                if link.endswith(".txt"):
                    print(f"Candidate: {link}")
                    # Try to see if this is the one
                    # We can try to download it.
                    target_link = link
            
            if target_link:
                print(f"Testing discovered link: {target_link}")
                final_url = f"{base_url}{target_link}"
                resp_disc = requests.get(final_url)
                print(f"Status: {resp_disc.status_code}")
                if resp_disc.status_code == 200:
                    print("Success: Downloaded using discovered link!")
                    print(f"Discovered URL: {final_url}")
                    # Analyze the encoding
                    # Extract the filename part
                    # /C%3A/.../filename
                    filename_part = target_link.split("/")[-1]
                    print(f"Server encoded filename as: {filename_part}")
                else:
                    print(f"Failure: Link found but returned {resp_disc.status_code}")
            else:
                print("No suitable link found in search results.")
        except Exception as e:
            print(f"Error parsing search result: {e}")

    else:
        print("Search failed to find the new file after retries.")


    # Cleanup
    try:
        os.remove(special_filename)
        os.remove(space_filename)
        os.remove(jp_filename)
        print("\nCleanup: Temporary test files removed.")
    except Exception as e:
        print(f"Cleanup Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Everything HTTP Server API")
    parser.add_argument("--url", default="http://127.160.164.78:8000", help="Base URL of the Everything server")
    args = parser.parse_args()
    
    test_everything_api(args.url)
