"""Fetch jobs from public job-board APIs and write docs/jobs.json. Standard library only."""
import datetime, html, json, pathlib, re, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "jobs.json"
UA = {"User-Agent": "job-agent/1.0 (personal job search)"}
KEEP_DAYS = 21


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def strip(h):
    h = html.unescape(h or "")
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h)).strip()


def greenhouse(token, cfg):
    for j in get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true").get("jobs", []):
        yield dict(id=f"gh:{token}:{j['id']}", source="greenhouse", company=token, title=j["title"],
                   location=(j.get("location") or {}).get("name", ""), url=j["absolute_url"],
                   description=strip(j.get("content")))


def lever(token, cfg):
    for j in get(f"https://api.lever.co/v0/postings/{token}?mode=json"):
        yield dict(id=f"lv:{token}:{j['id']}", source="lever", company=token, title=j["text"],
                   location=(j.get("categories") or {}).get("location", ""), url=j["hostedUrl"],
                   description=j.get("descriptionPlain", ""))


def ashby(token, cfg):
    for j in get(f"https://api.ashbyhq.com/posting-api/job-board/{token}").get("jobs", []):
        yield dict(id=f"ab:{token}:{j['id']}", source="ashby", company=token, title=j["title"],
                   location=j.get("location") or "", url=j.get("jobUrl", ""),
                   description=j.get("descriptionPlain") or strip(j.get("descriptionHtml")))


def remotive(_, cfg):
    for term in cfg.get("remotive_searches", []):
        for j in get("https://remotive.com/api/remote-jobs?search=" + urllib.parse.quote(term)).get("jobs", []):
            yield dict(id=f"rv:{j['id']}", source="remotive", company=j["company_name"], title=j["title"],
                       location=j.get("candidate_required_location", ""), url=j["url"],
                       description=strip(j.get("description")))


def remoteok(_, cfg):
    for j in get("https://remoteok.com/api"):
        if "position" not in j:
            continue  # first element is a legal notice
        yield dict(id=f"ro:{j['id']}", source="remoteok", company=j.get("company", ""), title=j["position"],
                   location=j.get("location") or "", url=j.get("url", ""),
                   description=strip(j.get("description")))


FETCHERS = dict(greenhouse=greenhouse, lever=lever, ashby=ashby, remotive=remotive, remoteok=remoteok)


def matches(job, cfg):
    title, loc = job["title"].lower(), (job["location"] or "").lower()
    targets = [t.lower() for t in cfg.get("target_titles", [])]
    if targets and not any(t in title for t in targets):
        return False
    if any(x.lower() in title + " " for x in cfg.get("exclude_keywords", [])):
        return False
    if any(x.lower() in loc for x in cfg.get("exclude_locations", [])):
        return False
    locs = [l.lower() for l in cfg.get("locations", [])]
    return not (locs and loc and not any(l in loc for l in locs))


def main():
    cfg = json.loads((ROOT / "config.json").read_text())
    today = datetime.date.today()
    old = {}
    if OUT.exists():
        try:
            old = {j["id"]: j for j in json.loads(OUT.read_text()).get("jobs", [])}
        except Exception:
            pass
    fresh, errors = {}, []
    for s in cfg["sources"]:
        label = s["type"] + (":" + s["token"] if s.get("token") else "")
        try:
            for j in FETCHERS[s["type"]](s.get("token"), cfg):
                if matches(j, cfg):
                    j["description"] = j["description"][:5000]
                    j["last_seen"] = today.isoformat()
                    fresh[j["id"]] = j
        except Exception as e:
            errors.append(f"{label}: {e}")
    cutoff = (today - datetime.timedelta(days=KEEP_DAYS)).isoformat()
    kept = {k: v for k, v in old.items() if v.get("last_seen", "") >= cutoff}
    jobs = sorted({**kept, **fresh}.values(), key=lambda j: j["last_seen"], reverse=True)
    OUT.write_text(json.dumps(
        {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(), "errors": errors, "jobs": jobs}, indent=1))
    print(f"{len(fresh)} matching now, {len(jobs)} total, {len(errors)} source errors")
    for e in errors:
        print("  !", e)


if __name__ == "__main__":
    main()
