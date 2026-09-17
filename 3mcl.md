# The published site serves no Content-Security-Policy
kind: todo
created: 2026-09-17T18:03Z

- 2026-09-17T18:03Z Escaping (this.i @twdcue2y) closes the stored-XSS injection at every sink in site.py, but the site has no defence in depth behind it: no CSP header and no meta http-equiv. GitHub Pages cannot set headers, so this needs either a meta tag injected into the Zensical template or a fronting CDN. A future sink added to site.py that forgets to escape has nothing to stop it.
