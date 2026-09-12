"""Optional local launcher. Requires Python 3; no third-party packages."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from pathlib import Path
import webbrowser

root = Path(__file__).resolve().parent
url = 'http://127.0.0.1:8787/Kureishi_ADV_Studio.html'
try:
    server = ThreadingHTTPServer(('127.0.0.1', 8787), partial(SimpleHTTPRequestHandler, directory=str(root)))
except OSError:
    print('Port 8787 is in use. Close the previous launcher, then try again.')
    input('Press Enter to close. ')
else:
    print('Kureishi ADV Studio:', url)
    print('Keep this window open. Press Ctrl+C to stop.')
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
