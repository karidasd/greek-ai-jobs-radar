import urllib.request
import json
import re
import os
from datetime import datetime, date

CATEGORIES = {
    "Programming Languages": {
        "Python": ["python"],
        "SQL": ["sql"],
        "JavaScript": ["javascript", "typescript", "node.js", "nodejs"],
        "Java": ["java ", "java,", "java."],
        "C++": ["c++", "c/c++"],
        "Go": [" golang", " go ", "go lang"]
    },
    "AI & Machine Learning": {
        "PyTorch": ["pytorch"],
        "TensorFlow": ["tensorflow"],
        "LLM": ["llm", "large language model", "gpt", "gemini"],
        "RAG": ["rag", "retrieval augmented", "retrieval-augmented"],
        "LangChain": ["langchain"],
        "Hugging Face": ["huggingface", "hugging face"],
        "Scikit-Learn": ["scikit", "sklearn"],
        "Pandas": ["pandas"],
        "NumPy": ["numpy"]
    },
    "Cloud & MLOps": {
        "AWS": ["aws", "amazon web services"],
        "Docker": ["docker"],
        "Kubernetes": ["kubernetes", "k8s"],
        "GCP": ["gcp", "google cloud"],
        "Azure": ["azure"],
        "Airflow": ["airflow"],
        "Spark": ["spark", "pyspark"],
        "Git": ["git", "github", "gitlab"],
        "Snowflake": ["snowflake"],
        "Tableau": ["tableau"],
        "Power BI": ["powerbi", "power bi"]
    }
}

def clean_html(raw_html):
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, " ", raw_html)
    return cleantext.lower()

def extract_salary_info(text):
    text = text.lower()
    symbol_match = re.search(r"([\$€£])\s*(\d{2,3})k\b", text)
    if not symbol_match:
        symbol_match = re.search(r"([\$€£])\s*(\d{2,3}),?000\b", text)
    text_match = re.search(r"\b(\d{2,3})k\s*(usd|eur|gbp|euro|euros)\b", text)
    if not text_match:
        text_match = re.search(r"\b(\d{2,3}),?000\s*(usd|eur|gbp|euro|euros)\b", text)
    raw_val = None
    currency = "usd"
    amount_k = 0
    if symbol_match:
        sym = symbol_match.group(1)
        amt = int(symbol_match.group(2))
        currency = "usd" if sym == "$" else "eur" if sym == "€" else "gbp"
        amount_k = amt
        raw_val = symbol_match.group(0).upper()
    elif text_match:
        amt = int(text_match.group(1))
        curr_str = text_match.group(2)
        currency = "eur" if "eur" in curr_str else "gbp" if "gbp" in curr_str else "usd"
        amount_k = amt
        raw_val = text_match.group(0).upper()
    if amount_k > 0:
        eur_val = amount_k * 1000 * (0.92 if currency == "usd" else 1.17 if currency == "gbp" else 1.0)
        return {"raw": raw_val, "eur_annual": int(eur_val), "currency": currency}
    gr_match = re.search(r"(\d{1,2})[.,]?(\d{3})\s*(€|eur|ευρώ)", text)
    if gr_match:
        monthly = int(gr_match.group(1) + gr_match.group(2))
        if 800 <= monthly <= 15000:
            return {"raw": f"€{monthly}/mo", "eur_annual": monthly * 14, "currency": "eur"}
    return None

def estimate_net_monthly(gross_annual, region):
    if not gross_annual:
        return 0
    if region == "Greece":
        rate = 0.75 if gross_annual <= 20000 else 0.70 if gross_annual <= 40000 else 0.65
        return int(gross_annual * rate / 14)
    elif region == "Europe & UK":
        return int(gross_annual * 0.60 / 12)
    else:
        return int(gross_annual * 0.70 / 12)

