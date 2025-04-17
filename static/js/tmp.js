const mediaId = document.getElementById("media_id_value")?.dataset.mediaId;
const subtitleContainer = document.getElementById("subtitles");
let subtitlesData = { es: [], fr: [], eslong: [], frlong: [] };
let activeTab = "es";
let currentIndex = -1;
let replayingSubtitleIndex = -1;
let displayedSubtitleIndex = -1
let replayingSubtitle = false;
let isEditingEs = false;
let isEditingFr = false;
const gap = 4;
const epsilon = 0.05;
let subtitles = [];

// Chargement des sous-titres
function loadSubtitles(variant) {
    fetch(`/subtitles?media_id=${mediaId}&variant=${variant}`)
        .then(response => response.json())
        .then(data => {
            subtitlesData[variant] = data;
            if (variant === "es") {
                subtitles = subtitlesData["es"];
                displaySubtitles(); // Afficher les sous-titres au démarrage
            }
        })
        .catch(error => console.error("Error loading subtitles:", error));
}

const currentSubtitleDiv = document.getElementById("current-subtitle");
updateCurrenrSubtitleColumns(4, gap);

function updateCurrenrSubtitleColumns(numberOfItems, gapInPercent) {
    currentSubtitleDiv.style.setProperty('--num-cols', numberOfItems);
    currentSubtitleDiv.style.setProperty('--col-gap', `${gapInPercent}%`);
}

function canSwitchSubtitle() {
    if (isEditingEs || isEditingFr) {
        abandon = window.confirm("Vous avez des modifications non enregistrées. Voulez-vous vraiment changer de sous-titre ?");
        if (abandon) {
            isEditingEs = false;
            isEditingFr = false;
            return true;
        } else {
            return false;
        }
    }
    return true;
}

function findCurrentSubtitleIndex(currentTime) {
    if (!subtitles || subtitles.length === 0) {
        console.warn("Le tableau 'subtitles' est vide ou non défini.");
        return -1;
    }

    for (let i = 0; i < subtitles.length; i++) {
        const start = subtitles[i].start - epsilon;
        const end = subtitles[i].end + epsilon;
        const nextStart = (i + 1 < subtitles.length) ? subtitles[i + 1].start : Infinity;
        const safeEnd = Math.min(end, nextStart - epsilon);
        if (currentTime >= start && currentTime < safeEnd) {
            return i;
        }
    }
    return -1;
}

function findClosestSubtitleIndex(currentTime) {
    if (!subtitles || subtitles.length === 0) {
        console.warn("Le tableau 'subtitles' est vide ou non défini.");
        return 0;
    }

    let closestIndex = 0;
    let smallestDiff = Math.abs(currentTime - subtitles[0].start);

    for (let i = 1; i < subtitles.length; i++) {
        const diff = Math.abs(currentTime - subtitles[i].start);
        if (diff < smallestDiff) {
            smallestDiff = diff;
            closestIndex = i;
        }
    }

    return closestIndex;
}

function findClosestPreviousSubtitleIndex(currentTime) {
    if (!subtitles || subtitles.length === 0) {
        console.warn("Le tableau 'subtitles' est vide ou non défini.");
        return 0;
    }
    for (let i = subtitles.length - 1; i >= 0; i--) {
        if (subtitles[i].end < currentTime - epsilon) {
            return i;
        }
    }
    return 0;
}

function findClosestNextSubtitleIndex(currentTime) {
    if (!subtitles || subtitles.length === 0) {
        console.warn("Le tableau 'subtitles' est vide ou non défini.");
        return 0;
    }
    for (let i = 0; i < subtitles.length; i++) {
        if (subtitles[i].start > currentTime + epsilon) {
            return i;
        }
    }
    return subtitles.length - 1;
}

