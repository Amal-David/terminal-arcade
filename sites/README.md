# Product landing sites

These directories are the self-contained production sources for the Bookshelf
and Polyglot landing pages. Each folder is deployed through Pagecast to its own
Cloudflare Pages project so origin-scoped crawlers and agent-readiness scanners
can assess the products independently.

```bash
node /path/to/pagecast/src/cli.js publish site sites/bookshelf \
  --project bookshelf --json

node /path/to/pagecast/src/cli.js publish site sites/polyglot \
  --project polyglot --json
```

Production URLs:

- <https://bookshelf-8dz.pages.dev/>
- <https://polyglot-5os.pages.dev/>

The `_worker.js` file in each bundle performs one narrow dynamic behavior:
requests for `/` with `Accept: text/markdown` receive that site's `llms.txt`.
Normal browser requests continue to receive `index.html` and all other paths
are served by the static asset binding.

Run `python3 scripts/validate_agent_ready_sites.py` before deploying. After a
deployment, submit each production root—not a nested Pagecast `/p/...` URL—to
`https://isitagentready.com/api/scan`.
