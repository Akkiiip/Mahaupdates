"""MahaUpdate network compatibility patch for official scraper sources."""
from __future__ import annotations

from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning

TLS_FALLBACK_HOSTS = {
    "mjp.maharashtra.gov.in",
    "www.mahatransco.in",
    "mahatransco.in",
    "www.ibps.in",
    "ibps.in",
}

_ORIGINAL_REQUEST = requests.sessions.Session.request

def _host(url):
    try:
        return (urlparse(str(url)).hostname or "").lower()
    except Exception:
        return ""

def _patched_request(self, method, url, **kwargs):
    try:
        return _ORIGINAL_REQUEST(self, method, url, **kwargs)
    except requests.exceptions.SSLError:
        host = _host(url)
        if host not in TLS_FALLBACK_HOSTS:
            raise

        print(f"NETWORK WARNING: TLS verification failed for {host}; retrying official host.")
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        retry_kwargs = dict(kwargs)
        retry_kwargs["verify"] = False
        return _ORIGINAL_REQUEST(self, method, url, **retry_kwargs)

requests.sessions.Session.request = _patched_request

_ORIGINAL_SESSION_INIT = requests.Session.__init__

def _patched_session_init(self, *args, **kwargs):
    _ORIGINAL_SESSION_INIT(self, *args, **kwargs)
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=False,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    self.mount("http://", adapter)
    self.mount("https://", adapter)

requests.Session.__init__ = _patched_session_init

# Every scraper imports ``create_client`` directly from supabase.  Patching it
# here makes the shared title gate unavoidable for every current and future
# scraper launched from this repository, without relying on per-scraper lists.
try:
    import supabase
    from notification_validation import validated_create_client
    supabase.create_client = validated_create_client(supabase.create_client)
except ImportError:
    # Allows lightweight tools that do not install scraper dependencies to run.
    pass