function updateActiveSubtitle() {
    const video = document.getElementById("video");
    if (["esfrlong", "eslong", "frlong"].includes(activeTab)) {
        subtitles = subtitlesData["eslong"];
    } else {
        subtitles = subtitlesData["es"];
    }
    currentIndex = findCurrentSubtitleIndex(video.currentTime);
    if (currentIndex == displayedSubtitleIndex) return;
    if (isEditingEs || isEditingFr) {
        const confirmation = window.confirm("Vous avez des modifications non enregistrées. Voulez-vous vraiment changer de sous-titre ?");
        if (!confirmation) {
            return;
        }
    }
    currentSubtitleDiv.innerHTML = "";
    if (["es", "fr", "eslong", "frlong"].includes(activeTab)) {
        const subDiv = document.createElement("div");
        currentSubtitleDiv.appendChild(subDiv);
        subDiv.style.gridColumn = '1 / 5';
        subDiv.id = ["es", "eslong"].includes(activeTab) ? "es-sub" : "fr-sub";
        const editButton = document.createElement("button");
        editButton.textContent = "Editer";
        editButton.style.gridColumn = '1 / 5';
        editButton.id = `edit-button-${activeTab}`;
        editButton.style.display = "block";
        editButton.style.margin = "10px auto";
        editButton.onclick = enterEditMode;
        currentSubtitleDiv.appendChild(editButton);
        subDiv.textContent = currentIndex > -1 ? subtitlesData[activeTab][currentIndex].text || "" : "";
    } else if (["esfr", "esfrlong"].includes(activeTab)) {
        const esSubDiv = document.createElement("div");
        esSubDiv.id = "es-sub";
        esSubDiv.style.gridColumn = '1 / 3';
        currentSubtitleDiv.appendChild(esSubDiv);

        const frSubDiv = document.createElement("div");
        frSubDiv.id = "fr-sub";
        frSubDiv.style.gridColumn = '3 / 5';
        currentSubtitleDiv.appendChild(frSubDiv);

        if (currentIndex > -1) {
            if (activeTab == "esfr") {
                esSubDiv.textContent = subtitlesData["es"][currentIndex].text || "";
                frSubDiv.textContent = subtitlesData["fr"][currentIndex].text || "";
            } else {
                esSubDiv.textContent = subtitlesData["eslong"][currentIndex].text || "";
                frSubDiv.textContent = subtitlesData["frlong"][currentIndex].text || "";
            }

            const makeEditButton = (id, col) => {
                const btn = document.createElement("button");
                btn.textContent = "Editer";
                btn.style.gridColumn = col;
                btn.style.display = "block";
                btn.style.margin = "10px auto";
                btn.id = id;
                btn.onclick = enterEditMode;
                currentSubtitleDiv.appendChild(btn);
            };

            makeEditButton(`edit-button-${activeTab.includes("long") ? "eslong" : "es"}`, '1 / 3');
            makeEditButton(`edit-button-${activeTab.includes("long") ? "frlong" : "fr"}`, '3 / 5');
        }
    }
    displayedSubtitleIndex = currentIndex;
}

function displaySubtitles() {
    subtitleContainer.innerHTML = "";
    subtitlesData["es"].forEach((sub, index) => {
        const div = document.createElement("div");
        div.classList.add("subtitle");
        div.innerText = sub.text;
        div.dataset.start = sub.start;
        div.dataset.index = index;
        div.onclick = () => {
            const video = document.getElementById("video");
            video.currentTime = sub.start;
            if (!video.paused) video.play();
        };
        subtitleContainer.appendChild(div);
    });
}

document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
        if (canSwitchSubtitle()) {
            document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            activeTab = tab.dataset.type;
            displaySubtitles();
            displayedSubtitleIndex = -1;
            updateActiveSubtitle();
        }
    });
});

document.addEventListener("timeupdate", () => {
    const video = document.getElementById("video");
    updateActiveSubtitle();
    subtitlesData["es"].forEach((sub, index) => {
        const div = subtitleContainer.children[index];
        if (video.currentTime >= sub.start && video.currentTime < sub.end) {
            div.scrollIntoView({ behavior: "smooth", block: "center" });
            div.classList.add("active");
        } else {
            div.classList.remove("active");
        }
    });
});

function playVideo() {
    const video = document.getElementById("video");
    video.play();
    replayingSubtitle = false;
}

function replaySubtitle() {
    const video = document.getElementById("video");
    if (!replayingSubtitle) {
        currentIndex = findClosestSubtitleIndex(video.currentTime);
    }
    if (!replayingSubtitle) {
        replayingSubtitleIndex = currentIndex;
        replayingSubtitle = true;
    }
    if (replayingSubtitleIndex >= 0) {
        video.currentTime = subtitles[replayingSubtitleIndex].start - 1.0;
        video.play();
        setTimeout(() => {
            video.pause();
        }, ((subtitles[replayingSubtitleIndex].end - subtitles[replayingSubtitleIndex].start) + 2.0) * 1000);
    }
}

function nextSubtitle() {
    const video = document.getElementById("video");
    currentIndex = findClosestNextSubtitleIndex(video.currentTime);
    replayingSubtitle = false;
    video.currentTime = subtitles[currentIndex].start + epsilon;
    updateActiveSubtitle();
    if (!video.paused) video.play();
}

function previousSubtitle() {
    const video = document.getElementById("video");
    currentIndex = findClosestPreviousSubtitleIndex(video.currentTime);
    replayingSubtitle = false;
    video.currentTime = subtitles[currentIndex].start + epsilon;
    updateActiveSubtitle();
    if (!video.paused) video.play();
}

function setupControls() {
    document.querySelector(".replay-btn")?.addEventListener("click", replaySubtitle);
    document.querySelector(".play-btn")?.addEventListener("click", playVideo);
    document.querySelector(".next-btn")?.addEventListener("click", nextSubtitle);
    document.querySelector(".prev-btn")?.addEventListener("click", previousSubtitle);
}

function initializeVideoViewer() {
    setupControls();
    loadSubtitles("es");
    loadSubtitles("fr");
    loadSubtitles("eslong");
    loadSubtitles("frlong");
}
