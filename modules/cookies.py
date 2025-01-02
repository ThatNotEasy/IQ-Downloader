import http.cookiejar as cookiejar

def load_cookies(cookies_file):
    cj = cookiejar.MozillaCookieJar()

    try:
        cj.load(cookies_file, ignore_discard=True, ignore_expires=True)
        print(f"Loaded {len(cj)} cookies from {cookies_file}")
    except FileNotFoundError:
        print(f"File not found: {cookies_file}")
    except Exception as e:
        print(f"Error loading cookies: {e}")

    # Convert cookies to a dictionary
    cookies_dict = {cookie.name: cookie.value for cookie in cj}
    return cookies_dict