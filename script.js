let globalNetSalaries = {};
let allCategories = {};

document.addEventListener("DOMContentLoaded", () => {
    loadData();
    initThemeToggle();
});

function initThemeToggle() {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;
    const currentTheme = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", currentTheme);
    btn.innerText = currentTheme === "dark" ? "🌙" : "☀️";
    
    btn.addEventListener("click", () => {
        const t = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", t);
        localStorage.setItem("theme", t);
        btn.innerText = t === "dark" ? "🌙" : "☀️";
    });
}

async function loadData() {
    try {
        const response = await fetch("data/skills.json?v=" + new Date().getTime());
        const data = await response.json();
        
        globalNetSalaries = data.avg_salaries_net;
        allCategories = data.categories;

        renderStats(data);
        renderSalaries(data.avg_salaries_eur, data.avg_salaries_net);
        renderTopCompanies(data.top_greek_companies);
        renderCategories(data.categories);
        renderJobs(data.latest_jobs, null);
        renderHallOfShame(data.latest_jobs);
        
        setupCalculator();
        setupSkillSniper(data.categories, data.latest_jobs);
        startLocationScanner(data.latest_jobs);
        
        loadChartData();
    } catch (error) {
        console.error("Error loading data:", error);
        const jl = document.getElementById("job-list");
        if (jl) jl.innerHTML = "<p style=\"color:#ef4444;\">Σφαλμα φορτωσης. Δοκιμασε Ctrl+F5.</p>";
    }
}

