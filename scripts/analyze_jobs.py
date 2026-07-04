import urllib.request
import json
import re
import os
from datetime import datetime

CATEGORIES = {
    "Programming Languages": {
        "Python": ["python"],
        "SQL": ["sql"],
        "R": [" r ", " r,", " r.", ">r<", ">r ", " r\n"],
        "Java": ["java ", "java,", "java."],
        "C++": ["c++", "c/c++"]
    },
    "AI & Machine Learning": {
        "PyTorch": ["pytorch"],
        "TensorFlow": ["tensorflow", " tf ", " tf,", " tf."],
        "LLM": ["llm", "large language model", "gpt"],
        "RAG": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
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
        "Airflow": ["airflow", "apache airflow"],
        "Spark": ["spark", "pyspark"],
        "Git": ["git", "github", "gitlab"],
        "Snowflake": ["snowflake"],
        "Tableau": ["tableau"],
        "Power BI": ["powerbi", "power bi"]
    }
}

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', raw_html)
    return cleantext.lower()

def extract_salary_info(text):
    text = text.lower()
    
    symbol_match = re.search(r'([\$€£])\s*(\d{2,3})k\b', text)
    if not symbol_match:
        symbol_match = re.search(r'([\$€£])\s*(\d{2,3}),?000\b', text)
        
    text_match = re.search(r'\b(\d{2,3})k\s*(usd|eur|gbp|euro|euros)\b', text)
    if not text_match:
        text_match = re.search(r'\b(\d{2,3}),?000\s*(usd|eur|gbp|euro|euros)\b', text)

    raw_val = None
    currency = 'usd'
    amount_k = 0

    if symbol_match:
        sym = symbol_match.group(1)
        amt = int(symbol_match.group(2))
        currency = 'usd' if sym == '$' else 'eur' if sym == '€' else 'gbp'
        amount_k = amt
        raw_val = symbol_match.group(0).upper()
    elif text_match:
        amt = int(text_match.group(1))
        curr_str = text_match.group(2)
        currency = 'eur' if 'eur' in curr_str else 'gbp' if 'gbp' in curr_str else 'usd'
        amount_k = amt
        raw_val = text_match.group(0).upper()
        
    if amount_k > 0:
        if currency == 'usd':
            eur_val = amount_k * 1000 * 0.92
        elif currency == 'gbp':
            eur_val = amount_k * 1000 * 1.17
        else:
            eur_val = amount_k * 1000
            
        return {"raw": raw_val, "eur_annual": int(eur_val), "currency": currency}
        
    # Check for monthly Greek/EU salaries e.g., 2000€, 2.500 ευρώ, 2000 eur
    gr_match = re.search(r'(\d{1,2})[.,]?(\d{3})\s*(€|eur|ευρώ)', text)
    if gr_match:
        thousands = gr_match.group(1)
        hundreds = gr_match.group(2)
        monthly = int(thousands + hundreds)
        if 800 <= monthly <= 15000:
            return {"raw": f"€{monthly}/mo", "eur_annual": monthly * 14, "currency": "eur"}
            
    return None

def estimate_net_monthly(gross_annual, region):
    if not gross_annual:
        return 0
    if region == "Greece":
        # 14 salaries, ~30-35% deductions
        if gross_annual <= 20000:
            net = gross_annual * 0.75
        elif gross_annual <= 40000:
            net = gross_annual * 0.70
        else:
            net = gross_annual * 0.65
        return int(net / 14)
    elif region == "Europe & UK":
        # 12 salaries, ~40% deductions
        return int((gross_annual * 0.60) / 12)
    else:
        # North America & Worldwide (12 salaries, ~30% deductions)
        return int((gross_annual * 0.70) / 12)

def classify_region(loc_string):
    if not loc_string:
        return "Worldwide"
    loc = loc_string.lower()
    if any(x in loc for x in ['greece', 'hellas', 'athens', 'thessaloniki', 'ελλάδα', 'αθήνα']):
        return "Greece"
    if any(x in loc for x in ['europe', 'eu ', 'uk', 'united kingdom', 'germany', 'france', 'spain', 'london', 'berlin', 'paris']):
        return "Europe & UK"
    if any(x in loc for x in ['us', 'usa', 'united states', 'america', 'canada', 'north america', 'new york', 'san francisco']):
        return "North America"
    return "Worldwide"