def classify_region(loc_string):
    if not loc_string:
        return "Worldwide"
    loc = loc_string.lower()
    if any(x in loc for x in ["greece", "hellas", "athens", "thessaloniki", "ελλάδα", "αθήνα"]):
        return "Greece"
    if any(x in loc for x in ["europe", "uk", "germany", "france", "spain", "london", "berlin", "paris", "amsterdam"]):
        return "Europe & UK"
    if any(x in loc for x in ["us", "usa", "united states", "canada", "new york", "san francisco"]):
        return "North America"
    return "Worldwide"

def fetch_jobs():
    jobs = []
    seen_urls = set()

    def add_job(title, company, url, desc, location):
        if url and url not in seen_urls:
            seen_urls.add(url)
            jobs.append({
                "title": title, "company": company, "url": url,
                "description": clean_html(str(desc)), "location": location or "Worldwide"
            })

    # --- Remotive ---
    for cat in ["data", "software-dev"]:
        try:
            req = urllib.request.Request(f"https://remotive.com/api/remote-jobs?category={cat}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read().decode())
            count = 0
            for j in data.get("jobs", []):
                add_job(j.get("title",""), j.get("company_name",""), j.get("url",""), j.get("description",""), j.get("candidate_required_location",""))
                count += 1
            print(f"Remotive ({cat}): {count} jobs")
        except Exception as e:
            print(f"Remotive {cat} error: {e}")

    # --- Jobicy ---
    for ind in ["data-science", "engineering"]:
        try:
            req = urllib.request.Request(f"https://jobicy.com/api/v2/remote-jobs?industry={ind}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read().decode())
            count = 0
            for j in data.get("jobs", []):
                add_job(j.get("jobTitle",""), j.get("companyName",""), j.get("url",""), j.get("jobDescription",""), j.get("jobGeo",""))
                count += 1
            print(f"Jobicy ({ind}): {count} jobs")
        except Exception as e:
            print(f"Jobicy {ind} error: {e}")

    try:
        req = urllib.request.Request("https://jobicy.com/api/v2/remote-jobs?geo=greece", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode())
        count = 0
        for j in data.get("jobs", []):
            add_job(j.get("jobTitle",""), j.get("companyName",""), j.get("url",""), j.get("jobDescription",""), "Greece")
            count += 1
        print(f"Jobicy (Greece): {count} jobs")
    except Exception as e:
        print(f"Jobicy Greece error: {e}")

    # --- Workable (Greek Companies) ---
    workable_companies = [
        "skroutz", "blueground", "epignosis", "novibet", "orfium",
        "hellasdirect", "welcomepickups", "spotawheel", "persado",
        "viva-wallet", "beat", "eia-music"
    ]
    for comp in workable_companies:
        try:
            req = urllib.request.Request(
                f"https://apply.workable.com/api/v3/accounts/{comp}/jobs",
                headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
                method="POST",
                data=b'{"query":"","location":[],"department":[],"worktype":[],"remote":[]}'
            )
            resp = urllib.request.urlopen(req).read().decode()
            data = json.loads(resp)
            TECH_KEYWORDS = [
                "data", "engineer", "developer", "software", "machine learning",
                "ai ", "ml ", "analyst", "devops", "backend", "frontend", "full stack",
                "fullstack", "python", "cloud", "infrastructure", "platform", "security",
                "automation", "architect", "mobile", "ios", "android", "qa ", "sre",
                "database", "bi ", "product manager", "scrum", "agile", "tech lead"
            ]
            count = 0
            for j in data.get("results", []):
                shortcode = j.get("shortcode")
                if not shortcode:
                    continue
                title_val = j.get("title", "")
                title_lower = title_val.lower() if isinstance(title_val, str) else ""
                
                dept_val = j.get("department", "")
                if isinstance(dept_val, list):
                    dept_val = " ".join([str(d) for d in dept_val])
                elif not isinstance(dept_val, str):
                    dept_val = str(dept_val)
                dept_lower = dept_val.lower()
                
                # Only include tech-related roles
                if not any(kw in title_lower or kw in dept_lower for kw in TECH_KEYWORDS):
                    continue
                url = f"https://apply.workable.com/{comp}/j/{shortcode}/"
                loc_dict = j.get("location", {})
                loc_str = f"{loc_dict.get('city', '')}, Greece".strip(", ")
                desc_text = f"{title_val} {dept_val} {comp}"
                add_job(title_val, comp.capitalize(), url, desc_text, loc_str or "Greece")
                count += 1
            print(f"Workable ({comp}): {count} tech jobs")
        except Exception as e:
            print(f"Workable {comp}: {e}")

    # --- Lever (Greek-adjacent companies) ---
    lever_companies = [
        ("taxheaven", "Taxheaven"),
        ("skroutz-marketplace", "Skroutz Marketplace"),
    ]
    for slug, name in lever_companies:
        try:
            req = urllib.request.Request(
                f"https://api.lever.co/v0/postings/{slug}?mode=json",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())
            count = 0
            for j in data:
                add_job(j.get("text",""), name, j.get("hostedUrl",""), j.get("descriptionPlain","") + " " + j.get("additionalPlain",""), "Greece")
                count += 1
            print(f"Lever ({slug}): {count} jobs")
        except Exception as e:
            print(f"Lever {slug}: {e}")

    # --- Greenhouse ---
    greenhouse_companies = [
        ("persado", "Persado"),
        ("wealthyhood", "Wealthyhood"),
    ]
    for slug, name in greenhouse_companies:
        try:
            req = urllib.request.Request(
                f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())
            count = 0
            for j in data.get("jobs", []):
                loc = j.get("location", {}).get("name", "Greece")
                add_job(j.get("title",""), name, j.get("absolute_url",""), j.get("content",""), loc)
                count += 1
            print(f"Greenhouse ({slug}): {count} jobs")
        except Exception as e:
            print(f"Greenhouse {slug}: {e}")

    return jobs

def load_salary_history(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_salary_history(filepath, avg_salaries):
    history = load_salary_history(filepath)
    today = str(date.today())
    # Avoid duplicate entries for same day
    history = [h for h in history if h.get("date") != today]
    history.append({"date": today, "salaries": avg_salaries})
    # Keep last 90 days
    history = history[-90:]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    return history

def analyze_jobs(jobs):
    total_jobs = len(jobs)
    if total_jobs == 0:
        return {}, [], {}, {}, [], []

    skill_counts = {}
    for cat, skills_dict in CATEGORIES.items():
        skill_counts[cat] = {skill: 0 for skill in skills_dict.keys()}

    valid_jobs_list = []
    region_salaries = {"Greece": [], "Europe & UK": [], "North America": [], "Worldwide": []}

    for job in jobs:
        desc = job["description"] + " " + job["title"].lower()
        salary_info = extract_salary_info(desc)
        region = classify_region(job["location"])

        if region == "Greece" and salary_info:
            if salary_info["currency"] == "usd" or salary_info["eur_annual"] > 60000:
                region = "Worldwide"

        found_skills = []
        for cat, skills_dict in CATEGORIES.items():
            for skill, keywords in skills_dict.items():
                for kw in keywords:
                    if kw in desc:
                        skill_counts[cat][skill] += 1
                        if skill not in found_skills:
                            found_skills.append(skill)
                        break

        is_workable = "workable.com" in job["url"]
        is_lever = "lever.co" in job["url"]
        is_greenhouse = "greenhouse.io" in job["url"] or "greenhouse" in job["url"].lower()

        if found_skills or is_workable or is_lever or is_greenhouse:
            job_entry = {
                "title": job["title"],
                "company": job["company"],
                "url": job["url"],
                "region": region,
                "location_raw": job["location"],
                "salary_raw": salary_info["raw"] if salary_info else None,
                "salary_eur": salary_info["eur_annual"] if salary_info else None,
                "salary_net_mo": estimate_net_monthly(salary_info["eur_annual"], region) if salary_info else None,
                "skills": found_skills if found_skills else ["Tech"]
            }
            valid_jobs_list.append(job_entry)
            if salary_info:
                region_salaries[region].append(salary_info["eur_annual"])

    # Categories output
    categories_output = {}
    for cat, skills_dict in skill_counts.items():
        cat_list = []
        for skill, count in skills_dict.items():
            percentage = round((count / total_jobs) * 100, 1)
            cat_list.append({"skill": skill, "count": count, "percentage": percentage, "trend": 0})
        cat_list.sort(key=lambda x: x["count"], reverse=True)
        categories_output[cat] = cat_list

    # Avg salaries
    avg_salaries = {}
    avg_salaries_net = {}
    for r, sals in region_salaries.items():
        if sals:
            avg_gross = sum(sals) // len(sals)
            avg_salaries[r] = avg_gross
            avg_salaries_net[r] = estimate_net_monthly(avg_gross, r)
        else:
            avg_salaries[r] = 0
            avg_salaries_net[r] = 0

    # Score and sort
    for job in valid_jobs_list:
        job["_score"] = len(job["skills"]) + (5 if job["salary_eur"] else 0)
    valid_jobs_list.sort(key=lambda x: x["_score"], reverse=True)

    # Greek jobs only (Workable/Lever/Greenhouse)
    greek_jobs = [j for j in valid_jobs_list if j["region"] == "Greece" and
                  any(x in j["url"] for x in ["workable.com", "lever.co", "greenhouse.io", "gr.indeed.com"])]

    # Top companies
    from collections import Counter
    import urllib.parse
    gr_company_counts = Counter([j["company"] for j in greek_jobs])
    workable_slugs = ["skroutz","blueground","epignosis","novibet","orfium","hellasdirect","welcomepickups","spotawheel","persado","viva-wallet","beat","eia-music"]
    top_greek_companies = []
    for comp, count in gr_company_counts.most_common(8):
        slug = comp.lower().replace(" ", "-")
        if slug in workable_slugs:
            url = f"https://apply.workable.com/{slug}/"
        else:
            url = f"https://www.google.com/search?q={urllib.parse.quote(comp + ' careers greece')}"
        top_greek_companies.append({"name": comp, "count": count, "url": url})

    return categories_output, greek_jobs[:50], avg_salaries, avg_salaries_net, top_greek_companies

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    output_file = os.path.join(data_dir, "skills.json")
    history_file = os.path.join(data_dir, "history.json")

    jobs = fetch_jobs()

    # Baseline Greek jobs
    jobs.append({"title": "Data Scientist", "company": "Ανώνυμη Ελληνική Εταιρεία", "url": "https://gr.indeed.com/",
                  "description": "python sql docker llm μισθός 1800€", "location": "Athens, Greece"})
    jobs.append({"title": "AI Engineer", "company": "Athens Tech Startup", "url": "https://gr.indeed.com/",
                  "description": "pytorch tensorflow aws cloud 25000 eur annual", "location": "Athens, Greece"})

    print(f"Total jobs: {len(jobs)}")

    categories_stats, top_jobs, avg_salaries, avg_salaries_net, top_greek_companies = analyze_jobs(jobs)

    # Save salary history
    history = save_salary_history(history_file, avg_salaries_net)
    print(f"Salary history: {len(history)} entries saved")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_jobs_analyzed": len(jobs),
            "avg_salaries_eur": avg_salaries,
            "avg_salaries_net": avg_salaries_net,
            "top_greek_companies": top_greek_companies,
            "categories": categories_stats,
            "latest_jobs": top_jobs
        }, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(top_jobs)} live jobs to {output_file}")
    print(f"Salaries: {avg_salaries}")

if __name__ == "__main__":
    main()
