<div align="center">

# ⚡ Greek AI Jobs Radar
### Το μοναδικό εργαλείο που λέει την αλήθεια για την Ελληνική αγορά Tech

[![Live Demo](https://img.shields.io/badge/🌐_LIVE_DEMO-karidasd.github.io-00e5ff?style=for-the-badge)](https://karidasd.github.io/greek-ai-jobs-radar/)
[![Auto Update](https://img.shields.io/badge/🤖_Auto_Update-Every_Night-10b981?style=for-the-badge)](https://github.com/karidasd/greek-ai-jobs-radar/actions)
[![Made in Greece](https://img.shields.io/badge/🇬🇷_Made_in-Greece-0d5eaf?style=for-the-badge)](https://karidasd.github.io/greek-ai-jobs-radar/)

</div>

---

## Τι είναι αυτό;

Ένα **100% δωρεάν, open-source εργαλείο** που κάθε βράδυ σαρώνει αυτόματα την αγορά εργασίας στην Ελλάδα και εμφανίζει:

- 🇬🇷 **Live αγγελίες** από Ελληνικές εταιρείες (Skroutz, Novibet, Blueground, Orfium, Spotawheel...)
- 💰 **Πραγματικούς μισθούς** — Μικτά & Καθαρά, σε Ευρώ, με φόρους
- 📈 **Τάσεις αγοράς** — Ποιες τεχνολογίες ζητούνται περισσότερο (Python, SQL, AWS...)
- 🛑 **Υπολογιστή Αδικίας** — Δες αν πληρώνεσαι λιγότερο από τον μέσο όρο
- 🎯 **Skill-Sniper** — Βάλε τα skills σου και δες ποιες αγγελίες σου ταιριάζουν
- 📡 **Graphical Radar** — Live scanner με τοποθεσίες αγγελιών

---

## 🛡️ Γιατί δεν ξύνουμε LinkedIn & Kariera.gr;

Απλό: **Cloudflare + Anti-bot = 403 Forbidden** σε κάθε αυτοματοποιημένο εργαλείο.

Αντί γι' αυτό, ανακαλύψαμε ότι όλες οι μεγάλες Ελληνικές Tech εταιρείες χρησιμοποιούν το **Workable** ως σύστημα HR. Το Workable έχει ανοιχτό JSON API:

```
POST https://apply.workable.com/api/v3/accounts/{company}/jobs
```

Το καλούμε απευθείας → παίρνουμε **καθαρά δεδομένα** χωρίς bot detection, χωρίς κόστος.

---

## 🧠 Πώς υπολογίζονται οι μισθοί;

### Βήμα 1: Εξαγωγή Μισθού (NLP Regex)
Ψάχνουμε στην περιγραφή κάθε αγγελίας για salary patterns:
- `$150k` → USD → EUR (x 0.92)
- `£50k` → GBP → EUR (x 1.17)
- `2.500€/μήνα` → x14 μηνιάτικα = Ετήσιος Μισθός

### Βήμα 2: Καθαρός Μισθός ανά Χώρα

| Χώρα | Διαίρεση | Κρατήσεις |
|------|----------|-----------|
| 🇬🇷 Ελλάδα (<20k€) | ÷ 14 | ~25% |
| 🇬🇷 Ελλάδα (<40k€) | ÷ 14 | ~30% |
| 🇬🇷 Ελλάδα (>40k€) | ÷ 14 | ~35% |
| 🇪🇺 Ευρώπη & UK | ÷ 12 | ~40% |
| 🌎 Worldwide / USA | ÷ 12 | ~30% |

---

## ⚙️ Αρχιτεκτονική

```
GitHub Actions (CRON: κάθε μεσάνυχτα)
    └── analyze_jobs.py
            ├── Workable API (10 Ελληνικές εταιρείες)
            ├── Remotive API (remote tech jobs)
            ├── Jobicy API  (remote jobs + Greece filter)
            └── Salary NLP Extractor
                    └── data/skills.json
                            └── GitHub Pages (index.html + script.js)
```

**Κόστος hosting: 0€. Κόστος servers: 0€. Κόστος APIs: 0€.**

---

## 🚀 Τρέξε το τοπικά

```bash
git clone https://github.com/karidasd/greek-ai-jobs-radar.git
cd greek-ai-jobs-radar
python scripts/analyze_jobs.py
# Άνοιξε το index.html στον browser
```

---

## 🎯 Features Roadmap

- [x] Live αγγελίες από Workable API
- [x] Σύγκριση μισθών Ελλάδα vs Κόσμος
- [x] Skill-Sniper (% Match αγγελιών)
- [x] Υπολογιστής Αδικίας
- [x] Graphical Radar Scanner
- [x] Snipe Recruiter (Cold Email Generator)
- [ ] Lever & Greenhouse API integration
- [ ] Email alerts για νέες αγγελίες
- [ ] Ιστορικό μισθών (salary history tracking)

---

<div align="center">
<b>Built by karidasd · No bullshit · No paywalls · No LinkedIn</b>
</div>
