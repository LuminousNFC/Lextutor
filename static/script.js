const CONFIG = {
    API_BASE_URL: "http://127.0.0.1:8080",
    WS_URL: "ws://127.0.0.1:8080/ws",
    MAX_RECONNECT_ATTEMPTS: 5,
    FETCH_TIMEOUT: 60000,
};

const SELECTORS = {
    messageForm: "#message-form",
    userInput: "#user-input",
    keyword1: "#keyword-1",
    keyword2: "#keyword-2",
    keyword3: "#keyword-3",
    messagesContainer: "#messages",
    statusText: "#status-text",
    articlesContainer: "#articles-content",
    searchResultsContent: "#search-results-content",
    clearButton: "#clear-button",
    lawSelect: "#law-select",
    articleNumber: "#article-number",
    fetchArticleButton: "#fetch-article-button",
    articleResult: "#article-result",
    timer: "#timer",
    debugInfo: "#debug-info",
    errorMessage: "#error-message",
};

const elements = Object.fromEntries(
    Object.entries(SELECTORS).map(([key, selector]) => [key, document.querySelector(selector)])
);

const articleCache = new Map();
const jurisprudenceCache = new Set();

const appState = {
    currentQuestion: "",
    articles: [],
    jurisprudence: [],
    isLoading: false,
};

let dataProcessed = {
    assistantResponse: false,
    articles: false,
    jurisprudence: false
};

window.addEventListener('error', function (event) {
    console.error('Erreur JavaScript capturée:', event.error);
    elements.errorMessage.textContent = 'Une erreur inattendue est survenue. Veuillez réessayer.';
});

function decodeAndNormalizeText(text) {
    const textArea = document.createElement('textarea');
    textArea.innerHTML = text;
    let decodedText = textArea.value;

    decodedText = decodedText.normalize('NFC');

    const specialChars = {
        'Ã©': 'é', 'Ã¨': 'è', 'Ãª': 'ê', 'Ã ': 'à', 'Ã¢': 'â',
        'Ã´': 'ô', 'Ã®': 'î', 'Ã¯': 'ï', 'Ã§': 'ç', 'Ã¹': 'ù',
        'Ã»': 'û', 'Ã¼': 'ü', 'Ãœ': 'Ü', 'Å"': 'œ', 'Ã¦': 'æ',
        'Ã€': 'À', 'Ã‰': 'É', 'â€"': '–', 'â€™': "'", 'â€œ': '"',
        'â€': '"', 'â€¢': '•', 'â€"': '—', 'â€¦': '…', 'â€°': '‰',
        'Â ': ' ', 'Ã\xa0': 'à'
    };

    Object.entries(specialChars).forEach(([encoded, decoded]) => {
        decodedText = decodedText.replace(new RegExp(encoded, 'g'), decoded);
    });

    return decodedText;
}

