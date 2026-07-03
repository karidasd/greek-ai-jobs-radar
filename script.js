document.addEventListener("DOMContentLoaded", async () => {
    try {
        const response = await fetch('data/skills.json');
        const data = await response.json();
        
        renderStats(data);
        renderSalaries(data.avg_salaries_eur, data.avg_salaries_net);
        renderCategories(data.categories);
        renderJobs(data.latest_jobs);
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
                <a href="${job.url}" target="_blank" class="apply-btn">Δες το</a>
            </div>
            <div class="job-skills">
                ${skillsHtml}
            </div>
        `;
        jobList.appendChild(jobEl);
    });
}
