# N211WP maintenance tracker (public, read-only)

Static snapshot of Wayne McClelland's N211WP maintenance tracker, published at
https://n211wp-maintenance-tracker.netlify.app. Netlify deploys `site/` on every push to `main` (no build step).

To rebuild: refresh the JSON files in `data/` from the tracker's datasets (same file shapes), update `data/lede.txt`, then

    python3 tools/build_site.py --version X.Y --refreshed dd-Mon-yyyy --published dd-Mon-yyyy --lede-file data/lede.txt

and commit `data/` and `site/`. The page has no backend: it is read-only by construction.