function sanitizeAndNormalizeText(text) {
    if (typeof text !== 'string') return '';
    text = decodeAndNormalizeText(text);
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function displayDebugInfo(info) {
    console.log("Debug info:", info);
    if (elements.debugInfo) {
        elements.debugInfo.innerHTML += `<p>${JSON.stringify(info)}</p>`;
    }
}

function setLoadingIndicator(isLoading) {
    appState.isLoading = isLoading;
    if (elements.statusText) {
        elements.statusText.textContent = isLoading
            ? "Chargement..."
            : "En attente d'une question...";
    }
}

function appendMessageAndSave(role, content) {
    appendMessage(role, content);
    const conversation = loadSavedConversation();
    conversation.push({ role, content });
    saveConversationLocally(conversation);
}

function appendMessage(role, content) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}-message`;
    
    if (typeof content === 'object') {
        messageDiv.innerHTML = formatComplexContent(content);
    } else if (role === "assistant" && typeof content === 'string') {
        messageDiv.innerHTML = formatAssistantResponse(content);
    } else {
        messageDiv.textContent = content;
    }
    
    if (elements.messagesContainer) {
        elements.messagesContainer.appendChild(messageDiv);
        elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    } else {
        console.error("Élément messagesContainer non trouvé dans le DOM.");
    }
}

function formatComplexContent(content) {
    let formattedContent = '<div class="complex-content">';
    for (const [key, value] of Object.entries(content)) {
        formattedContent += `<div class="content-item"><strong>${key}:</strong> ${sanitizeAndNormalizeText(JSON.stringify(value))}</div>`;
    }
    formattedContent += '</div>';
    return formattedContent;
}

function saveConversationLocally(conversation) {
    localStorage.setItem("savedConversation", JSON.stringify(conversation));
}

function loadSavedConversation() {
    return JSON.parse(localStorage.getItem("savedConversation") || "[]");
}

function clearSavedConversation() {
    localStorage.removeItem("savedConversation");
}

function loadConversationHistory() {
    const savedConversation = loadSavedConversation();
    if (elements.messagesContainer) {
        elements.messagesContainer.innerHTML = "";
        savedConversation.forEach((message) => appendMessage(message.role, message.content));
    } else {
        console.error("Élément messagesContainer non trouvé dans le DOM.");
    }
}

function clearQuestionHistory() {
    if (elements.messagesContainer) elements.messagesContainer.innerHTML = "";
    if (elements.articlesContainer) elements.articlesContainer.innerHTML = "<h3>Articles mentionnés :</h3>";
    if (elements.searchResultsContent) elements.searchResultsContent.innerHTML = "<h3>Jurisprudence pertinente :</h3>";
    if (elements.statusText) elements.statusText.textContent = "En attente d'une question...";
    resetTimer();
    clearSavedConversation();
}

function formatAssistantResponse(response) {
    if (typeof response !== 'string') {
        console.error('La réponse n\'est pas une chaîne:', response);
        return '<p>Erreur: Réponse inattendue du serveur</p>';
    }

    const sections = response.split("\n\n");
    let formattedResponse = '<div class="legal-analysis">';

    const sectionFormatters = {
        "Domaine(s) juridique(s) :": (content) => `<h2>Domaine(s) juridique(s)</h2><p>${sanitizeAndNormalizeText(content)}</p>`,
        "Articles de Loi :": (content) => `<h2>Articles de Loi</h2><ul>${formatList(content)}</ul>`,
        "Mots-clés :": (content) => `<h2>Mots-clés</h2><ul>${formatList(content)}</ul>`,
        "Résumé :": (content) => `<h2>Résumé</h2><p>${sanitizeAndNormalizeText(content)}</p>`,
        "Principe jurisprudentiel / Arrêt de référence :": (content) => `<h2>Principe jurisprudentiel / Arrêt de référence</h2><ul>${formatList(content)}</ul>`,
        "Controverse ou évolution": (content) => `<h2>Controverse ou évolution</h2><p>${sanitizeAndNormalizeText(content)}</p>`
    };

    sections.forEach((section) => {
        const [title, ...content] = section.split(":");
        const formatter = sectionFormatters[title.trim()];
        if (formatter) {
            formattedResponse += formatter(sanitizeAndNormalizeText(content.join(":").trim()));
        } else {
            formattedResponse += `<p>${sanitizeAndNormalizeText(section)}</p>`;
        }
    });

    return formattedResponse + "</div>";
}

function formatList(content) {
    return content.split("\n").slice(1)
        .map(item => `<li>${sanitizeAndNormalizeText(item.trim())}</li>`)
        .join("");
}

function displayRealTimeData(data) {
    if (data.assistantResponse && !dataProcessed.assistantResponse) {
        console.log("Affichage de la réponse de l'assistant");
        appendMessage("assistant", data.assistantResponse);
        dataProcessed.assistantResponse = true;
    }

    if (data.articles && Array.isArray(data.articles) && !dataProcessed.articles) {
        console.log("Extraction des articles en arrière-plan");
        appendMessage("system", "Extraction des articles en cours...");
        data.articles.forEach(article => setTimeout(() => displayArticle(article), 0));
        dataProcessed.articles = true;
    }

    if (data.jurisprudence && Array.isArray(data.jurisprudence) && !dataProcessed.jurisprudence) {
        console.log("Extraction de la jurisprudence en arrière-plan");
        appendMessage("system", "Extraction de la jurisprudence en cours...");
        setTimeout(() => displayJurisprudence(data.jurisprudence), 0);
        dataProcessed.jurisprudence = true;
    }
}

function cacheArticle(article) {
    const cacheKey = `${article.law_code}-${article.article_number}`;
    articleCache.set(cacheKey, article);
}

async function displayArticle(article) {
    if (!elements.articlesContainer) {
        console.error("L'élément articles-content est introuvable dans le DOM.");
        return;
    }

    let articlesContent = elements.articlesContainer.querySelector('.articles-content');
    if (!articlesContent) {
        articlesContent = document.createElement('div');
        articlesContent.className = 'articles-content';
        elements.articlesContainer.innerHTML = "<h3>Articles extraits :</h3>";
        elements.articlesContainer.appendChild(articlesContent);
    }

    const existingArticle = document.getElementById(`article-${article.law_code}-${article.article_number}`);
    if (existingArticle) {
        console.log(`L'article ${article.law_code} ${article.article_number} existe déjà. Mise à jour du contenu.`);
        updateArticleDiv(existingArticle, article);
    } else {
        const articleDiv = createArticleDiv(article);
        articlesContent.appendChild(articleDiv);
        articleDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function createArticleDiv(article) {
    const articleDiv = document.createElement("div");
    articleDiv.classList.add("article-item");
    const articleId = `article-${article.law_code}-${article.article_number}`;
    articleDiv.id = articleId;

    articleDiv.innerHTML = `
        <div class="article-header">
            <h3>${sanitizeAndNormalizeText(article.law_code)} ${sanitizeAndNormalizeText(article.article_number)}: ${sanitizeAndNormalizeText(article.title || "Sans titre")}</h3>
            <button class="toggle-button" onclick="toggleArticleContent('${articleId}')">Afficher/Masquer</button>
        </div>
        <div id="content-${articleId}" class="article-content" style="display: none;">
            ${formatArticleContent(article)}
        </div>
    `;

    return articleDiv;
}

function updateArticleDiv(existingArticleDiv, newArticle) {
    const headerElement = existingArticleDiv.querySelector('.article-header h3');
    const contentElement = existingArticleDiv.querySelector('.article-content');
    
    headerElement.textContent = `${sanitizeAndNormalizeText(newArticle.law_code)} ${sanitizeAndNormalizeText(newArticle.article_number)}: ${sanitizeAndNormalizeText(newArticle.title || "Sans titre")}`;
    contentElement.innerHTML = formatArticleContent(newArticle);
}

function formatArticleContent(article) {
    if (typeof article !== 'object' || article === null) {
        console.error("Format d'article invalide dans formatArticleContent:", article);
        return "Erreur: Format d'article invalide";
    }
    const fedlexLink = getFedlexLink(article.law_code, article.article_number);
    const linkText = fedlexLink
        ? `<a href="${fedlexLink}" target="_blank" rel="noopener noreferrer">Voir sur Fedlex</a>`
        : "Lien non disponible";
    
    return `
        <div class="article-text">
            <h4>${sanitizeAndNormalizeText(article.law_code || "")} ${sanitizeAndNormalizeText(article.article_number || "")}</h4>
            <h5>${sanitizeAndNormalizeText(article.title || "")}</h5>
            <div class="article-body">${sanitizeAndNormalizeText(article.content || article.full_text || "Contenu non disponible")}</div>
            <div class="article-link">${linkText}</div>
        </div>
    `;
}

function toggleArticleContent(articleId) {
    const contentDiv = document.getElementById(`content-${articleId}`);
    if (contentDiv) {
        contentDiv.style.display = contentDiv.style.display === "none" ? "block" : "none";
    } else {
        console.error(`Élément content-${articleId} non trouvé`);
    }
}

async function displayJurisprudence(jurisprudence) {
    if (elements.searchResultsContent) {
        let jurisprudenceContainer = elements.searchResultsContent.querySelector('.jurisprudence-container');
        if (!jurisprudenceContainer) {
            elements.searchResultsContent.innerHTML = "<h3>Jurisprudence pertinente :</h3>";
            jurisprudenceContainer = document.createElement("div");
            jurisprudenceContainer.className = "jurisprudence-container";
            elements.searchResultsContent.appendChild(jurisprudenceContainer);
        }

        if (Array.isArray(jurisprudence) && jurisprudence.length > 0) {
            jurisprudence.forEach((item) => {
                const jurisprudenceItem = createJurisprudenceItem(item);
                jurisprudenceContainer.appendChild(jurisprudenceItem);
            });
        }
    } else {
        console.error("Élément searchResultsContent non trouvé dans le DOM.");
    }
}

function createJurisprudenceItem(item) {
    const itemDiv = document.createElement("div");
    itemDiv.className = "jurisprudence-item";

    const title = document.createElement("h3");
    title.textContent = sanitizeAndNormalizeText(item.title || "Jurisprudence sans titre");
    itemDiv.appendChild(title);

    const summary = document.createElement("p");
    summary.textContent = sanitizeAndNormalizeText(item.summary || "Aucun résumé disponible");
    itemDiv.appendChild(summary);

    return itemDiv;
}

let startTime;
let timerAnimationFrame;

function startTimer() {
    startTime = Date.now();
    updateTimer();
}

function stopTimer() {
    if (timerAnimationFrame) {
        cancelAnimationFrame(timerAnimationFrame);
        timerAnimationFrame = null;
    }
}

function resetTimer() {
    stopTimer();
    if (elements.timer) {
        elements.timer.textContent = "Temps écoulé: 0 secondes";
    }
}

function updateTimer() {
    const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
    if (elements.timer) {
        elements.timer.textContent = `Temps écoulé: ${elapsedTime} secondes`;
    }
    timerAnimationFrame = requestAnimationFrame(updateTimer);
}

class LegalAnalyzer {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.shouldReconnect = true;
        this.connectWebSocket();
    }

    connectWebSocket() {
        try {
            this.socket = new WebSocket(CONFIG.WS_URL);

            this.socket.onopen = () => {
                console.log("Connexion WebSocket ouverte");
                if (elements.statusText) {
                    elements.statusText.textContent = "Connecté au serveur";
                }
                this.reconnectAttempts = 0;
            };

            this.socket.onmessage = (event) => {
                console.log("Message WebSocket reçu:", event.data);
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.warn("Message non-JSON reçu:", event.data);
                    this.handleNonJsonMessage(event.data);
                }
            };

            this.socket.onclose = (event) => {
                console.warn("Connexion WebSocket fermée:", event);
                if (elements.statusText) {
                    elements.statusText.textContent = "Déconnecté du serveur";
                }

                if (this.shouldReconnect && this.reconnectAttempts < CONFIG.MAX_RECONNECT_ATTEMPTS) {
                    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000);
                    setTimeout(() => this.connectWebSocket(), delay);
                    this.reconnectAttempts++;
                } else if (!this.shouldReconnect) {
                    console.log("La reconnexion automatique est désactivée.");
                } else {
                    if (elements.statusText) {
                        elements.statusText.textContent = "Impossible de se reconnecter";
                    }
                    displayDebugInfo("Nombre maximum de tentatives de reconnexion atteint");
                }
            };

            this.socket.onerror = (error) => {
                console.error("Erreur WebSocket:", error);
                if (elements.statusText) {
                    elements.statusText.textContent = "Erreur de connexion";
                }
            };
        } catch (error) {
            console.error("Erreur lors de la connexion WebSocket:", error);
            if (elements.statusText) {
                elements.statusText.textContent = "Erreur lors de la connexion WebSocket";
            }
        }
    }

    closeWebSocket() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.shouldReconnect = false;
            this.socket.close();
            console.log("WebSocket fermé manuellement.");
        }
    }

    async handleWebSocketMessage(data) {
        console.log("Traitement du message WebSocket:", JSON.stringify(data, null, 2));
        displayDebugInfo(data);
        switch (data.type) {
            case "progress":
                console.log("Progression:", data.data);
                appendMessageAndSave("system", data.data);
                break;
            case "result":
                if (data.data && data.data.error) {
                    console.error("Erreur reçue du serveur:", data.data.error);
                    appendMessageAndSave("system", `Erreur: ${sanitizeAndNormalizeText(data.data.error)}`);
                } else if (data.data) {
                    displayRealTimeData(data.data);
                }
                break;
            case "article":
                if (data.data) {
                    await this.handleArticleMessage(data.data);
                }
                break;
            case "jurisprudence":
                if (data.data && this.isNewJurisprudence(data.data)) {
                    await displayJurisprudence([data.data]);
                }
                break;
            case "assistantResponse":
                if (typeof data.data === 'string') {
                    appendMessageAndSave("assistant", data.data);
                } else {
                    console.error('Réponse inattendue de l\'assistant:', data);
                    appendMessageAndSave("assistant", "Erreur: Réponse inattendue du serveur");
                }
                break;
            case "analysis":
                if (typeof data.data === 'object') {
                    this.displayAnalysisData(data.data);
                } else {
                    console.error('Analyse inattendue:', data);
                    appendMessageAndSave("system", "Erreur: Analyse inattendue du serveur");
                }
                break;
            case "complete":
                console.log("Traitement terminé");
                stopTimer();
                dataProcessed = {
                    assistantResponse: false,
                    articles: false,
                    jurisprudence: false
                };
                appendMessageAndSave("system", "Traitement terminé");
                break;
            case "error":
                console.error("Erreur reçue du serveur:", data.data);
                appendMessageAndSave("system", `Erreur: ${sanitizeAndNormalizeText(data.data)}`);
                break;
            case "log":
                console.log("Log du serveur:", data.message);
                break;
            default:
                console.warn("Type de message WebSocket inconnu:", data.type);
        }
    }

    displayAnalysisData(analysisData) {
        if (analysisData['Domaines juridiques']) {
            appendMessageAndSave("system", `Domaines juridiques : ${analysisData['Domaines juridiques']}`);
        }
        if (analysisData['Articles de Loi']) {
            appendMessageAndSave("system", "Articles de Loi mentionnés :");
            analysisData['Articles de Loi'].forEach(article => {
                appendMessageAndSave("system", `- ${article.law_code} ${article.article_number}: ${article.description}`);
            });
        }
        if (analysisData['Résumé']) {
            appendMessageAndSave("system", `Résumé : ${analysisData['Résumé']}`);
        }
    }

    async handleArticleMessage(article) {
        if (typeof article !== 'object' || article === null) {
            console.error("Format d'article invalide:", article);
            return;
        }
        cacheArticle(article);
        await displayArticle(article);
    }

    isNewJurisprudence(jurisprudence) {
        const jurisprudenceKey = jurisprudence.title;
        if (jurisprudenceCache.has(jurisprudenceKey)) {
            console.log("Jurisprudence déjà reçue:", jurisprudenceKey);
            return false;
        }
        jurisprudenceCache.add(jurisprudenceKey);
        return true;
    }

    handleNonJsonMessage(message) {
        console.log("Message non-JSON reçu:", message);
        if (typeof message === 'string' && message.includes('Extraction de l\'article réussie')) {
            const articleMatch = message.match(/\[({.*?})\]/);
            if (articleMatch && articleMatch[1].trim().startsWith('{')) {
                try {
                    const articleData = JSON.parse(articleMatch[1].replace(/'/g, '"'));
                    this.handleArticleMessage(articleData);
                } catch (error) {
                    console.error("Erreur lors du parsing de l'article:", error);
                    if (elements.articleResult) {
                        elements.articleResult.textContent = `Erreur: Impossible de traiter l'article. ${error.message}`;
                    }
                }
            } else {
                console.error("Format d'article invalide dans le message non-JSON");
                if (elements.articleResult) {
                    elements.articleResult.textContent = "Erreur: Format d'article invalide reçu du serveur.";
                }
            }
        } else {
            console.warn("Message non-JSON inattendu reçu");
            if (elements.statusText) {
                elements.statusText.textContent = "Message inattendu reçu du serveur";
            }
        }
    }

    async processQuestion(question, keywords) {
        console.log("Traitement de la question:", question);
        resetTimer();
        startTimer();

        appendMessageAndSave("user", question);
        elements.userInput.value = "";
        elements.keyword1.value = "";
        elements.keyword2.value = "";
        elements.keyword3.value = "";
        setLoadingIndicator(true);

        const requestData = {
            question,
            keywords: keywords.filter(Boolean),
        };

        try {
            await this.sendQuestionViaWebSocket(requestData);
        } catch (error) {
            console.error("Erreur lors du traitement de la question:", error);
            if (elements.statusText) {
                elements.statusText.textContent = "Une erreur est survenue";
            }
            appendMessageAndSave(
                "system",
                `Désolé, une erreur s'est produite lors de l'envoi de votre demande: ${sanitizeAndNormalizeText(error.message)}`
            );
            stopTimer();
        } finally {
            setLoadingIndicator(false);
        }
    }

    async sendQuestionViaWebSocket(data) {
        console.log("Envoi de la question via WebSocket");
        if (this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        } else {
            console.error("WebSocket n'est pas connecté");
            appendMessageAndSave("system", "Erreur: La connexion au serveur est perdue. Veuillez rafraîchir la page.");
            throw new Error("WebSocket n'est pas connecté");
        }
    }
}

async function fetchWithTimeout(url, options, timeout = CONFIG.FETCH_TIMEOUT) {
    console.log(`Fetching ${url} with timeout ${timeout}`);
    try {
        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), timeout);
        const response = await fetch(url, { ...options, signal: controller.signal });
        clearTimeout(id);
        if (!response.ok) {
            throw new Error(`Erreur HTTP! Statut: ${response.status}`);
        }
        const text = await response.text();
        return JSON.parse(decodeAndNormalizeText(text));
    } catch (error) {
        console.error(`Erreur lors de la requête ${url}:`, error);
        if (elements.errorMessage) {
            elements.errorMessage.textContent = `Erreur: ${sanitizeAndNormalizeText(error.message)}`;
        }
        throw error;
    }
}

