# -*- coding: utf-8 -*-
import asyncio
import random
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import logging
import sys
import json
import io
import unicodedata
from typing import List, Dict, Any

# Configuration de l'encodage
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """Normalise le texte en remplaçant les caractères accentués par leur équivalent non accentué."""
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

async def human_typing(page, selector, text, delay=0.1):
    """Simule une frappe humaine."""
    await page.focus(selector)
    for char in text:
        await page.keyboard.press(char)
        await asyncio.sleep(delay + random.uniform(0, 0.1))

async def wait_for_results(page, timeout=60000, max_retries=3):
    """Attend que les résultats apparaissent avec gestion des retries."""
    for attempt in range(max_retries):
        try:
            await page.wait_for_selector('div.result-item', timeout=timeout)
            logger.info("Résultats trouvés.")
            return True
        except PlaywrightTimeoutError:
            if attempt < max_retries - 1:
                logger.warning(f"Timeout atteint (tentative {attempt + 1}/{max_retries}). Nouvelle tentative...")
                await asyncio.sleep(5)
            else:
                logger.error("Échec de l'attente des résultats après plusieurs tentatives.")
                return False

async def extract_results(page, limit=20) -> List[Dict[str, str]]:
    """Extrait les résultats de la page en évitant les doublons."""
    results = await page.query_selector_all('div.result-item')
    extracted_data = []
    seen_titles = set()

    for result in results[:limit]:
        title_elem = await result.query_selector('div.result-body')
        link_elem = await result.query_selector('a')
        summary_elem = await result.query_selector('div.result-body')

        title_text = await title_elem.text_content() if title_elem else "No Title"
        link_href = await link_elem.get_attribute('href') if link_elem else "No Link"
        summary_text = await summary_elem.text_content() if summary_elem else "No Summary"
        
        # Vérifier si ce titre n'a pas déjà été vu
        if title_text.strip() not in seen_titles:
            extracted_data.append({
                "title": title_text.strip(),
                "link": link_href,
                "summary": summary_text.strip()
            })
            seen_titles.add(title_text.strip())

    logger.info(f"Nombre de résultats uniques extraits : {len(extracted_data)}")
    return extracted_data

async def run(playwright, query: str) -> List[Dict[str, Any]]:
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(locale='fr-FR')

    # Masquer les indicateurs d'automatisation
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    page = await context.new_page()

    try:
        # Accéder à l'URL
        logger.info("Accès à l'URL : https://beta.entscheidsuche.ch/")
        await page.goto("https://beta.entscheidsuche.ch/", wait_until="networkidle")

        # Saisie de la requête de recherche avec comportement humain
        logger.info(f"Recherche effectuée pour : {query}")
        await human_typing(page, 'input.form-control', query)
        await page.keyboard.press('Enter')
        
        # Attente des résultats avec gestion des retries
        if not await wait_for_results(page):
            logger.warning("Aucun résultat trouvé après plusieurs tentatives.")
            await page.screenshot(path="no_results_screenshot.png")
            return []

        # Scroll pour charger plus de résultats
        for _ in range(3):  # Augmenté à 3 scrolls
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

        # Extraction des résultats
        extracted_data = await extract_results(page)

        if extracted_data:
            return extracted_data
        else:
            logger.warning("Aucun résultat extrait. Capture d'écran sauvegardée.")
            await page.screenshot(path="no_results_screenshot.png")
            return []

    except Exception as e:
        logger.error(f"Une erreur s'est produite : {e}")
        await page.screenshot(path="error_screenshot.png")
        return []
    finally:
        await browser.close()

async def main(query: str) -> List[Dict[str, Any]]:
    query = normalize_text(query.encode('utf-8').decode('utf-8'))
    async with async_playwright() as playwright:
        return await run(playwright, query)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python beta_entscheidsuche_extractor.py <keyword>")
        sys.exit(1)

    keyword = sys.argv[1]
    results = asyncio.run(main(keyword))
    print(json.dumps(results, ensure_ascii=False, indent=2))
