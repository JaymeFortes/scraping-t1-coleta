import re  # Permite limpar e padronizar espaços nos textos extraídos.
import csv  # Permite criar o arquivo de resultados no formato CSV.
import json  # Permite criar o arquivo de resultados no formato JSON.
import os  # Permite verificar se os arquivos de uma execução já existem.
import time  # Permite esperar o carregamento da página após cada ação.
from urllib.parse import urljoin  # Monta URLs completas a partir de links relativos.

from bs4 import BeautifulSoup  # Converte o HTML em uma estrutura pesquisável.
from selenium import webdriver  # Controla o navegador automaticamente.
from selenium.webdriver.chrome.options import Options  # Configurações do Chrome.

# Define o tipo de seletor usado pelo Selenium, neste caso XPath.
from selenium.webdriver.common.by import By

# Endereço principal do site, usado para completar links relativos.
BASE = "https://www.infojobs.com.br"
# Página de busca que será aberta pelo navegador.
URL = f"{BASE}/vagas-de-emprego-desenvolvedor-em-porto-alegre,-rs.aspx"
# Quantidade desejada de lotes de vagas; cada lote normalmente contém cerca de 20 vagas.
LOTES_ALVO = 4


def texto(el, default=""):
    # Se o elemento não existir, devolve o valor padrão informado.
    if not el:
        return default
    # Obtém o texto visível, transforma vários espaços em um só e remove espaços externos.
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()


def extrair_vaga(card):
    # Procura o elemento que contém o endereço da vaga no atributo data-href.
    link_el = card.select_one("[data-href]")
    # Converte o endereço relativo em uma URL completa; se não houver link, usa texto vazio.
    link = urljoin(BASE, link_el["data-href"]) if link_el else ""

    # Procura o local da vaga, separa pelo primeiro caractere vírgula e usa a primeira parte.
    local = texto(card.select_one("div.mb-8")).split(",")[0].strip()

    # Começa com salário vazio porque o campo pode não existir no card.
    salario = ""
    # Procura o ícone HTML que identifica a informação de salário.
    money = card.select_one("svg.icon-money")
    # Só tenta buscar o texto do salário se o ícone tiver sido encontrado.
    if money:
        # Sobe até o elemento pai do ícone e extrai o texto desse bloco.
        salario = texto(money.find_parent("div"))

    # Seleciona todos os elementos que podem conter partes da descrição da vaga.
    mediums = card.select("div.text-medium")
    # Usa o último elemento encontrado, ou texto vazio se nenhum existir.
    descricao = texto(mediums[-1]) if mediums else ""

    # Devolve os dados da vaga em um dicionário com nomes de campos organizados.
    return {
        # Título encontrado no h2 com a classe usada pela página.
        "titulo": texto(card.select_one("h2.js_vacancyTitle")),
        # Nome da empresa; usa "Não informada" quando o link da empresa não existir.
        "empresa": texto(card.select_one("a[href*='/empresa-']"), "Não informada"),
        # Local extraído; usa "Não informado" quando o campo estiver vazio.
        "local": local or "Não informado",
        # Salário extraído; usa "Não informado" quando o campo estiver vazio.
        "salario": salario or "Não informado",
        # URL completa da vaga.
        "link": link,
        # Descrição extraída; usa "Não informada" quando o campo estiver vazio.
        "descricao": descricao or "Não informada",
    }


def coletar_html_com_scroll(url, lotes_alvo):
    # Cria um objeto para configurar o navegador Chrome.
    opts = Options()
    # Esta opção faria o Chrome funcionar sem abrir uma janela, se fosse ativada.
    # opts.add_argument("--headless=new")
    # Define o tamanho da janela para que a página carregue o layout esperado.
    opts.add_argument("--window-size=1200,900")
    # Abre o Chrome controlado pelo Selenium com as opções definidas acima.
    driver = webdriver.Chrome(options=opts)
    try:
        # Acessa a URL recebida como argumento.
        driver.get(url)
        # Aguarda o carregamento inicial da página.
        time.sleep(3)
        # Guarda a quantidade anterior de cards e quantas vezes ela permaneceu igual.
        qtd_anterior, estaveis = 0, 0
        # Permite no máximo três tentativas de rolagem para cada lote desejado.
        for i in range(lotes_alvo * 3):
            # Rola até o final da página para disparar o carregamento de mais vagas.
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Aguarda as novas vagas serem carregadas pelo site.
            time.sleep(2.5)

            # --- Contagem dos cards durante o scroll ---
            # Versão com SELETOR CSS (a que usávamos antes):
            # qtd = len(driver.find_elements("css selector", "div.card.js_rowCard"))

            # Procura no HTML todos os elementos <div> que possuem as classes
            # "card" e "js_rowCard". By.XPATH informa ao Selenium que o texto
            # seguinte deve ser interpretado como um seletor XPath. O método
            # find_elements retorna uma lista com os elementos encontrados, e
            # len() conta essa lista; por isso, qtd guarda o total de cards.
            qtd = len(driver.find_elements(
    By.XPATH,
    "//div[contains(concat(' ', normalize-space(@class), ' '), ' card ') "
    "and contains(concat(' ', normalize-space(@class), ' '), ' js_rowCard ')]"
))

            # Exibe no terminal a quantidade de vagas encontradas nesta rolagem.
            print(f"  scroll {i+1}: {qtd} vagas")
            # Se a quantidade não mudou, talvez não existam mais vagas para carregar.
            if qtd == qtd_anterior:
                # Conta quantas vezes seguidas a quantidade permaneceu igual.
                estaveis += 1
                # Encerra após duas tentativas sem novas vagas.
                if estaveis >= 2:
                    break
            else:
                # Zera a contagem porque novas vagas foram carregadas.
                estaveis = 0
            # Atualiza a quantidade anterior para comparar na próxima iteração.
            qtd_anterior = qtd
            # Encerra quando a quantidade desejada de vagas for atingida.
            if qtd >= lotes_alvo * 20:
                break
        # Devolve o HTML completo da página depois das rolagens.
        return driver.page_source
    finally:
        # Fecha o navegador mesmo se ocorrer algum erro durante a coleta.
        driver.quit()