async function fetchArticleWithRetry(lawCode, articleNumber, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fetchArticle(lawCode, articleNumber);
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            console.log(`Tentative ${i + 1} échouée, nouvel essai...`);
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }
}

async function fetchArticle(lawCode, articleNumber) {
    console.log(`Récupération de l'article: ${lawCode} ${articleNumber}`);
    try {
        const response = await fetchWithTimeout(
            `${CONFIG.API_BASE_URL}/api/fetch-article`,
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ lawCode, articleNumber }),
            }
        );

        if (!response.success) {
            throw new Error(response.error || "Erreur inconnue lors de la récupération de l'article");
        }

        displayDebugInfo(response);
        return response;
    } catch (error) {
        console.error("Erreur lors de la récupération de l'article:", error);
        if (elements.articleResult) {
            if (error.name === 'AbortError') {
                elements.articleResult.textContent = "La requête a pris trop de temps. Veuillez réessayer.";
            } else {
                elements.articleResult.textContent = `Erreur lors de la récupération de l'article: ${sanitizeAndNormalizeText(error.message)}`;
            }
        }
        throw error;
    }
}

function getFedlexLink(lawCode, articleNumber) {
    const reference = fedlexReferences[lawCode];
    if (reference) {
        return `${reference.lien}#art_${articleNumber}`;
    }
    return null;
}

