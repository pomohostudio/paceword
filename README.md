# fred-mcp

Local cache-and-query MCP server over the FRED API with full vintage support.
Authored on the owner's Mac; packaged on this branch so cloud environments can run it:

    command: npx
    args:    ["-y", "github:antoniosaldanhaoliveira/paceword#fred-mcp"]
    env:     FRED_API_KEY=<key>   (required; server refuses to start without it)
             FRED_DB_PATH=<path>  (optional; defaults to ~/.local/share/fred-mcp/fred.db)

Requires Node >= 22.5 (node:sqlite). Reference and usage doctrine: docs/FRED.md on the
cthmodules-audit branch — the rule that matters most: never backtest against
current-vintage data; use fred_query with as_of.
