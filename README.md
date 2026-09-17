# 🔎 Web Scraper de Vagas — InfoJobs

Coletor de vagas de emprego do portal [InfoJobs](https://www.infojobs.com.br) que busca anúncios por cargo/localidade, extrai os dados de cada vaga e exporta o resultado em **CSV** e **JSON**.

Desenvolvido como Laboratório 1 da disciplina **Coleta, Preparação e Análise de Dados** (PUCRS). Exemplo de coleta configurado: vagas de **Desenvolvedor** em **Porto Alegre – RS**.

> ⚙️ Stack: **Python · Selenium · BeautifulSoup**

---

## ✨ O que ele faz

- Acessa a busca do InfoJobs e navega pelos resultados carregados dinamicamente (**scroll infinito**);
- Extrai de cada vaga: **título, empresa, local, faixa salarial, link e descrição**;
- Remove **duplicatas** e trata **campos ausentes** (vagas confidenciais, salário "A combinar" etc.);
- Exporta um arquivo único em **CSV** e **JSON**.

## 🛠️ Tecnologias

| Ferramenta | Papel |
|---|---|
| **Selenium** | Abre um navegador real (Chrome), acessa a busca e rola a página para carregar todas as vagas |
| **BeautifulSoup** | Faz o parsing do HTML e extrai os campos de cada vaga |
| **Biblioteca padrão** | `re` (normalização de texto), `csv`/`json` (exportação), `urllib.parse` (URLs absolutas) |

## 📋 Pré-requisitos

- **Python 3.10+**
- **Google Chrome** instalado (o Selenium 4.6+ baixa o ChromeDriver automaticamente via Selenium Manager — não é preciso instalar o driver manualmente)

## 🚀 Instalação

```bash
# clonar o repositório
git clone https://github.com/<seu-usuario>/t1-coleta.git
cd t1-coleta

# criar e ativar o ambiente virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# instalar as dependências
pip install -r requirements.txt
```

Caso não haja um `requirements.txt`, instale diretamente:

```bash
pip install selenium beautifulsoup4
```

## ▶️ Como executar

```bash
python scraper.py
```

O script abre uma janela do Chrome, faz a busca, rola a página até carregar todas as vagas e gera os arquivos de saída. Para rodar **sem abrir a janela** (modo headless), descomente esta linha em `scraper.py`:

```python
# opts.add_argument("--headless=new")
```

### Alterar o cargo ou a cidade

Basta trocar a URL de busca no topo do arquivo:

```python
URL = f"{BASE}/vagas-de-emprego-desenvolvedor-em-porto-alegre,-rs.aspx"
```

## 📦 Saída

Dois arquivos são gerados na raiz do projeto:

- `vagas_infojobs.csv` (codificação `utf-8-sig`, abre com acentos corretos no Excel)
- `vagas_infojobs.json` (`ensure_ascii=False`, indentado)

Cada vaga contém os campos:

| Campo | Descrição |
|---|---|
| `titulo` | Título da vaga |
| `empresa` | Nome da empresa (`"Não informada"` em vagas confidenciais) |
| `local` | Cidade – UF |
| `salario` | Faixa salarial (`"A combinar"` quando não divulgada) |
| `link` | URL completa da vaga |
| `descricao` | Resumo da vaga |

## 🧠 Como funciona

O InfoJobs carrega as vagas por **scroll infinito** (via JavaScript), sem paginação por URL — então `requests` sozinho enxergaria apenas o primeiro lote. Por isso a abordagem é **híbrida**:

1. O **Selenium** abre o Chrome, acessa a busca e rola a página repetidamente, carregando lotes sucessivos de vagas até o total estabilizar;
2. O HTML resultante (`driver.page_source`) é entregue ao **BeautifulSoup**, que extrai os campos de cada card;
3. As vagas são deduplicadas pelo **link** (identificador único) e os campos ausentes recebem valores padrão;
4. O resultado é exportado em CSV e JSON.

### Métodos de busca utilizados

- **Seletores CSS** (BeautifulSoup) — localizam cada campo dentro do card (ex.: `h2.js_vacancyTitle`, `a[href*='/empresa-']`);
- **XPath** (Selenium) — conta os cards a cada rolagem para detectar quando o carregamento termina;
- **Expressões regulares** (`re`) — normalizam espaços e quebras de linha no texto extraído.

## ⚖️ Considerações éticas

- O `robots.txt` do InfoJobs foi verificado: as páginas de busca e de vaga são permitidas; áreas de sistema e endpoints `.ashx` são bloqueados e **não são acessados**;
- **Nenhuma coleta é feita via API** — apenas leitura do HTML renderizado;
- Há uma pausa (`time.sleep`) entre as rolagens para não sobrecarregar o servidor.

## 📁 Estrutura do projeto

```
t1-coleta/
├── scraper.py              # código-fonte do coletor
├── requirements.txt        # dependências
├── vagas_infojobs.csv      # dados coletados (CSV)
├── vagas_infojobs.json     # dados coletados (JSON)
├── relatorio.pdf           # relatório de desenvolvimento
└── README.md
```

## 🎓 Contexto acadêmico

Projeto desenvolvido para a disciplina de Coleta, Preparação e Análise de Dados (PUCRS).