let fedlexReferences;

fetch('/static/fedlex_references.json')
    .then(response => response.json())
    .then(data => {
        fedlexReferences = data;
        populateLawSelect();
    })
    .catch(error => {
        console.error('Erreur lors du chargement de fedlex_references.json:', error);
    });

function populateLawSelect() {
    if (elements.lawSelect) {
        const lawSelect = elements.lawSelect;
        lawSelect.innerHTML = '<option value="">Sélectionnez une loi</option>';

        for (const [code, info] of Object.entries(fedlexReferences || {})) {
            const option = document.createElement('option');
            option.value = code;
            option.textContent = `${code} - ${info.titre}`;
            lawSelect.appendChild(option);
        }
    } else {
        console.error("Élément lawSelect non trouvé dans le DOM.");
    }
}

let legalAnalyzer;

window.addEventListener("load", function () {
    console.log("Chargement de la fenêtre terminé");
    legalAnalyzer = new LegalAnalyzer();
    clearQuestionHistory();
    loadConversationHistory();
});

window.addEventListener("error", function (event) {
    console.error("Erreur non gérée:", event.error);
    if (elements.errorMessage) {
        elements.errorMessage.innerHTML = `
        <p>Une erreur inattendue s'est produite:</p>
        <pre>${event.error.stack}</pre>
        <p>Veuillez réessayer ou contacter l'administrateur.</p>
    `;
    }
});

