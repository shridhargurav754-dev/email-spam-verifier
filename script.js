const spamKeywords = [
    "winner",
    "congratulations",
    "prize",
    "free",
    "urgent",
    "act now",
    "limited offer",
    "cash",
    "reward",
    "exclusive",
    "buy now",
    "investment",
    "million",
    "selected",
    "verify your account",
    "password",
    "account suspended",
    "security alert",
    "click here",
    "urgent action"
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

    const text = document
        .getElementById("emailContent")
        .value;

    if (!text.trim()) {
        alert("Paste email content first.");
        return;
    }

    let score = 0;
    let details = [];

    const wordCount =
        text.trim().split(/\s+/).length;

    if (wordCount > 100) {
        score += 2;
        details.push("Long email detected (+2)");
    }

    const lower = text.toLowerCase();

    let keywordHits = 0;

    spamKeywords.forEach(word => {
        if (lower.includes(word)) {
            keywordHits++;
        }
    });

    if (keywordHits > 0) {
        score += 2;
        details.push(
            `${keywordHits} spam keyword(s) found (+2)`
        );
    }

    const links =
        text.match(/https?:\/\/\S+|www\.\S+/gi);

    if (links) {
        score += links.length >= 3 ? 2 : 1;
        details.push(
            `${links.length} link(s) detected`
        );
    }

    const exclamations =
        (text.match(/!/g) || []).length;

    if (exclamations >= 5) {
        score += 1;
        details.push(
            "Too many exclamation marks (+1)"
        );
    }

    let urgencyFound = false;

    urgencyPatterns.forEach(item => {
        if (lower.includes(item)) {
            urgencyFound = true;
        }
    });

    if (urgencyFound) {
        score += 1;
        details.push(
            "Urgency phrase detected (+1)"
        );
    }

    const spam = score >= 3;

    document.getElementById(
        "classification"
    ).innerHTML =
        spam
        ? '<span class="spam">SPAM</span>'
        : '<span class="safe">NOT SPAM</span>';

    const risk =
        Math.min(
            Math.round((score / 10) * 100),
            100
        );

    document.getElementById(
        "riskScore"
    ).textContent =
        `Risk Score: ${risk}%`;

    document.getElementById(
        "details"
    ).innerHTML =
        details.length
        ? details.join("<br>")
        : "No spam indicators found.";
}

function clearText() {
    document.getElementById(
        "emailContent"
    ).value = "";

    document.getElementById(
        "classification"
    ).textContent =
        "Classification: -";

    document.getElementById(
        "riskScore"
    ).textContent =
        "Risk Score: 0%";

    document.getElementById(
        "details"
    ).innerHTML = "";
}

function loadSpamSample() {

    document.getElementById(
        "emailContent"
    ).value =
`CONGRATULATIONS!!!

You are a WINNER.

Claim your FREE prize now.

Click here:
https://spam-example.com

Act now before offer ends!`;
}

function loadSafeSample() {

    document.getElementById(
        "emailContent"
    ).value =
`Hello John,

Just checking regarding the meeting next week.

Please let me know if you can attend.

Thanks,
Support Team`;
}