def fetch_jobs():
    jobs = []
    seen_urls = set()

    def add_job(title, company, url, desc, location):
        if url and url not in seen_urls:
            seen_urls.add(url)
            jobs.append({
                'title': title,
                'company': company,
                'url': url,
                'description': clean_html(desc),
                'location': location if location else "Worldwide"
            })

    for cat in ['data', 'software-dev']:
        try:
            req = urllib.request.Request(f'https://remotive.com/api/remote-jobs?category={cat}', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                count = 0
                for j in data.get('jobs', []):
                    add_job(j.get('title', ''), j.get('company_name', ''), j.get('url', ''), j.get('description', ''), j.get('candidate_required_location', ''))
                    count += 1
            print(f"Fetched {count} from Remotive ({cat}).")
        except Exception as e:
            print(f"Error fetching from Remotive {cat}: {e}")

    for ind in ['data-science', 'engineering']:
        try:
            req = urllib.request.Request(f'https://jobicy.com/api/v2/remote-jobs?industry={ind}', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                count = 0
                for j in data.get('jobs', []):
                    add_job(j.get('jobTitle', ''), j.get('companyName', ''), j.get('url', ''), j.get('jobDescription', ''), j.get('jobGeo', ''))
                    count += 1
            print(f"Fetched {count} from Jobicy ({ind}).")
        except Exception as e:
            print(f"Error fetching from Jobicy {ind}: {e}")
            
    try:
        req = urllib.request.Request('https://jobicy.com/api/v2/remote-jobs?geo=greece', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            count = 0
            for j in data.get('jobs', []):
                add_job(j.get('jobTitle', ''), j.get('companyName', ''), j.get('url', ''), j.get('jobDescription', ''), "Greece")
                count += 1
        print(f"Fetched {count} from Jobicy (Greece).")
    except Exception as e:
        pass

    try:
        req = urllib.request.Request('https://www.arbeitnow.com/api/job-board-api', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            count = 0
            for j in data.get('data', []):
                add_job(j.get('title', ''), j.get('company_name', ''), j.get('url', ''), j.get('description', ''), j.get('location', ''))
                count += 1
    except Exception as e:
        print(f"Error fetching from Arbeitnow: {e}")

    # 4. Workable Greek Companies
    greek_companies = [
        'skroutz', 'blueground', 'epignosis', 'novibet', 'orfium', 
        'hellasdirect', 'welcomepickups', 'spotawheel', 'persado', 'hackthebox'
    ]
    for comp in greek_companies:
        try:
            req = urllib.request.Request(
                f'https://apply.workable.com/api/v3/accounts/{comp}/jobs', 
                headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}, 
                method='POST', 
                data=b'{"query":"","location":[],"department":[],"worktype":[],"remote":[]}'
            )
            resp = urllib.request.urlopen(req).read().decode()
            data = json.loads(resp)
            count = 0
            for j in data.get('results', []):
                # Only add if it's tech related (Data, Eng, AI, Dev, Analyst)
                title = j.get('title', '').lower()
                if any(x in title for x in ['data', 'engineer', 'developer', 'software', 'machine learning', 'ai', 'analyst', 'tech']):
                    # Build URL
                    shortcode = j.get('shortcode')
                    url = f'https://apply.workable.com/{comp}/j/{shortcode}/' if shortcode else ''
                    loc_dict = j.get('location', {})
                    loc_str = f"{loc_dict.get('city', '')}, Greece"
                    add_job(j.get('title', ''), comp.capitalize(), url, j.get('title', ''), loc_str)
                    count += 1
            print(f"Fetched {count} tech jobs from Workable ({comp}).")
        except Exception as e:
            print(f"Error fetching from Workable {comp}: {e}")

    return jobs

def get_previous_data(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                old_percentages = {}
                for cat in old_data.get('categories', {}).values():
                    for skill in cat:
                        old_percentages[skill['skill']] = skill['percentage']
                return old_percentages
        except:
            return {}
    return {}

def analyze_jobs(jobs, previous_percentages):
    total_jobs = len(jobs)
    if total_jobs == 0:
        return {}, [], {}

    skill_counts = {}
    for cat, skills_dict in CATEGORIES.items():
        skill_counts[cat] = {skill: 0 for skill in skills_dict.keys()}

    # Filter logic: Keep if it has skills OR if it's a Workable Greek job
    valid_jobs_list = []
    region_salaries = {"Greece": [], "Europe & UK": [], "North America": [], "Worldwide": []}

    for job in jobs:
        desc = job['description'] + " " + job['title'].lower()
        salary_info = extract_salary_info(desc)
        region = classify_region(job['location'])
        
        # GREEK REALITY CHECK
        if region == "Greece" and salary_info:
            if salary_info['currency'] == 'usd' or salary_info['eur_annual'] > 60000:
                region = "Worldwide"
                
        found_skills = []
        for cat, skills_dict in CATEGORIES.items():
            for skill in skills_dict.keys():
                if re.search(r'\b' + re.escape(skill) + r'\b', desc, re.IGNORECASE):
                    found_skills.append(skill)
                    
        # Force keep if it's from our workable scraper
        is_workable = "workable.com" in job['url']
        
        if found_skills or is_workable:
            job_entry = {
                "title": job['title'],
                "company": job['company'],
                "url": job['url'],
                "region": region,
                "location_raw": job['location'],
                "salary_raw": salary_info['raw'] if salary_info else None,
                "salary_eur": salary_info['eur_annual'] if salary_info else None,
                "salary_net_mo": estimate_net_monthly(salary_info['eur_annual'], region) if salary_info else None,
                "skills": found_skills if found_skills else ["Tech"]
            }
            valid_jobs_list.append(job_entry)
            
            if salary_info:
                region_salaries[region].append(salary_info['eur_annual'])

    # Prepare categories output
    categories_output = {}
    for cat, skills_dict in skill_counts.items():
        cat_list = []
        for skill, count in skills_dict.items():
            percentage = round((count / total_jobs) * 100, 1)
            old_pct = previous_percentages.get(skill, percentage)
            trend = round(percentage - old_pct, 1)
            
            cat_list.append({
                "skill": skill,
                "count": count,
                "percentage": percentage,
                "trend": trend
            })
        cat_list.sort(key=lambda x: x['count'], reverse=True)
        categories_output[cat] = cat_list

    # Compute Averages
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

    unicorn_job = None
    max_score = -1
    
    for job in valid_jobs_list:
        score = len(job['skills'])
        if job['salary_eur']:
            score += 5
        job['_score'] = score
        
        if score > max_score and job['salary_eur'] and job['salary_eur'] > 80000:
            max_score = score
            unicorn_job = job

    if unicorn_job:
        unicorn_job['is_unicorn'] = True
        
    valid_jobs_list.sort(key=lambda x: x['_score'], reverse=True)
    
    # FILTER: Only show jobs from Greece in the final Job Board
    greek_jobs = [j for j in valid_jobs_list if j['region'] == 'Greece']
    
    # Calculate Top Greek Companies by open roles
    import urllib.parse
    from collections import Counter
    gr_company_counts = Counter([j['company'] for j in greek_jobs if j['company']])
    top_greek_companies = []
    # Known workable companies to generate direct links
    workable_comps = [c.lower() for c in ['skroutz', 'blueground', 'epignosis', 'novibet', 'orfium', 'hellasdirect', 'welcomepickups', 'spotawheel', 'persado', 'hackthebox']]
    for comp, count in gr_company_counts.most_common(5):
        if comp.lower() in workable_comps:
            url = f"https://apply.workable.com/{comp.lower()}/"
        else:
            url = f"https://www.google.com/search?q={urllib.parse.quote(comp + ' careers')}"
        top_greek_companies.append({"name": comp, "count": count, "url": url})

    return categories_output, greek_jobs[:100], avg_salaries, avg_salaries_net, top_greek_companies

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    output_file = os.path.join(data_dir, 'skills.json')
    previous_percentages = get_previous_data(output_file)
    
    jobs = fetch_jobs()
    
    # 🇬🇷 BASELINE GREEK REALITY INJECTION
    jobs.append({
        'title': 'Data Scientist / ML Engineer',
        'company': 'Ανώνυμη Ελληνική Εταιρεία',
        'url': 'https://gr.indeed.com/',
        'description': 'Ζητείται Data Scientist με γνώσεις Python, SQL, Docker, LLM. Μισθός: 1.800€',
        'location': 'Greece'
    })
    jobs.append({
        'title': 'AI Engineer (Mid-Level)',
        'company': 'Athens Tech Startup',
        'url': 'https://gr.indeed.com/',
        'description': 'Ψάχνουμε AI Engineer. Απαιτήσεις: PyTorch, TensorFlow, Cloud AWS. Μισθός: 25.000€',
        'location': 'Athens'
    })
    
    print(f"Total jobs collected: {len(jobs)}")
    
    categories_stats, top_jobs, avg_salaries, avg_salaries_net, top_greek_companies = analyze_jobs(jobs, previous_percentages)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json_data = {
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "total_jobs_analyzed": len(jobs),
            "avg_salaries_eur": avg_salaries,
            "avg_salaries_net": avg_salaries_net,
            "top_greek_companies": top_greek_companies,
            "categories": categories_stats,
            "latest_jobs": top_jobs
        }
        json.dump(json_data, f, indent=4, ensure_ascii=False)
        
    print(f"Saved analysis and {len(top_jobs)} live jobs to {output_file}")
    print(f"Geo Salaries: {avg_salaries}")

if __name__ == "__main__":
    main()