def proximo_numero_arquivo():
    # Começa pelo sufixo _1 e aumenta até encontrar um par de nomes disponível.
    numero = 1
    while (os.path.exists(f"vagas_infojobs_{numero}.csv")
           or os.path.exists(f"vagas_infojobs_{numero}.json")):
        numero += 1
    return numero


def main():
    # Informa ao usuário que a coleta começou.
    print("Coletando com scroll...")
    # Abre a página, faz as rolagens e recebe o HTML final.
    html = coletar_html_com_scroll(URL, LOTES_ALVO)

    # Analisa o HTML usando o parser html.parser do BeautifulSoup.
    soup = BeautifulSoup(html, "html.parser")
    # Seleciona todos os cards que representam vagas na página.
    cards = soup.select("div.card.js_rowCard")
    # Exibe quantos cards foram encontrados no HTML.
    print(f"Cards no HTML: {len(cards)}")

    # Cria um conjunto para controlar links que já foram processados.
    vistos = set()
    # Cria a lista que armazenará somente as vagas válidas e únicas.
    vagas = []
    # Percorre cada card encontrado na página.
    for card in cards:
        # Extrai os campos da vaga atual e cria um dicionário com eles.
        vaga = extrair_vaga(card)
        # Ignora cards sem link ou sem título, pois provavelmente estão incompletos.
        if not vaga["link"] or not vaga["titulo"]:
            continue
        # Ignora a vaga se o mesmo link já tiver sido adicionado.
        if vaga["link"] in vistos:
            continue
        # Registra o link como já visto.
        vistos.add(vaga["link"])
        # Adiciona a vaga válida e única à lista final.
        vagas.append(vaga)

    # Mostra a quantidade de vagas depois da remoção de duplicatas.
    print(f"Vagas únicas após dedup: {len(vagas)}")

    # Conta vagas com salário diferente de "A combinar" e "Não informado".
    com_salario = sum(1 for v in vagas if v["salario"] != "A combinar"
                      and v["salario"] != "Não informado")
    # Exibe o total de vagas que informaram uma faixa salarial.
    print(f"Vagas com faixa salarial informada: {com_salario}")

    # Define a ordem das colunas no arquivo CSV.
    campos = ["titulo", "empresa", "local", "salario", "link", "descricao"]
    # Escolhe um número que ainda não foi usado para não sobrescrever resultados.
    numero_arquivo = proximo_numero_arquivo()
    nome_csv = f"vagas_infojobs_{numero_arquivo}.csv"
    nome_json = f"vagas_infojobs_{numero_arquivo}.json"
    # Abre ou cria o CSV para escrita usando UTF-8 com marca compatível com Excel.
    with open(nome_csv, "w", newline="", encoding="utf-8-sig") as f:
        # Cria um escritor que transforma dicionários em linhas do CSV.
        writer = csv.DictWriter(f, fieldnames=campos)
        # Escreve a primeira linha com os nomes das colunas.
        writer.writeheader()
        # Escreve uma linha para cada vaga coletada.
        writer.writerows(vagas)

    # Abre ou cria o arquivo JSON para escrita usando UTF-8.
    with open(nome_json, "w", encoding="utf-8") as f:
        # Salva a lista de vagas no JSON, preservando acentos e usando indentação.
        json.dump(vagas, f, ensure_ascii=False, indent=2)

    # Confirma no terminal que os dois arquivos foram gerados.
    print(f"\nArquivos gerados: {nome_csv} e {nome_json}")


# Executa a função principal somente quando este arquivo é executado diretamente.
if __name__ == "__main__":
    main()