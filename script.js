// =========================
// Email Spam Verifier Pro
// =========================

const spamKeywords = [
    "winner","congratulations","prize","free",
    "urgent","act now","limited offer",
    "limited time","cash","reward",
    "exclusive","buy now","investment",
    "million","selected","verify your account",
    "password","confirm your","account suspended",
    "security alert","click here",
    "unauthorized","urgent action"
];

const urgencyPatterns = [
    "act now",
    "limited time",
    "today only",
    "final notice",
    "ending soon",
    "last chance",
    "urgent"
];

function analyzeEmail() {

    const text =
        document.getElementById("emailContent").value;

    if (!text.trim()) {
        alert("Paste email content first.");
        return;
    }

    const lower = text.toLowerCase();

    let score = 0;
    let explanations = [];

    // Word Count
    const words =
        text.trim().split(/\s+/);

    const wordCount = words.length;

    if (wordCount > 100) {
        score += 2;
        explanations.push(
            "Long email detected (+2)"
        );
    }

    // Spam Keywords

    let matchedKeywords = [];

    spamKeywords.forEach(keyword => {
        if (lower.includes(keyword)) {
            matchedKeywords.push(keyword);
        }
    });

    if (matchedKeywords.length > 0) {
        score += 2;
        explanations.push(
            `${matchedKeywords.length} spam keywords found (+2)`
        );
    }

    // Links

    const links =
        text.match(/https?:\/\/\S+|www\.\S+/gi) || [];

    if (links.length >= 3) {
        score += 2;
    }
    else if (links.length > 0) {
        score += 1;
    }

    if (links.length > 0) {
        explanations.push(
            `${links.length} suspicious links`
        );
    }

    // Exclamation

    const exclamations =
        (text.match(/!/g) || []).length;

    if (exclamations >= 5) {
        score += 1;
        explanations.push(
            "Too many exclamation marks (+1)"
        );
    }

    // Urgency

    let urgencyHits = [];

    urgencyPatterns.forEach(item => {
        if (lower.includes(item)) {
            urgencyHits.push(item);
        }
    });

    if (urgencyHits.length > 0) {
        score += 1;
        explanations.push(
            "Urgency phrases detected (+1)"
        );
    }

    // CAPS

    const capsWords =
        words.filter(
            w =>
                w.length > 2 &&
                w === w.toUpperCase()
        );

    const capsRatio =
        capsWords.length /
        Math.max(wordCount, 1);

    if (capsRatio >= 0.10) {
        score += 1;
        explanations.push(
            "ALL CAPS ratio high (+1)"
        );
    }

    // Repeated Characters

    if (/(.)\1{2,}/.test(text)) {
        score += 1;
        explanations.push(
            "Repeated character spam (+1)"
        );
    }

    // Final

    const totalPoints = 10;

    const risk =
        Math.min(
            Math.round(
                (score / totalPoints) * 100
            ),
            100
        );

    const spam =
        score >= 3;

    const confidence =
        spam ? risk : 100 - risk;

    updateResult(
        spam,
        risk,
        confidence
    );

    updatePerformance(
        score,
        wordCount,
        links.length,
        matchedKeywords.length
    );

    updateWordAnalysis(
        text,
        matchedKeywords,
        urgencyHits
    );

    document.getElementById(
        "details"
    ).innerHTML =
        explanations.join("<br>");
}

function updateResult(
    spam,
    risk,
    confidence
) {

    const cls =
        document.getElementById(
            "classification"
        );

    cls.innerHTML =
        spam
            ? `<span class="spam">🚨 SPAM</span>`
            : `<span class="safe">✅ NOT SPAM</span>`;

    document.getElementById(
        "riskScore"
    ).innerHTML =
        `Risk Score: ${risk}%`;

    document.getElementById(
        "confidence"
    ).innerHTML =
        `Confidence: ${confidence}%`;

    animateBar(risk);
}

function animateBar(target) {

    const bar =
        document.getElementById(
            "riskBar"
        );

    let width = 0;

    const timer =
        setInterval(() => {

            if (width >= target) {
                clearInterval(timer);
            }
            else {
                width++;
                bar.style.width =
                    width + "%";
            }

        }, 8);
}

function updatePerformance(
    score,
    wordCount,
    links,
    keywords
) {

    document.getElementById(
        "performanceInsights"
    ).innerHTML = `
        <b>Performance Insights</b><br>
        Score: ${score}/10<br>
        Word Count: ${wordCount}<br>
        Links Found: ${links}<br>
        Spam Keywords: ${keywords}
    `;
}

function updateWordAnalysis(
    text,
    keywords,
    urgency
) {

    const words =
        text
            .toLowerCase()
            .match(/[a-z]+/g) || [];

    let counts = {};

    words.forEach(word => {
        if (word.length > 3) {
            counts[word] =
                (counts[word] || 0) + 1;
        }
    });

    const topWords =
        Object.entries(counts)
            .sort((a,b)=>b[1]-a[1])
            .slice(0,10);

    let html =
        `<h3>Word Level Analysis</h3>`;

    html +=
        `<b>Spam Keywords:</b><br>` +
        (keywords.join(", ") || "None");

    html +=
        `<br><br><b>Urgency Phrases:</b><br>` +
        (urgency.join(", ") || "None");

    html +=
        `<br><br><b>Top Words:</b><br>`;

    topWords.forEach(item => {
        html +=
            `${item[0]} (${item[1]})<br>`;
    });

    document.getElementById(
        "wordAnalysis"
    ).innerHTML = html;
}

function exportReport() {

    const report =
`
EMAIL SPAM REPORT

${document.getElementById("classification").innerText}

${document.getElementById("riskScore").innerText}

${document.getElementById("performanceInsights").innerText}
`;

    const blob =
        new Blob(
            [report],
            {type:"text/plain"}
        );

    const a =
        document.createElement("a");

    a.href =
        URL.createObjectURL(blob);

    a.download =
        "spam-report.txt";

    a.click();
}

function copyResult() {

    navigator.clipboard.writeText(
        document.getElementById(
            "performanceInsights"
        ).innerText
    );

    alert("Copied!");
}

function clearText() {

    document.getElementById(
        "emailContent"
    ).value = "";

    document.getElementById(
        "details"
    ).innerHTML = "";

    document.getElementById(
        "wordAnalysis"
    ).innerHTML = "";

    document.getElementById(
        "performanceInsights"
    ).innerHTML = "";
}

function loadSpamSample() {

    document.getElementById(
        "emailContent"
    ).value =
`CONGRATULATIONS!!!

You are a WINNER.

Claim your FREE prize.

Click here:
https://spam.com

Act now before offer ends!!!`;
}

function loadSafeSample() {

    document.getElementById(
        "emailContent"
    ).value =
`Hello John,

Meeting is scheduled for next week.

Please confirm attendance.

Thanks.`;
}
