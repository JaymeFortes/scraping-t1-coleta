import re
import csv
import json
import os
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE = "https://www.infojobs.com.br"
URL = f"{BASE}/vagas-de-emprego-advogado-criminalista-em-porto-alegre,-rs.aspx"
# Cada lote normalmente contém cerca de 20 vagas.
LOTES_ALVO = 4

resp = requests.get(URL)
print(resp.status_code)
#print(resp.text)

def texto(el, default=""):
    if not el:
        return default
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()


def extrair_vaga(card):
    link_el = card.select_one("[data-href]")
    link = urljoin(BASE, link_el["data-href"]) if link_el else ""

    local = texto(card.select_one("div.mb-8")).split(",")[0].strip()

    # O salário pode não existir no card.
    salario = ""
    money = card.select_one("svg.icon-money")
    if money:
        salario = texto(money.find_parent("div"))

    # A descrição é o último bloco de texto do card.
    mediums = card.select("div.text-medium")
    descricao = texto(mediums[-1]) if mediums else ""

    return {
        "titulo": texto(card.select_one("h2.js_vacancyTitle")),
        "empresa": texto(card.select_one("a[href*='/empresa-']"), "Não informada"),
        "local": local or "Não informado",
        "salario": salario or "Não informado",
        "link": link,
        "descricao": descricao or "Não informada",
    }


def coletar_html_com_scroll(url, lotes_alvo):
    opts = Options()
    # opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1200,900")
    driver = webdriver.Chrome(options=opts)
    try:
        driver.get(url)
        time.sleep(3)
        qtd_anterior, estaveis = 0, 0
        # Máximo de três rolagens por lote desejado.
        for i in range(lotes_alvo * 3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.5)

            qtd = len(driver.find_elements(
    By.XPATH,
    "//div[contains(concat(' ', normalize-space(@class), ' '), ' card ') "
    "and contains(concat(' ', normalize-space(@class), ' '), ' js_rowCard ')]"
))

            print(f"  scroll {i+1}: {qtd} vagas")
            # Para após duas rolagens seguidas sem novas vagas.
            if qtd == qtd_anterior:
                estaveis += 1
                if estaveis >= 2:
                    break
            else:
                estaveis = 0
            qtd_anterior = qtd
            if qtd >= lotes_alvo * 20:
                break
        return driver.page_source
    finally:
        driver.quit()


def proximo_numero_arquivo():
    # Evita sobrescrever resultados de execuções anteriores.
    numero = 1
    while (os.path.exists(f"vagas_infojobs_{numero}.csv")
           or os.path.exists(f"vagas_infojobs_{numero}.json")):
        numero += 1
    return numero


def main():
    print("Coletando com scroll...")
    html = coletar_html_com_scroll(URL, LOTES_ALVO)

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.card.js_rowCard")
    print(f"Cards no HTML: {len(cards)}")

    vistos = set()
    vagas = []
    for card in cards:
        vaga = extrair_vaga(card)
        # Ignora cards incompletos e vagas repetidas.
        if not vaga["link"] or not vaga["titulo"]:
            continue
        if vaga["link"] in vistos:
            continue
        vistos.add(vaga["link"])
        vagas.append(vaga)

    print(f"Vagas únicas após dedup: {len(vagas)}")

    com_salario = sum(1 for v in vagas if v["salario"] != "A combinar"
                      and v["salario"] != "Não informado")
    print(f"Vagas com faixa salarial informada: {com_salario}")

    campos = ["titulo", "empresa", "local", "salario", "link", "descricao"]
    numero_arquivo = proximo_numero_arquivo()
    nome_csv = f"vagas_infojobs_{numero_arquivo}.csv"
    nome_json = f"vagas_infojobs_{numero_arquivo}.json"
    # utf-8-sig para o Excel reconhecer os acentos.
    with open(nome_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(vagas)

    with open(nome_json, "w", encoding="utf-8") as f:
        json.dump(vagas, f, ensure_ascii=False, indent=2)

    print(f"\nArquivos gerados: {nome_csv} e {nome_json}")


if __name__ == "__main__":
    main()
