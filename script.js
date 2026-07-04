let globalNetSalaries = {};

document.addEventListener("DOMContentLoaded", async () => {
    try {
        // Append a timestamp to bypass aggressive browser caching
        const response = await fetch('data/skills.json?v=' + new Date().getTime());
        const data = await response.json();
        
        globalNetSalaries = data.avg_salaries_net;

        renderStats(data);
        renderSalaries(data.avg_salaries_eur, data.avg_salaries_net);
        renderTopCompanies(data.top_greek_companies);
        renderCategories(data.categories);
        renderJobs(data.latest_jobs);
        
        setupCalculator();
    } catch (error) {
        console.error("Error loading data:", error);
    }
});

function formatEUR(number) {
    if (!number) return "Άγνωστος";
    return new Intl.NumberFormat('el-GR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(number);
}

function renderStats(data) {
    const statsContainer = document.getElementById('stats-container');
    statsContainer.innerHTML = `
        <div class="stat-card">
            <h3>Τελευταία Ενημέρωση</h3>
            <p>${data.last_updated}</p>
        </div>
        <div class="stat-card">
            <h3>Αγγελίες που Αναλύθηκαν</h3>
            <p>${data.total_jobs_analyzed}</p>
        </div>
    `;
}

function renderSalaries(salaries, netSalaries) {
    const chartContainer = document.getElementById('salary-chart');
    if (!salaries || Object.keys(salaries).length === 0) return;

    let maxSalary = Math.max(...Object.values(salaries));
    if (maxSalary === 0) maxSalary = 100000; // fallback

    const regions = [
        { id: "Greece", name: "Ελλάδα 🇬🇷", color: "#3b82f6" },
        { id: "Europe & UK", name: "Ευρώπη & UK 🇪🇺", color: "#8b5cf6" },
        { id: "Worldwide", name: "Παγκόσμια (Remote) 🌍", color: "#10b981" },
        { id: "North America", name: "Αμερική 🇺🇸", color: "#f59e0b" }
    ];

    let html = '';
    regions.forEach(r => {
        let val = salaries[r.id] || 0;
        let net = netSalaries ? (netSalaries[r.id] || 0) : 0;
        let width = val === 0 ? 5 : (val / maxSalary) * 100;
        
        let valText = val === 0 ? 'N/A' : `${formatEUR(val)} Μικτά/έτος`;
        let netText = net === 0 ? '' : `(~${formatEUR(net)}/μήνα Καθαρά)`;
        
        html += `
            <div class="salary-bar-container" style="flex-wrap: wrap;">
                <div class="salary-label">${r.name}</div>
                <div class="salary-track">
                    <div class="salary-fill" style="width: ${width}%; background: ${r.color};"></div>
                </div>
                <div class="salary-value">${valText}</div>
                <div style="width: 100%; text-align: right; font-size: 0.85rem; color: #9ca3af; margin-top: -5px; padding-right: 120px;">
                    ${netText}
                </div>
            </div>
        `;
    });
    chartContainer.innerHTML = html;
}

function renderCategories(categories) {
    const grid = document.getElementById('categories-grid');
    grid.innerHTML = '';

    for (const [catName, skills] of Object.entries(categories)) {
        const card = document.createElement('div');
        card.className = 'category-card';
        
        const catTitle = document.createElement('h3');
        catTitle.textContent = catName;
        card.appendChild(catTitle);

        skills.forEach(skill => {
            const skillItem = document.createElement('div');
            skillItem.className = 'skill-item';
            
            let trendHtml = '';
            if (skill.trend > 0) {
                trendHtml = `<span class="trend up">↑ ${skill.trend}%</span>`;
            } else if (skill.trend < 0) {
                trendHtml = `<span class="trend down">↓ ${Math.abs(skill.trend)}%</span>`;
            } else {
                trendHtml = `<span class="trend">−</span>`;
            }

            skillItem.innerHTML = `
                <span class="skill-name">${skill.skill}</span>
                <div class="skill-stats">
                    <span class="skill-pct">${skill.percentage}%</span>
                    ${trendHtml}
                </div>
            `;
            
            // Add a progress bar under the skill
            const progressTrack = document.createElement('div');
            progressTrack.className = 'progress-track';
            const progressFill = document.createElement('div');
            progressFill.className = 'progress-fill';
            progressFill.style.width = `${skill.percentage}%`;
            progressTrack.appendChild(progressFill);
            
            card.appendChild(skillItem);
            card.appendChild(progressTrack);
        });

        grid.appendChild(card);
    }
}

function renderJobs(jobs) {
    const jobList = document.getElementById('job-list');
    jobList.innerHTML = '';

    jobs.forEach(job => {
        const jobEl = document.createElement('div');
        jobEl.className = 'job-card';
        if (job.is_unicorn) {
            jobEl.classList.add('unicorn');
        }

        const skillsHtml = job.skills.map(s => `<span class="tag skill-tag">${s}</span>`).join('');
        const unicornBadge = job.is_unicorn ? `<span class="badge unicorn-badge">👑 Unicorn Job</span>` : '';
        const grBadge = job.region === "Greece" ? `<span class="badge gr-badge">🇬🇷 Ελληνική Αγορά</span>` : '';
        
        let salaryHtml = '';
        if (job.salary_eur) {
            salaryHtml = `<span class="badge salary-badge">💰 ${formatEUR(job.salary_eur)}/έτος</span>`;
        }

        jobEl.innerHTML = `
            <div class="job-header">
                <div>
                    ${unicornBadge}
                    ${grBadge}
                    ${salaryHtml}
                    <h3><a href="${job.url}" target="_blank">${job.title}</a></h3>
                    <p class="company">${job.company} • 📍 ${job.location_raw}</p>
                </div>
                <div>
                    <button class="snipe-btn" onclick="snipeRecruiter('${job.title}', '${job.company}', '${job.skills.join(', ')}')">🎯 Snipe Recruiter</button>
                    <a href="${job.url}" target="_blank" class="apply-btn">Δες το</a>
                </div>
            </div>
            <div class="job-skills">
                ${skillsHtml}
            </div>
        `;
        jobList.appendChild(jobEl);
    });
}

window.snipeRecruiter = function(title, company, skills) {
    const prompt = `Act as an aggressive, highly professional technical recruiter and career coach. 
Write a short "Cold Email" (in Greek) that I will send to the HR Manager of ${company} to apply for the "${title}" position. 
The job requires the following skills: ${skills}.
The tone should be confident, showing that I have exactly these skills and I am ready to deliver results immediately. Keep it under 150 words. Do not use generic corporate jargon, make it punchy.`;
    
    // Copy to clipboard
    navigator.clipboard.writeText(prompt).then(() => {
        alert("🎯 Το Μυστικό Prompt αντιγράφηκε στο πρόχειρο (Clipboard)!\n\nΤώρα θα ανοίξει το ChatGPT. Απλά κάνε Επικόλληση (Paste) και πάτα Enter για να σου γράψει το τέλειο Cold Email.");
        window.open("https://chatgpt.com/", "_blank");
    }).catch(err => {
        console.error('Failed to copy: ', err);
        alert("Κάτι πήγε στραβά με την αντιγραφή. Δοκίμασε ξανά.");
    });
}

function renderTopCompanies(companies) {
    const list = document.getElementById('top-companies-list');
    if (!companies || companies.length === 0) {
        list.innerHTML = '<li>Δεν βρέθηκαν δεδομένα.</li>';
        return;
    }
    
    let html = '';
    companies.forEach((comp, index) => {
        let medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🏢';
        let workableUrl = comp.url || '#';
        html += `
            <a href="${workableUrl}" target="_blank" style="text-decoration: none; color: inherit; display: block;">
                <li style="display: flex; justify-content: space-between; background: rgba(59, 130, 246, 0.1); padding: 10px 15px; border-radius: 6px; border-left: 3px solid #3b82f6; transition: background 0.3s ease; cursor: pointer;" onmouseover="this.style.background='rgba(59, 130, 246, 0.3)'" onmouseout="this.style.background='rgba(59, 130, 246, 0.1)'">
                    <span style="font-weight: 600;">${medal} ${comp.name}</span>
                    <span style="color: #60a5fa; font-weight: bold;">${comp.count} Θέσεις &rarr;</span>
                </li>
            </a>
        `;
    });
    list.innerHTML = html;
}

function setupCalculator() {
    const btn = document.getElementById('calc-btn');
    const input = document.getElementById('user-salary');
    const resultDiv = document.getElementById('calc-result');

    btn.addEventListener('click', () => {
        const salary = parseInt(input.value);
        if (!salary || salary < 400 || salary > 50000) {
            resultDiv.innerHTML = '<span style="color: #ef4444;">Βάλε έναν έγκυρο καθαρό μισθό (π.χ. 1500)</span>';
            return;
        }

        const grNet = globalNetSalaries['Greece'] || 1900;
        const euNet = globalNetSalaries['Europe & UK'] || 3300;

        let diffGr = Math.round(((salary - grNet) / grNet) * 100);
        let diffEu = Math.round(((salary - euNet) / euNet) * 100);

        let msg = '';
        if (diffGr < 0) {
            msg += `<span style="color: #ef4444;">⚠️ Πληρώνεσαι ${Math.abs(diffGr)}% ΚΑΤΩ από τον Ελληνικό μέσο όρο Tech.</span><br/>`;
        } else {
            msg += `<span style="color: #10b981;">✅ Είσαι ${diffGr}% ΠΑΝΩ από τον Ελληνικό μέσο όρο.</span><br/>`;
        }

        if (diffEu < 0) {
            msg += `<span style="color: #ef4444; margin-top: 5px; display: inline-block;">❌ Και ${Math.abs(diffEu)}% ΚΑΤΩ από την Ευρώπη (Remote). Ώρα για αλλαγή!</span>`;
        } else {
            msg += `<span style="color: #10b981; margin-top: 5px; display: inline-block;">🌍 Κερδίζεις ακόμα και την Ευρώπη!</span>`;
        }

        resultDiv.innerHTML = msg;
    });
}
