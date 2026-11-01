"""Rewrites the project section of README.md with your most recent and biggest repos."""
import json, os, re, urllib.request
from concurrent.futures import ThreadPoolExecutor

USER = os.environ.get("GH_USER", "raiyan019")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
EXCLUDE = {USER.lower(), "idk"}          # profile repo + any repo you never want shown
N_RECENT, N_BIG = 3, 3
START, END = "<!--PROJECTS:START-->", "<!--PROJECTS:END-->"


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def code_bytes(repo):
    try:
        return sum(api(f"/repos/{USER}/{repo['name']}/languages").values())
    except Exception:
        return 0


def card(name):
    url = (f"https://github-readme-stats.vercel.app/api/pin/?username={USER}&repo={name}"
           "&theme=tokyonight&hide_border=true&bg_color=0D1117&title_color=7aa2f7&icon_color=bb9af7")
    return (f'<a href="https://github.com/{USER}/{name}">'
            f'<img src="{url}" alt="{name}" /></a>')


def grid(repos):
    rows = []
    for i in range(0, len(repos), 2):
        cells = "".join(f'<td width="50%" align="center">{card(r["name"])}</td>' for r in repos[i:i + 2])
        rows.append(f"  <tr>{cells}</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def build():
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner")
             if not r["fork"] and not r["archived"] and r["name"].lower() not in EXCLUDE]
    recent = sorted(repos, key=lambda r: r["pushed_at"], reverse=True)[:N_RECENT]
    taken = {r["name"] for r in recent}
    with ThreadPoolExecutor(8) as ex:
        sizes = list(ex.map(code_bytes, repos))
    ranked = sorted(zip(repos, sizes), key=lambda t: t[1], reverse=True)
    big = [r for r, s in ranked if s > 0 and r["name"] not in taken][:N_BIG]
    return (f"{START}\n\n### 🔥 Recently Active\n\n{grid(recent)}\n\n"
            f"### 🏗️ Biggest Builds <sub>(most lines of code)</sub>\n\n{grid(big)}\n\n{END}")


if __name__ == "__main__":
    text = open("README.md", encoding="utf-8").read()
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: build(), text, flags=re.S)
    open("README.md", "w", encoding="utf-8").write(new)
