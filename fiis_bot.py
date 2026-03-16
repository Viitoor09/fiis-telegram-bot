import os
import sqlite3
import telebot
import matplotlib.pyplot as plt
import io
import yfinance as yf
from telebot import types
from dotenv import load_dotenv

load_dotenv()
CHAVE_API = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(CHAVE_API)

def configurar_comandos():
    comandos = [
        types.BotCommand("start", "Reiniciar o bot e ver o menu"),
        types.BotCommand("ajuda", "Como usar o bot"),
        types.BotCommand("comprar", "Adicionar FII (Ex: /comprar MXRF11 10 9.80)"),
        types.BotCommand("remover", "Remover um ativo da carteira"),
        types.BotCommand("carteira", "Ver seu patrimônio e dividendos")
    ]
    bot.set_my_commands(comandos)

configurar_comandos()

conexao = sqlite3.connect('carteira_fiis.db', check_same_thread=False)
cursor = conexao.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS carteira (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        ticker TEXT,
        quantidade INTEGER,
        preco_medio REAL,
        UNIQUE(usuario_id, ticker)
    )
''')
conexao.commit()

def gerar_grafico_carteira(ativos_processados):
    labels = [item['ticker'] for item in ativos_processados]
    valores = [item['valor_total'] for item in ativos_processados]
    
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        valores, 
        labels=labels, 
        autopct='%1.1f%%', 
        startangle=140, 
        colors=plt.cm.Paired.colors
    )
    
    ax.set_title("Distribuição da Carteira")
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.close() 
    return img_buffer

def buscar_ultimo_dividendo(ticker_sa):
    try:
        fundo = yf.Ticker(ticker_sa)
        dividendos = fundo.dividends
        if not dividendos.empty:
            return dividendos.iloc[-1]
        return 0.0
    except:
        return 0.0


def consultar_fii_profissional(ticker):
    if ticker.startswith('/'):
        return "❌ Comando inválido para pesquisa. Escolha uma opção do menu."
    try:
        ticker = ticker.upper().strip()
        ticker_sa = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
        
        fundo = yf.Ticker(ticker_sa)
        info = fundo.info

        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info:
            return f"❌ Erro: O fundo '{ticker}' não foi encontrado ou não tem dados na B3."
        
        preco = info.get('currentPrice') or info.get('regularMarketPrice')
        preco_texto = f"R$ {preco:.2f}" if preco is not None else "Não disponível"

        pvp = info.get('priceToBook')
        if pvp is not None:
            if pvp < 1: status_pvp = "🟢 Descontado (barato)"
            elif pvp > 1.05: status_pvp = "🔴 Caro (Acima do patrimonial)"
            else: status_pvp = "🟡 No preço justo"
            pvp_texto = f"{pvp:.2f} ({status_pvp})"
        else:
            pvp_texto = "Não disponível"

        ultimo_pago = buscar_ultimo_dividendo(ticker_sa)
        
        dy = info.get('dividendYield')
        dy_formatado = "Não informado"

        if dy:
            dy_real = dy if dy > 1 else dy * 100
            if dy_real > 30:
                dy_formatado = "Dado instável no Yahoo"
            else:
                dy_formatado = f"{dy_real:.2f}%"
        
        return (
            f"--- 📊 RELATÓRIO: {ticker} ---\n"
            f"💰 Preço Atual: {preco_texto}\n"
            f"📉 P/VP: {pvp_texto}\n"
            f"💸 Dividend Yield: {dy_formatado}\n"
            f"🪙 Último Provento: R$ {ultimo_pago:.2f}\n"
            f"----------------------------"
        )
    
    except Exception as e: 
        return f"⚠️ Erro ao processar {ticker}: {e}"
    
def simulador_investimento(ticker, valor_investido):
    try:
        ticker = ticker.upper().strip()
        ticker_sa = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker

        fundo = yf.Ticker(ticker_sa)
        preco_atual = fundo.info.get('currentPrice') or fundo.info.get('regularMarketPrice')
        ultimo_pago = buscar_ultimo_dividendo(ticker_sa)

        if not preco_atual or preco_atual == 0:
            return "❌ Não foi possível obter o preço para simulação."
        qtd_cotas = int(valor_investido // preco_atual)
        total_gastos = qtd_cotas * preco_atual
        rendimento_mensal = qtd_cotas * ultimo_pago

        return (
            f"--- 🧮 SIMULAÇÃO: {ticker} ---\n"
            f"💵 Investimento: R$ {valor_investido:.2f}\n"
            f"🧱 Cotas compradas: {qtd_cotas}\n"
            f"💰 Total a pagar: R$ {total_gastos:.2f}\n"
            f"💸 Salário mensal estimado: R$ {rendimento_mensal:.2f}\n"
            f"----------------------------"
        )
    except:
        return "⚠️ Erro ao simular. Verifique o ticker e o valor"
    
@bot.message_handler(commands=["start"])
def boas_vindas(mensagem):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('🔍 Consultar FII'), types.KeyboardButton('🧮 Simular'), types.KeyboardButton('💼 Minha Carteira'))
    bot.send_message(mensagem.chat.id, f"Olá {mensagem.from_user.first_name}! Escolha uma opção:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🔍 Consultar FII')
def pedir_ticker(mensagem):
    msg = bot.send_message(mensagem.chat.id, "Digite o código (ex: MXRF11):")
    bot.register_next_step_handler(msg, processar_consulta)

def processar_consulta(mensagem):
    resultado = consultar_fii_profissional(mensagem.text)
    bot.send_message(mensagem.chat.id, resultado)

@bot.message_handler(func=lambda m: m.text == '🧮 Simular')
def pedir_simulacao(mensagem):
    msg = bot.send_message(mensagem.chat.id, "Digite o FII e o VALOR (ex: MXRF11 1000):")
    bot.register_next_step_handler(msg, processar_simulacao)

def processar_simulacao(mensagem):
    try:
        partes = mensagem.text.split()
        res = simulador_investimento(partes[0], float(partes[1].replace(',','.')))
        bot.send_message(mensagem.chat.id, res)
    except:
        bot.send_message(mensagem.chat.id, "❌ Use: TICKER VALOR (ex:MXRF11 500)")

@bot.message_handler(commands=["comprar"])
def registrar_compra(mensagem):
    try:
        dados = mensagem.text.split()
        if len(dados) != 4:
            bot.reply_to(mensagem, "❌ Use: /comprar TICKER QTD PRECO")
            return
            
        ticker = dados[1].upper().strip()
        nova_qtd = int(dados[2])
        novo_preco = float(dados[3].replace(',', '.'))
        user_id = mensagem.from_user.id

        ticker_sa = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
        fundo = yf.Ticker(ticker_sa)
        if not fundo.info or ('regularMarketPrice' not in fundo.info):
            bot.reply_to(mensagem, f"🚫 Ticker {ticker} inválido.")
            return

        cursor.execute('SELECT quantidade, preco_medio FROM carteira WHERE usuario_id = ? AND ticker = ?', (user_id, ticker))
        resultado = cursor.fetchone()

        if resultado:
            qtd_antiga, preco_antigo = resultado
            
            qtd_total = qtd_antiga + nova_qtd
            novo_preco_medio = ((qtd_antiga * preco_antigo) + (nova_qtd * novo_preco)) / qtd_total
            
            cursor.execute('''
                UPDATE carteira SET quantidade = ?, preco_medio = ?
                WHERE usuario_id = ? AND ticker = ?
            ''', (qtd_total, novo_preco_medio, user_id, ticker))
            msg_sucesso = f"✅ Carteira Atualizada!\nAgora você tem {qtd_total} cotas de {ticker} com preço médio de R$ {novo_preco_medio:.2f}"
        else:
            cursor.execute('''
                INSERT INTO carteira (usuario_id, ticker, quantidade, preco_medio)
                VALUES (?, ?, ?, ?)
            ''', (user_id, ticker, nova_qtd, novo_preco))
            msg_sucesso = f"✅ {ticker} adicionado com sucesso!"

        conexao.commit()
        bot.reply_to(mensagem, msg_sucesso)

    except Exception as e:
        bot.reply_to(mensagem, f"⚠️ Erro: {e}")

@bot.message_handler(func=lambda m: m.text == '💼 Minha Carteira')
def ver_carteira(mensagem):
    user_id = mensagem.from_user.id
    cursor.execute('SELECT ticker, quantidade, preco_medio FROM carteira WHERE usuario_id = ?', (user_id,))
    ativos = cursor.fetchall()

    if not ativos:
        bot.send_message(mensagem.chat.id, "Sua carteira está vazia! Use /comprar para adicionar.")
        return
    
    bot.send_chat_action(mensagem.chat.id, 'upload_photo')
    
    texto = "--- 💼 SUA CARTEIRA ---\n\n"
    total_proventos = 0
    total_patrimonio = 0
    dados_grafico = []

    for ticker, qtd, preco_med in ativos:
        try:
            ticker_sa = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
            f = yf.Ticker(ticker_sa)
            
            info = f.info
            preco_atual = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if preco_atual is None:
                texto += f"⚠️ {ticker}: Erro ao buscar dados atuais.\n----------------------\n"
                continue

            total_pago = qtd * preco_med
            valor_hoje = qtd * preco_atual
            lucro = valor_hoje - total_pago
            
            total_patrimonio += valor_hoje
            dados_grafico.append({'ticker': ticker, 'valor_total': valor_hoje})

            ultimo_div = buscar_ultimo_dividendo(ticker_sa)
            recebido_neste_fii = qtd * ultimo_div
            total_proventos += recebido_neste_fii

            texto += f"📌 {ticker}: {qtd} cotas\n"
            texto += f"Custo: R$ {preco_med:.2f} | Atual: R$ {preco_atual:.2f}\n"
            texto += f"Resultado: R$ {lucro:.2f}\n"
            texto += f"💰 Provento Estimado: R$ {recebido_neste_fii:.2f}\n"
            texto += "----------------------\n"
            
        except Exception as e:
            print(f"Erro ao processar {ticker}: {e}")
            texto += f"❌ {ticker}: Erro técnico.\n----------------------\n"

    texto += f"\n📊 **Patrimônio Total: R$ {total_patrimonio:.2f}**"
    texto += f"\n💵 **Total de Dividendos/Mês: R$ {total_proventos:.2f}**"
    
    try:
        foto_grafico = gerar_grafico_carteira(dados_grafico)
        bot.send_photo(mensagem.chat.id, foto_grafico, caption=texto, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(mensagem.chat.id, texto, parse_mode="Markdown")
        print(f"Erro ao gerar gráfico: {e}")

@bot.message_handler(commands=["remover", "vender"])
def selecionar_remocao(mensagem):
    user_id = mensagem.from_user.id
    
    cursor.execute('SELECT ticker FROM carteira WHERE usuario_id = ?', (user_id,))
    ativos = cursor.fetchall()
    
    if not ativos:
        bot.reply_to(mensagem, "Sua carteira está vazia.")
        return

    markup = types.InlineKeyboardMarkup()
    for item in ativos:
        ticker = item[0]
        botao = types.InlineKeyboardButton(text=f"❌ {ticker}", callback_data=f"del_{ticker}")
        markup.add(botao)
        
    bot.send_message(mensagem.chat.id, "Escolha o que deseja remover ou vender:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_"))
def confirmar_remocao(call):
    user_id = call.from_user.id
    ticker = call.data.split("_")[1]
    
    try:
        cursor.execute('DELETE FROM carteira WHERE usuario_id = ? AND ticker = ?', (user_id, ticker))
        conexao.commit()
        
        bot.edit_message_text(f"✅ O ativo {ticker} foi removido com sucesso!", 
                              call.message.chat.id, 
                              call.message.message_id)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"⚠️ Erro: {e}")

@bot.message_handler(commands=["ajuda"])
def comando_ajuda(mensagem):
    texto_ajuda = (
        "✨ **Bem-vindo ao Menu de Ajuda do FiisBot!** ✨\n\n"
        "Aqui estão os comandos que você pode usar para gerir seus investimentos:\n\n"
        "🔍 **CONSULTAS E SIMULAÇÕES**\n"
        "• Clique em `🔍 Consultar FII` para ver o preço atual, P/VP e Dividend Yield de qualquer fundo.\n"
        "• Clique em `🧮 Simular` para descobrir quanto você ganharia investindo um valor específico em um FII.\n\n"
        "💼 **GESTÃO DE CARTEIRA**\n"
        "• `/comprar TICKER QTD PRECO` -> Adiciona um FII à sua carteira. Se você já tiver o ativo, eu calculo o novo **Preço Médio** automaticamente!\n"
        "  _Exemplo: /comprar MXRF11 10 9.80_\n\n"
        "• `/remover` -> Abre um menu com botões para você escolher qual ativo deseja excluir da sua lista.\n\n"
        "• `💼 Minha Carteira` -> Mostra seu patrimônio total, lucro/prejuízo de cada ativo e o seu **salário mensal estimado** em dividendos.\n\n"
        "--- \n"
        "💡 *Dica:* Use sempre o código do fundo com os números (ex: HGLG11). O bot consulta dados em tempo real da B3!"
    )
    
    bot.send_message(mensagem.chat.id, texto_ajuda, parse_mode="Markdown")

print("🚀 FiisBot Online!")
bot.polling()