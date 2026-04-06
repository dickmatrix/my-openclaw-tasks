# Bypass Protocol for GitHub Access (from luz)

When `web_fetch` target includes `github.com` and returns Blocked/Timed-out:

## URL Rewriting Rules

1. **Clone**: `https://github.com/{user}/{repo}` → `https://ghproxy.com/https://github.com/{user}/{repo}.git`
2. **Raw file**: `https://raw.githubusercontent.com/{user}/{repo}/main/{file}` → `https://raw.gitmirror.com/{user}/{repo}/main/{file}`
3. **Clone command**: `git clone --depth 1 {mirrored_url} ./workspace/temp_repo`

## Direct Raw Access (curl works)
`raw.githubusercontent.com` is accessible via curl directly.

## Note
- Kimi API (web_search) has 401 auth error on this system
- GitHub raw content accessible via curl
- GitHub API/clone may be rate-limited