function formatEUR(number) {
    if (!number) return "Αγνωστος";
    return new Intl.NumberFormat("el-GR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(number);
}

function renderStats(data) {
    const c = document.getElementById("stats-container");
    if (!c) return;
    c.innerHTML = `
        <div class="stat-card"><h3>Τελευταια Ενημερωση</h3><p>${data.last_updated}</p></div>
        <div class="stat-card"><h3>Αγγελιες που Αναλυθηκαν</h3><p>${data.total_jobs_analyzed}</p></div>
    `;
}

function renderSalaries(salaries, netSalaries) {
    const c = document.getElementById("salary-chart");
    if (!c || !salaries) return;
    let maxSalary = Math.max(...Object.values(salaries));
    if (maxSalary === 0) maxSalary = 100000;
    const regions = [
        { id: "Greece", name: "Ελλαδα", color: "#3b82f6" },
        { id: "Europe & UK", name: "Ευρωπη & UK", color: "#8b5cf6" },
        { id: "Worldwide", name: "Παγκοσμια Remote", color: "#10b981" },
        { id: "North America", name: "Αμερικη", color: "#f59e0b" }
    ];
    let html = "";
    regions.forEach(r => {
        let val = salaries[r.id] || 0;
        let net = netSalaries ? (netSalaries[r.id] || 0) : 0;
        let width = val === 0 ? 5 : (val / maxSalary) * 100;
        html += `<div class="salary-bar-container" style="flex-wrap:wrap;">
            <div class="salary-label">${r.name}</div>
            <div class="salary-track"><div class="salary-fill" style="width:${width}%;background:${r.color};"></div></div>
            <div class="salary-value">${val === 0 ? "N/A" : formatEUR(val) + "/ετος"}</div>
            <div style="width:100%;text-align:right;font-size:0.85rem;color:#9ca3af;margin-top:-5px;padding-right:120px;">${net ? "(~" + formatEUR(net) + "/μηνα Καθαρα)" : ""}</div>
        </div>`;
    });
    c.innerHTML = html;
}

function renderCategories(categories) {
    const grid = document.getElementById("categories-grid");
    if (!grid || !categories) return;
    grid.innerHTML = "";
    for (const [catName, skills] of Object.entries(categories)) {
        const card = document.createElement("div");
        card.className = "category-card";
        let html = "<h3>" + catName + "</h3>";
        skills.forEach(skill => {
            let trendHtml = skill.trend > 0 ? "<span class=\"trend up\">+ " + skill.trend + "%</span>"
                : skill.trend < 0 ? "<span class=\"trend down\">- " + Math.abs(skill.trend) + "%</span>"
                : "<span class=\"trend\">-</span>";
            html += `<div class="skill-item">
                <span class="skill-name">${skill.skill}</span>
                <div class="skill-stats"><span class="skill-pct">${skill.percentage}%</span>${trendHtml}</div>
            </div>
            <div class="progress-track"><div class="progress-fill" style="width:${skill.percentage}%"></div></div>`;
        });
        card.innerHTML = html;
        grid.appendChild(card);
    }
}

function renderJobs(jobs, selectedSkills) {
    const jobList = document.getElementById("job-list");
    if (!jobList) return;
    jobList.innerHTML = "";

    if (!jobs || jobs.length === 0) {
        jobList.innerHTML = "<p style=\"color:#9ca3af;\">Δεν βρεθηκαν αγγελιες.</p>";
        return;
    }

    const showMatch = selectedSkills && selectedSkills.size > 0;
    let displayJobs = [...jobs];

    if (showMatch) {
        displayJobs = displayJobs.map(job => {
            let matchCount = 0;
            const searchText = (job.title + " " + (job.company || "")).toLowerCase();
            selectedSkills.forEach(skill => {
                if (searchText.includes(skill.toLowerCase())) matchCount++;
            });
            const matchPct = Math.min(100, Math.round((matchCount / selectedSkills.size) * 100));
            return { ...job, matchPct };
        });
        displayJobs.sort((a, b) => (b.matchPct || 0) - (a.matchPct || 0));
    }

    displayJobs.forEach(job => {
        const jobEl = document.createElement("div");
        jobEl.className = "job-card";
        if (job.is_unicorn) jobEl.classList.add("unicorn");

        let salaryStr;
        if (job.salary_eur) {
            salaryStr = "💰 " + formatEUR(job.salary_eur) + "/έτος (~" + formatEUR(job.salary_net_mo) + "/μήνα καθαρά)";
        } else {
            const regionKey = job.region || "Greece";
            const mktNet = globalNetSalaries[regionKey];
            if (mktNet) {
                salaryStr = "<span style='color:#94a3b8;'>Μισθός: Κατόπιν Συνεννόησης</span>" +
                            " <span style='color:#60a5fa;font-size:0.8rem;'>(Μέσος αγοράς: ~" + formatEUR(mktNet) + "/μήνα καθαρά)</span>";
            } else {
                salaryStr = "<span style='color:#94a3b8;'>Μισθός: Κατόπιν Συνεννόησης</span>";
            }
        }

        let matchHtml = "";
        if (showMatch && job.matchPct !== undefined) {
            let cls = job.matchPct >= 60 ? "high" : job.matchPct >= 30 ? "med" : "low";
            matchHtml = "<div class=\"match-badge " + cls + "\">🎯 " + job.matchPct + "% Match</div>";
        }

        const safeTitle = (job.title || "Αγγελια").replace(/\\/g, "").replace(/"/g, "");
        const safeCompany = (job.company || "").replace(/\\/g, "").replace(/"/g, "");

        jobEl.innerHTML = matchHtml + `
            <div class="job-card-header">
                <div>
                    <h3><a href="${job.url}" target="_blank" rel="noopener">${job.title || "Αγγελια"}</a></h3>
                    <p class="company">${job.company || ""} • 📍 ${job.location_raw || "Ελλαδα"}</p>
                    <p style="font-size:0.85rem;margin-top:5px;">${salaryStr}</p>
                </div>
                <div style="display:flex;gap:8px;flex-shrink:0;align-items:flex-start;margin-top:5px;">
                    <button class="snipe-btn" id="snipe-${Math.random().toString(36).substr(2,9)}">🎯 Snipe</button>
                    ${!job.salary_eur ? `<button class="share-btn" style="background:transparent;color:#fbbf24;border:1px solid #fbbf24;border-radius:8px;padding:8px;cursor:pointer;transition:all 0.2s;" title="Share violation">📤</button>` : ''}
                    <a href="${job.url}" target="_blank" rel="noopener" class="apply-btn">Δες →</a>
                </div>
            </div>`;

        const snipeBtn = jobEl.querySelector(".snipe-btn");
        snipeBtn.addEventListener("click", () => snipeRecruiter(safeTitle, safeCompany));

        const shareBtn = jobEl.querySelector(".share-btn");
        if (shareBtn) {
            shareBtn.addEventListener("click", () => {
                const text = encodeURIComponent(`Η ${job.company || 'εταιρεία'} ψάχνει ${job.title || 'άτομο'} στην Ελλάδα αλλά δεν αναφέρει μισθό στην αγγελία, παραβιάζοντας την Οδηγία ΕΕ 2023/970 για Μισθολογική Διαφάνεια. Δες περισσότερα στο DarkAIs Jobs Radar: https://karidasd.github.io/greek-ai-jobs-radar/`);
                window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank');
            });
        }

        jobList.appendChild(jobEl);
    });
}

function snipeRecruiter(title, company) {
    const prompt = "Εισαι career coach. Γραψε μου ενα συντομο Cold Email στα Ελληνικα (κατω απο 120 λεξεις) που θα στειλω στον HR Manager της εταιρειας \"" + company + "\" για τη θεση \"" + title + "\". Ο τονος να ειναι σιγουρος και επαγγελματικος. Να ξεκινα απευθειας με το email, χωρις εισαγωγη.";
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(prompt).then(() => {
            alert("Το Prompt αντιγραφηκε!\n\nΤωρα ανοιγει το ChatGPT. Κανε Paste (Ctrl+V) και πατα Enter!");
            window.open("https://chatgpt.com/", "_blank");
        }).catch(() => {
            window.open("https://chatgpt.com/", "_blank");
            alert("Αντιγραψε χειροκινητα:\n\n" + prompt);
        });
    } else {
        window.open("https://chatgpt.com/", "_blank");
        alert("Αντιγραψε χειροκινητα:\n\n" + prompt);
    }
}

function renderTopCompanies(companies) {
    const list = document.getElementById("top-companies-list");
    if (!list) return;
    if (!companies || companies.length === 0) {
        list.innerHTML = "<li>Δεν βρεθηκαν δεδομενα.</li>";
        return;
    }
    let html = "";
    companies.forEach((comp, index) => {
        const medal = index === 0 ? "🥇" : index === 1 ? "🥈" : index === 2 ? "🥉" : "🏢";
        html += `<a href="${comp.url}" target="_blank" rel="noopener" style="text-decoration:none;color:inherit;display:block;">
            <li style="display:flex;justify-content:space-between;background:rgba(59,130,246,0.1);padding:10px 15px;border-radius:6px;border-left:3px solid #3b82f6;transition:background 0.3s;cursor:pointer;"
                onmouseover="this.style.background='rgba(59,130,246,0.3)'" onmouseout="this.style.background='rgba(59,130,246,0.1)'">
                <span style="font-weight:600;">${medal} ${comp.name}</span>
                <span style="color:#60a5fa;font-weight:bold;">${comp.count} Θεσεις &rarr;</span>
            </li></a>`;
    });
    list.innerHTML = html;
}

function setupCalculator() {
    const btn = document.getElementById("calc-btn");
    const input = document.getElementById("user-salary");
    const resultDiv = document.getElementById("calc-result");
    if (!btn || !input || !resultDiv) return;
    btn.addEventListener("click", () => {
        const salary = parseInt(input.value);
        if (!salary || salary < 400 || salary > 50000) {
            resultDiv.innerHTML = "<span style=\"color:#ef4444;\">Βαλε εναν εγκυρο μισθο (π.χ. 1500)</span>";
            return;
        }
        const grNet = globalNetSalaries["Greece"] || 1900;
        const euNet = globalNetSalaries["Europe & UK"] || 3300;
        let msg = "";
        const diffGr = Math.round(((salary - grNet) / grNet) * 100);
        const diffEu = Math.round(((salary - euNet) / euNet) * 100);
        msg += diffGr < 0
            ? "<span style=\"color:#ef4444;\">Πληρωνεσαι " + Math.abs(diffGr) + "% ΚΑΤΩ απο τον Ελληνικο μεσο οπο Tech (" + formatEUR(grNet) + "/μηνα).</span><br/>"
            : "<span style=\"color:#10b981;\">Εισαι " + diffGr + "% ΠΑΝΩ απο τον Ελληνικο μεσο ορο (" + formatEUR(grNet) + "/μηνα).</span><br/>";
        msg += diffEu < 0
            ? "<span style=\"color:#ef4444;margin-top:5px;display:inline-block;\">" + Math.abs(diffEu) + "% ΚΑΤΩ απο την Ευρωπη Remote (" + formatEUR(euNet) + "/μηνα). Ωρα για αλλαγη!</span>"
            : "<span style=\"color:#10b981;margin-top:5px;display:inline-block;\">Κερδιζεις ακομα και την Ευρωπη!</span>";
        resultDiv.innerHTML = msg;
    });
}

let selectedUserSkills = new Set();
let allLoadedJobs = [];

function setupSkillSniper(categories, jobs) {
    allLoadedJobs = jobs;
    const container = document.getElementById("skill-selector");
    if (!container) return;
    const allSkills = [];
    if (categories) {
        for (const skillList of Object.values(categories)) {
            skillList.forEach(s => { if (s.count > 0) allSkills.push(s.skill); });
        }
    }
    if (allSkills.length === 0) {
        container.innerHTML = "<p style=\"color:#9ca3af;\">Φορτωση skills...</p>";
        return;
    }
    allSkills.sort().forEach(skill => {
        const label = document.createElement("label");
        label.className = "skill-checkbox-label";
        label.textContent = skill;
        label.addEventListener("click", () => {
            if (selectedUserSkills.has(skill)) {
                selectedUserSkills.delete(skill);
                label.classList.remove("selected");
            } else {
                selectedUserSkills.add(skill);
                label.classList.add("selected");
            }
            renderJobs(allLoadedJobs, selectedUserSkills);
        });
        container.appendChild(label);
    });
}

function startLocationScanner(jobs) {
    const locations = [...new Set(
        (jobs || []).map(j => j.location_raw).filter(l => l && l.trim() !== "")
    )];
    const statusText = document.getElementById("radar-status-text");
    const blipsContainer = document.getElementById("radar-blips");
    if (!statusText || !blipsContainer) return;
    if (locations.length === 0) { statusText.innerText = "📡 Online"; return; }

    let i = 0;
    const center = 100;
    setInterval(() => {
        const loc = locations[i % locations.length];
        statusText.innerText = "📡 " + loc;
        const angle = Math.random() * 2 * Math.PI;
        const radius = 15 + Math.random() * 70;
        const x = center + radius * Math.cos(angle);
        const y = center + radius * Math.sin(angle);

        const blip = document.createElement("div");
        blip.className = "radar-blip";
        blip.style.left = (x - 3) + "px";
        blip.style.top = (y - 3) + "px";

        const lbl = document.createElement("div");
        lbl.className = "blip-label";
        lbl.style.left = (x > center ? x - 55 : x + 10) + "px";
        lbl.style.top = (y - 8) + "px";
        lbl.innerText = loc;

        blipsContainer.appendChild(blip);
        blipsContainer.appendChild(lbl);
        setTimeout(() => { blip.remove(); lbl.remove(); }, 2000);
        i++;
    }, 1500);
}

// ─── Hall of Shame & Chart ────────────────────────────────────────────────
function renderHallOfShame(jobs) {
    const shameContainer = document.getElementById("hall-of-shame");
    if (!shameContainer) return;
    
    const badJobs = (jobs || []).filter(j => j.region === "Greece" && !j.salary_eur && j.company);
    const companyCounts = {};
    badJobs.forEach(j => {
        companyCounts[j.company] = (companyCounts[j.company] || 0) + 1;
    });
    
    const sortedBad = Object.entries(companyCounts).sort((a,b) => b[1]-a[1]);
    
    if (sortedBad.length === 0) {
        shameContainer.innerHTML = "<p style='color:#10b981;'>Όλες οι εταιρείες αναγράφουν μισθό! 🎉</p>";
        return;
    }
    
    shameContainer.innerHTML = "";
    sortedBad.slice(0, 10).forEach(([comp, count]) => {
        const el = document.createElement("div");
        el.style.background = "rgba(239,68,68,0.1)";
        el.style.border = "1px solid rgba(239,68,68,0.4)";
        el.style.padding = "8px 12px";
        el.style.borderRadius = "8px";
        el.style.fontSize = "0.9rem";
        el.innerHTML = `<span style="font-weight:bold;color:#ef4444;">${comp}</span> <span style="color:var(--text-secondary);">(${count} αγγελίες)</span>`;
        shameContainer.appendChild(el);
    });
}

function loadChartData() {
    fetch("data/history.json?v=" + new Date().getTime())
        .then(r => r.json())
        .then(data => {
            if (!data || data.length < 2) {
                document.getElementById("trend-note").innerText = "Συλλέγουμε δεδομένα. Ελάτε ξανά σε λίγες μέρες για το γράφημα.";
                return;
            }
            renderChart(data);
        })
        .catch(() => {
            document.getElementById("trend-note").innerText = "Δεν βρέθηκε ιστορικό.";
        });
}

function renderChart(historyData) {
    const ctx = document.getElementById("salary-trend-chart");
    if (!ctx) return;
    
    const labels = historyData.map(d => {
        const [y, m, day] = d.date.split("-");
        return `${day}/${m}`;
    });
    const grData = historyData.map(d => d.salaries["Greece"] || 0);
    const euData = historyData.map(d => d.salaries["Europe & UK"] || 0);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Ελλάδα (Net/mo)',
                    data: grData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59,130,246,0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Ευρώπη (Net/mo)',
                    data: euData,
                    borderColor: '#10b981',
                    borderWidth: 2,
                    borderDash: [5,5],
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#94a3b8' } }
            },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, min: 500 }
            }
        }
    });
}

// ─── Email Alerts (Formspree) ───────────────────────────────────────────────
const alertForm = document.getElementById("alert-form");
if (alertForm) {
    alertForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const email  = document.getElementById("alert-email").value.trim();
        const skills = document.getElementById("alert-skills").value.trim();
        const result = document.getElementById("alert-result");
        if (!email) return;
        result.innerHTML = "<span style='color:#60a5fa;'>Αποστολή...</span>";
        fetch("https://formspree.io/f/xpwzqkrg", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "application/json" },
            body: JSON.stringify({ email, skills, source: "Greek AI Jobs Radar" })
        }).then(r => {
            if (r.ok) {
                result.innerHTML = "<span style='color:#10b981;'>Εγγραφηκες! Θα λαμβανεις alerts για νεες αγγελιες.</span>";
                alertForm.reset();
            } else {
                result.innerHTML = "<span style='color:#ef4444;'>Σφαλμα. Δοκιμασε ξανα.</span>";
            }
        }).catch(() => {
            result.innerHTML = "<span style='color:#ef4444;'>Σφαλμα συνδεσης.</span>";
        });
    });
}

