# 📊 FiisBot - Gestor de Carteira de Fundos Imobiliários

O **FiisBot** é um bot do Telegram desenvolvido para facilitar o acompanhamento de investimentos em Fundos Imobiliários (FIIs). Ele permite consultar dados em tempo real da B3, simular investimentos e gerenciar uma carteira pessoal com cálculos automáticos de preço médio e dividendos.

---

## 🚀 Funcionalidades

- **🔍 Consulta Profissional:** Preço atual, P/VP (com indicação de barato/caro) e Dividend Yield.
- **🧮 Simulação Inteligente:** Cálculo de quantas cotas comprar com determinado valor e projeção de rendimento mensal.
- **💼 Gestão de Carteira:** - Adição de ativos com cálculo automático de **Preço Médio**.
  - Visualização de patrimônio total e lucro/prejuízo por ativo.
  - Estimativa de "Salário Mensal" (dividendos total/mês).
- **📈 Gráficos Dinâmicos:** Geração de gráfico de pizza mostrando a diversificação do patrimônio.
- **🗑️ Remoção Ágil:** Menu interativo para remover ativos da carteira.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.x
- **API do Telegram:** `pyTelegramBotAPI`
- **Dados Financeiros:** `yfinance` (Yahoo Finance)
- **Banco de Dados:** `SQLite3` (Persistência de dados local)
- **Visualização de Dados:** `Matplotlib` (Geração de gráficos)
- **Variáveis de Ambiente:** `python-dotenv` (Segurança de chaves API)

---

## 📦 Como rodar o projeto localmente

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/Viitoor09/fiis-telegram-bot.git](https://github.com/Viitoor09/fiis-telegram-bot.git)