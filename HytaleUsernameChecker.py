import time
import random
import requests
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import sys
REQUEST = "https://accounts.hytale.com/api/account/username-reservations/availability?username=" #with username at end
OUTPUT_FILE = "valid_users.out"




options = Options()
options.binary_location = "/usr/bin/firefox"
options.add_argument("--headless")
service = Service(executable_path="/usr/bin/geckodriver")
driver = webdriver.Firefox(options=options, service=service)
def get_cookies(TOKEN):
    print("Opening site to capture cookies...")
    driver.get(f"https://accounts.hytale.com/reserve?token={TOKEN}")
    
    # Wait a few seconds for Cloudflare/Kratos to settle
    time.sleep(10) 
    
    # Extract cookies from the browser session
    browser_cookies = driver.get_cookies()
    
    # Convert to dictionary format for requests
    cookie_dict = {c['name']: c['value'] for c in browser_cookies}
    return cookie_dict

def create_session_with_cookie_dict(cookies_to_add):
    """Create a session with the specific _cfuvid cookie."""
    session = requests.Session()
    
    # Add cookie to session
    session.cookies.update(cookies_to_add)
    print(f"✓ Added cookies to session")
    
    # Also set headers to match browser behavior
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest' : 'document',
        'Sec-Fetch-Mode' : 'navigate',
        'Sec-Fetch-User' : '?1',
        'Sec-GPC' : '1',
        'Upgrade-Insecure-Requests' : '1'
    })
    
    # Test the session
    print("Testing authentication...")
    test_response = session.get(REQUEST + "testusername123")
    print(f"Test response status: {test_response.status_code}")
    
    # Check if we get a proper response (not 303 redirect)
    if test_response.status_code == 303:
        print("⚠️  Still getting redirects - may need additional cookies")
        print(f"   Redirect location: {test_response.headers.get('Location', 'Unknown')}")
    elif test_response.status_code == 200:
        print("✓ Good! Getting 200 responses")
    else:
        print(f"Got status {test_response.status_code}")
    
    return session




def check_name(name, session):
    try:
        response = session.get(REQUEST + name, timeout=3)
        is_available = (response.status_code == 200)
        return (name, is_available, response.status_code)
    except requests.exceptions.RequestException as e:
        print(f"Failed on: {name} : {e}")
    except requests.exceptions.Timeout:
        print("Timeout")
    except Exception as e:
        print("Uncaught error : {e}")


def main():
    global driver
    INPUT_FILE = input("Path to input usernames\nFormat the file with one username per line: \n")
    TOKEN = input("Token from hytale username reservation url: \n") 
    kratos_token = input("Kratos session token: \n")
    cookies = get_cookies(TOKEN)
    print(cookies)
    cookies_to_add = {
        '_cfuvid': cookies['_cfuvid'],
        'ory_kratos_session' : kratos_token 
    }
    cur_session = create_session_with_cookie_dict(cookies_to_add)
    with open (INPUT_FILE, 'r') as f:
        n = [line.strip() for line in f if line.strip()]
    with open (OUTPUT_FILE, 'a') as out:
    
        if not n:
            return
    
        hits = []
    
        for i, j in enumerate(n):
            name, is_available, code = check_name(j, cur_session)
            
            print(f"{name} : {is_available} : {code}")
            if (code == 200):
                out.write(name + "\n")
                hits.append(name)
            if (code == 429):
                print("Rate limit, sleeping for 60seconds...")
                time.sleep(60)
                driver.quit()
                driver = webdriver.Firefox(options=options, service=service)
                cookies = get_cookies()
                cookies_to_add = {
                    '_cfuvid': cookies['_cfuvid'],
                    'ory_kratos_session' : kratos_token
                }
                cur_session = create_session_with_cookie_dict(cookies_to_add)
                name, is_available, code = check_name(j, cur_session)
                
                print(f"{name} : {is_available} : {code}")
                if (code == 200):
                    out.write(name + "\n")
                    hits.append(name)


    print(f"{len(hits)} hits found:")
    print(hits)




main()
