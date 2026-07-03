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
            
        return {"raw": raw_val, "eur_annual": int(eur_val)}
        
    # Check for monthly Greek/EU salaries e.g., 2000€, 2.500 ευρώ, 2000 eur
    gr_match = re.search(r'(\d{1,2})[.,]?(\d{3})\s*(€|eur|ευρώ)', text)
    if gr_match:
        thousands = gr_match.group(1)
        hundreds = gr_match.group(2)
        monthly = int(thousands + hundreds)
        if 800 <= monthly <= 15000:
            return {"raw": f"€{monthly}/mo", "eur_annual": monthly * 14}
            
    return None

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
        print(f"Fetched {count} from Arbeitnow.")
    except Exception as e:
        print(f"Error fetching from Arbeitnow: {e}")

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

    valid_jobs_list = []
    region_salaries = {"Greece": [], "Europe & UK": [], "North America": [], "Worldwide": []}

    for job in jobs:
        desc = job['description'] + " " + job['title'].lower()
        salary_info = extract_salary_info(desc)
        region = classify_region(job['location'])
        found_skills = []

        for cat, skills_dict in CATEGORIES.items():
            for skill, keywords in skills_dict.items():
                for kw in keywords:
                    if kw in desc:
                        skill_counts[cat][skill] += 1
                        found_skills.append(skill)
                        break

        if found_skills:
            job_entry = {
                "title": job['title'],
                "company": job['company'],
                "url": job['url'],
                "region": region,
                "location_raw": job['location'],
                "salary_raw": salary_info['raw'] if salary_info else None,
                "salary_eur": salary_info['eur_annual'] if salary_info else None,
                "skills": found_skills
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
    for r, sals in region_salaries.items():
        if sals:
            avg_salaries[r] = sum(sals) // len(sals)
        else:
            avg_salaries[r] = 0

    unicorn_job = None
    max_score = -1

    for job in valid_jobs_list:
        score = len(job['skills']) * 10
        if job['salary_eur']:
            score += 20
            # Higher salary = higher score
            score += (job['salary_eur'] // 10000) * 2
            
        if job['region'] == "Greece":
            score += 50 # Priority to Greek jobs
            
        job['is_unicorn'] = False
        job['_score'] = score
        
        if score > max_score:
            max_score = score
            unicorn_job = job

    if unicorn_job:
        unicorn_job['is_unicorn'] = True
        
    valid_jobs_list.sort(key=lambda x: x['_score'], reverse=True)

    return categories_output, valid_jobs_list[:100], avg_salaries

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    output_file = os.path.join(data_dir, 'skills.json')
    previous_percentages = get_previous_data(output_file)
    
    jobs = fetch_jobs()
    print(f"Total jobs collected: {len(jobs)}")
    
    categories_stats, top_jobs, avg_salaries = analyze_jobs(jobs, previous_percentages)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json_data = {
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "total_jobs_analyzed": len(jobs),
            "avg_salaries_eur": avg_salaries,
            "categories": categories_stats,
            "latest_jobs": top_jobs
        }
        json.dump(json_data, f, indent=4, ensure_ascii=False)
        
    print(f"Saved analysis and {len(top_jobs)} live jobs to {output_file}")
    print(f"Geo Salaries: {avg_salaries}")

if __name__ == "__main__":
    main()