window.toggleArticleContent = toggleArticleContent;

if (elements.messageForm) {
    elements.messageForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        console.log("Formulaire soumis");

        const question = elements.userInput.value.trim();
        const keywords = [
            elements.keyword1.value.trim(),
            elements.keyword2.value.trim(),
            elements.keyword3.value.trim()
        ];

        if (!question) return;

        await legalAnalyzer.processQuestion(question, keywords);
    });
} else {
    console.error("Élément messageForm non trouvé dans le DOM.");
}

if (elements.clearButton) {
    elements.clearButton.addEventListener("click", function () {
        console.log("Bouton d'effacement de l'historique cliqué");
        clearQuestionHistory();
    });
} else {
    console.error("Élément clearButton non trouvé dans le DOM.");
}

if (elements.fetchArticleButton) {
    elements.fetchArticleButton.addEventListener("click", async function () {
        console.log("Bouton de récupération d'article cliqué");
        const lawCode = elements.lawSelect.value;
        const artNumber = elements.articleNumber.value.trim();
        if (!lawCode || !artNumber) {
            if (elements.articleResult) {
                elements.articleResult.textContent =
                    "Veuillez sélectionner une loi et entrer un numéro d'article.";
            }
            return;
        }

        try {
            const article = await fetchArticleWithRetry(lawCode, artNumber);
            if (article.success) {
                if (elements.articleResult) {
                    elements.articleResult.innerHTML = formatArticleContent(article);
                }
            } else if (article.error) {
                if (elements.articleResult) {
                    elements.articleResult.textContent = `Erreur: ${sanitizeAndNormalizeText(article.error)}`;
                }
            } else {
                if (elements.articleResult) {
                    elements.articleResult.textContent = "Contenu de l'article non disponible.";
                }
            }
        } catch (error) {
            console.error("Erreur:", error);
            if (elements.articleResult) {
                elements.articleResult.textContent = `Erreur lors de la récupération de l'article: ${sanitizeAndNormalizeText(error.message)}`;
            }
        }
    });
} else {
    console.error("Élément fetchArticleButton non trouvé dans le DOM.");
}
