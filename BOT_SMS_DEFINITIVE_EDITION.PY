from datetime import datetime, timedelta, timezone
from io import BytesIO
import io
import json
import time
import matplotlib.pyplot as plt
import qrcode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, CallbackContext,  MessageHandler, filters, ConversationHandler
import requests
import mercadopago
import asyncio
import sqlite3
import pandas as pd


MEU_SMS_ACTIVATE_API_KEY = '3924d657fb95cebf09d6d5704A190eb2'
TELEGRAM_BOT_TOKEN = '7894225433:AAEknYuQrHlFuXj_E5oR12g_DUbO_q8hwH8'
MP_ACCESS_TOKEN = 'APP_USR-3659660205672870-103020-e757331755777413d8214c1a1f9c11ce-1990304411'


# Inicializa o cliente do Mercado Pago
sdk = mercadopago.SDK(MP_ACESS_TOKEN)

user_payments = {}

service_prices = {
    'ig': {'br': 5, 'us': 4, 'cn': 4, 'en': 4, 'fr': 4},  # Instagram
    'tg': {'br': 13, 'us': 8, 'cn': 6, 'en': 9, 'fr': 16},  # Telegram
    'wa': {'br': 12, 'us': 12, 'cn': 6, 'en': 11, 'fr': 16},   # WhatsApp
    'ds': {'br': 5, 'us': 4, 'cn': 4, 'en': 4, 'fr': 4},  # Discord
    'fb': {'br': 5, 'us': 5, 'cn': 4, 'en': 4, 'fr': 4},  # Facebook
    'ub': {'br': 5, 'us': 5, 'cn': 4, 'en': 4, 'fr': 5},    # Uber
    'go': {'br': 5, 'us': 4, 'cn': 4, 'en': 6, 'fr': 6},  # Google/YouTube
    'rl': {'br': 5, 'us': 12, 'cn': 4, 'en': 4, 'fr': 4},   # inDrive
    'ki': {'br': 5, 'us': 4, 'cn': 5, 'en': 4, 'fr': 4}    # 99app
}


async def adicionar_saldo_via_comando(update: Update, context: CallbackContext):
    ADMIN_ID = {7450049318, 1500943516}  # IDs de administradores
    user_id = update.effective_user.id

    # Verifica se o usuário tem permissão para executar o comando
    if user_id not in ADMIN_ID:
        await update.message.reply_text("Você não tem permissão para acessar esta função.")
        return

    try:
        # Verifica se o comando foi passado com ambos os argumentos: ID do usuário e valor
        if len(context.args) < 2:
            await update.message.reply_text("Por favor, forneça o ID do usuário e o valor a ser adicionado. Exemplo: /adicionar_saldo 12345 50")
            return

        # Captura o ID do usuário e o valor a ser adicionado
        user_iddd = context.args[0]  # ID do usuário
        valor_adicional = float(context.args[1])  # Valor a ser adicionado (certifique-se de que é um número)

        # Validação do valor
        if valor_adicional <= 0:
            await update.message.reply_text("O valor a ser adicionado deve ser maior que zero.")
            return

        await update.message.reply_text(f"Adicionando {valor_adicional} ao saldo do usuário {user_iddd}...")

        # Conexão com o banco de dados (substitua pela sua função real)
        conexao = await conexao_banco()  # Esta função deve retornar uma conexão com o banco de dados
        cursor = conexao.cursor()

        # Tenta realizar a atualização no banco de dados
        cursor.execute('''SELECT saldo FROM usuarios WHERE user_id = ?''', (user_iddd,))
        resultado = cursor.fetchone()

        if resultado:
            # Se o usuário existir, adicione o valor ao saldo atual
            saldo_atual = resultado[0]
            novo_saldo = saldo_atual + valor_adicional

            # Atualiza o saldo no banco de dados
            cursor.execute('''UPDATE usuarios SET saldo = ? WHERE user_id = ?''', (novo_saldo, user_iddd))
            conexao.commit()

            await update.message.reply_text(f"Saldo do usuário {user_iddd} atualizado com sucesso! Novo saldo: {novo_saldo}. Rode /saldo para checar")
        else:
            await update.message.reply_text(f"Usuário {user_iddd} não encontrado no banco de dados.")

        # Fecha a conexão
        conexao.close()

    except ValueError:
        await update.message.reply_text("Por favor, forneça um valor numérico válido para o valor a ser adicionado.")
        
    except Exception as e:
        await update.message.reply_text(f"Erro ao tentar adicionar saldo ao usuário: {e}")
        

async def conexao_banco():
    conexao = sqlite3.connect('bot_sms.db')
    return conexao


async def zerar_saldo(update: Update, context: CallbackContext):
    ADMIN_ID = {7450049318, 1500943516}
    user_id = update.effective_user.id
    # if user_id != ADMIN_ID:
    if user_id not in ADMIN_ID:
        await update.message.reply_text("Você não tem permissão para acessar esta função.")
        return
    try:
        # A partir do comando /zerar_saldo <user_id>
        if len(context.args) == 0:
            await update.message.reply_text("Por favor, forneça o ID do usuário. Exemplo: /zerar_saldo 12345")
            return

        user_iddd = context.args[0]  # Captura o primeiro argumento como o ID do usuário
        await update.message.reply_text(f"Zerando saldo para o usuário: {user_iddd}...")

        # Conexão com o banco de dados (substitua pela sua função real)
        conexao = await conexao_banco()
        cursor = conexao.cursor()
        
        # Tenta realizar a atualização no banco
        cursor.execute('''
        UPDATE usuarios SET saldo = 0 where user_id = ?
     ''',(user_iddd,))
        print("Conexão estabelecida com sucesso!")
        conexao.commit()

        # await update.message.reply_text(f"Saldo do usuário {user_iddd} zerado com sucesso!")
        await update.message.reply_text(f"Saldo do usuário: {user_iddd} zerado com sucesso! Rode o comando /saldo para checar!")
        cursor.execute('''
        SELECT saldo FROM usuarios where user_id = ?
     ''',(user_iddd,))
        result = cursor.fetchone()
        print(result)
        conexao.close()

    except Exception as e:
        await update.message.reply_text(f"Erro ao tentar zerar o saldo do usuário: {e}")




async def registrar_pagamento(user_id, valor, nome):
    conexao = await conexao_banco()  # Certifique-se de que a conexão seja awaitable
    cursor = conexao.cursor()
    try:
       
        cursor.execute('''
        INSERT INTO usuarios 
        (user_id, saldo, nome) VALUES (?, ?, ?) 
        ON CONFLICT (user_id) DO UPDATE SET saldo = usuarios.saldo + ?, nome = ?
        ''', (user_id, valor, nome, valor, nome))
        # ON CONFLICT (user_id) DO UPDATE SET saldo = ROUND(usuarios.saldo + ?, 2), nome = ?         

        # Registra a transação
        cursor.execute('''
            INSERT INTO transacoes
            (user_id, valor, tipo) VALUES (?, ?, 'Pagamento')
        ''', (user_id, valor))

        conexao.commit()
        print(f"Pagamento de R${valor} registrado e saldo atualizado para o usuário {user_id}.")
    except Exception as e:
        print(f"Erro ao registrar o pagamento: {e}")
    finally:
        conexao.close()  # Não esqueça de fechar a conexão

async def valor_digitado(update: Update, context: CallbackContext):
    if update.callback_query:
        # Se for uma callback_query, responde no contexto da interação
        await update.callback_query.message.reply_text("Digite o valor da Recarga: R$ ")
    else:
        # Se não for uma callback_query (por exemplo, uma mensagem normal de comando),
        # responde com uma mensagem direta.
        await update.message.reply_text("Digite o valor da Recarga: R$ ")
    # await update.callback_query.message.reply_text("Digite o valor da Recarga: R$ ")

async def message_handler(update:Update, context:CallbackContext):
    valor = float(update.message.text)
    await pay(update, context, valor)

async def consultar_saldo(user_id, context, update: Update):
    if update.callback_query:
        # Se for uma callback_query, responde no contexto da interação
        await update.callback_query.message.reply_text("Consultando seu saldo...")
    else:
        # Se não for uma callback_query (por exemplo, uma mensagem normal de comando),
        # responde com uma mensagem direta.
        await update.message.reply_text("Consultando seu saldo...")
    # await update.callback_query.message.reply_text("Consultando seu saldo...")
    conexao = await conexao_banco()  # Use await para a conexão assíncrona
    cursor = conexao.cursor()
    try:
        cursor.execute('''SELECT saldo FROM usuarios WHERE user_id = ?''', (user_id,))
        resultado = cursor.fetchone()

        if resultado is not None:
            saldo = resultado[0]
        else:
            saldo = 0.0

        await context.bot.send_message(chat_id=user_id, text=f"SEU SALDO ATUAL É DE R${saldo:.2f}!")
        
    except Exception as e:
        print(f"ERRO AO CONSULTAR O SALDO: {e}")
        await context.bot.send_message(chat_id=user_id, text="Erro ao consultar saldo.")

    finally:
        conexao.close()  # Fecha a conexão


async def imprimir_dados_no_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = {7450049318, 1500943516}
    user_id = update.effective_user.id
    # if user_id != ADMIN_ID:
    if user_id not in ADMIN_ID:
        await update.message.reply_text("Você não tem permissão para acessar esta função.")
        return
    
    await update.message.reply_text("Consultando o banco de dados...")
    conexao = sqlite3.connect('bot_sms.db')
    cursor = conexao.cursor()
    
    try:
        # Obtém a lista de tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = cursor.fetchall()

        if not tabelas:
            await update.message.reply_text("Nenhuma tabela encontrada no banco de dados.")
            return

        for (tabela,) in tabelas:
            # Obtém os dados da tabela
            cursor.execute(f"SELECT * FROM {tabela};")
            dados = cursor.fetchall()

            if dados:
                # Obtém os nomes das colunas
                colunas = [descricao[0] for descricao in cursor.description]
                df = pd.DataFrame(dados, columns=colunas)

                # Cria uma tabela e salva como imagem
                fig, ax = plt.subplots(figsize=(10, len(df) * 0.5))  # Ajusta o tamanho da figura

                # Estilização
                ax.axis('tight')
                ax.axis('off')

                # Título
                plt.title(f'Tabela: {tabela}', fontsize=14, fontweight='bold', color='#0088cc')  # Cor do Telegram

                # Cria a tabela
                table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1.2, 1.2)

                # Estilizando as cores da tabela
                for (i, j), cell in table.get_celld().items():
                    if i == 0:  # Cabeçalho
                        cell.set_text_props(fontweight='bold', color='white')
                        cell.set_facecolor('#0088cc')  # Cor do Telegram
                    else:
                        cell.set_facecolor('#e8f8fa') if j % 2 == 0 else cell.set_facecolor('white')

                # Salva a tabela como imagem
                plt.savefig('tabela.png', bbox_inches='tight', dpi=300)
                plt.close()

                # Envia a imagem no bot
                with open('tabela.png', 'rb') as f:
                    await update.message.reply_photo(photo=f)
            else:
                await update.message.reply_text(f"Tabela: {tabela} - Nenhum dado encontrado.")

    except Exception as e:
        await update.message.reply_text(f"Erro ao acessar o banco de dados: {e}")
    finally:
        conexao.close()
     

async def rent_number(update: Update, context: ContextTypes.DEFAULT_TYPE, service: str, number_type: str):
    user_id = update.effective_user.id
    # service_price = prices.get(service, 0)
    # Obter o preço do número baseado no tipo (br ou foreign)
    if service in service_prices and number_type in service_prices[service]:
        price = service_prices[service][number_type]
    else:
        await update.callback_query.message.reply_text("Erro: Tipo de número ou serviço inválido.")
        return

    # Consulta o saldo do usuário no banco de dados
    conexao = await conexao_banco()
    cursor = conexao.cursor()
    cursor.execute('SELECT saldo FROM usuarios WHERE user_id = ?', (user_id,))
    resultado = cursor.fetchone()
    
    if resultado is not None:
        saldo = resultado[0]
    else:
        saldo = 0.0

    if saldo < price:
        # await update.callback_query.message.reply_text('Saldo insuficiente para alugar este número. Por favor, recarregue seu saldo via PIX.')
        conexao.close()
        main_keyboard = [
       
        [
            InlineKeyboardButton("Recarregar saldo", callback_data='pix'),
        ]
        
        ] 

        # Criar o teclado com todas as opções
        main_reply_markup = InlineKeyboardMarkup(main_keyboard)

        # Enviar mensagem com opções do menu principal
        
        await update.callback_query.message.reply_text(text='Saldo insuficiente para alugar este número. Por favor, recarregue seu saldo via PIX.', reply_markup=main_reply_markup)
        return

    conexao.close()  # Fecha a conexão após verificar o saldo

    # Verifica o saldo na API do sms-activate
    balance_response = requests.get(f'https://sms-activate.org/stubs/handler_api.php?api_key={VINICIUS_SMS_ACTIVATE_API_KEY}&action=getBalance')
    if balance_response.status_code == 200:
        balance = float(balance_response.text.split(':')[1])
        if balance <= 0:
            await update.callback_query.message.reply_text('Saldo insuficiente na API. Tente novamente mais tarde.')
            return

    # Solicita o número
    params = {
        'api_key': SMS_ACTIVATE_API_KEY,
        'action': 'getNumber',
        'service': service,
        'country': 0 # 0 é para aluguel global
    }
    if number_type == 'br':
        params['country'] = 73  # Para números brasileiros
    elif number_type == 'us':
        params['country'] = 187
    elif number_type == 'cn':
        params['country'] = 36
    elif number_type == 'en':
        params['country'] = 16
    elif number_type == 'fr':
        params['country'] = 78    # Para números estrangeiros
    response = requests.get('https://sms-activate.org/stubs/handler_api.php', params=params)
    if 'ACCESS_NUMBER' in response.text:
        _, id_activation, number = response.text.split(':')
        if number_type == 'br':
            await update.callback_query.message.reply_text(f'Número alugado com o código do país: +{number}')
            await update.callback_query.message.reply_text(f'Número alugado sem o código do país: {number[2:].strip()}')
        elif number_type == 'us':
            await update.callback_query.message.reply_text(f'Número alugado com o código do país: +{number}')
            await update.callback_query.message.reply_text(f'Número alugado sem o código do país: {number[1:].strip()}')
        elif number_type == 'cn':
            await update.callback_query.message.reply_text(f'Número alugado com o código do país: +{number}')
            await update.callback_query.message.reply_text(f'Número alugado sem o código do país: {number[1:].strip()}')
        elif number_type =='en':
            await update.callback_query.message.reply_text(f'Número alugado com o código do país: +{number}')
            await update.callback_query.message.reply_text(f'Número alugado sem o código do país: {number[2:].strip()}')
        elif number_type == 'fr':
            await update.callback_query.message.reply_text(f'Número alugado com o código do país: +{number}')
            await update.callback_query.message.reply_text(f'Número alugado sem o código do país: {number[2:].strip()}')
        await update.callback_query.message.reply_text('Aguardando SMS...')
        
        # Inicia o monitoramento do SMS com o id_activation (sem retornar ao usuário)
        asyncio.create_task(monitorar_sms(user_id, id_activation, context, update, price))
    else:
        await update.callback_query.message.reply_text('Erro ao alugar número: Não há números disponíveis para este país! Tente alugar um número de outro país.')


async def monitorar_sms(user_id, id_activation, context: ContextTypes.DEFAULT_TYPE, update: Update, price):
    while True:
        # Verifique se o SMS foi recebido
        response = requests.get(f'https://sms-activate.org/stubs/handler_api.php?api_key={VINICIUS_SMS_ACTIVATE_API_KEY}&action=getStatus&id={id_activation}')
        
        if 'STATUS_OK' in response.text:
            sms = response.text.split(':')[1]
            nome = update.effective_user.first_name
            await context.bot.send_message(chat_id=user_id, text=f'SMS recebido: {sms}')
            await registrar_pagamento(user_id, -price, nome) # Deduz o saldo
            break
        elif 'STATUS_WAIT_CODE' in response.text:
            # Aguardando o código, continue verificando
            await asyncio.sleep(2)  # Espera 10 segundos antes de verificar novamente
            print('Aguradando SMS...')
        else:
            # Se houver algum outro erro, pode ser interessante mostrar uma mensagem
            await context.bot.send_message(chat_id=user_id, text="Erro ao verificar SMS. Tente novamente mais tarde.")
            break

   

async def pay(update: Update, context: CallbackContext, valor) -> None:
    user_id = update.effective_user.id

    if user_id in user_payments and user_payments[user_id]["status"] != "approved":
        await update.message.reply_text("Você já tem um pagamento em andamento. Tente novamente mais tarde.")
        return
    
    await update.message.reply_text("Gerando pagamento...")

    # Data de expiração: 30 minutos a partir de agora em UTC-4
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=30)
    expiration_time_utc_minus_4 = expiration_time.astimezone(timezone(timedelta(hours=-4)))
    date_of_expiration = expiration_time_utc_minus_4.strftime("%Y-%m-%dT%H:%M:%S.000-04:00")

    # Dados do pagamento
    payment_data = {
        "transaction_amount": valor,  # Valor fixo para o exemplo
        "payment_method_id": "pix",
        "date_of_expiration": date_of_expiration,
        "payer": {
            "email": f"user{user_id}@example.com",  # Pode personalizar com o e-mail do usuário
        }
    }

    # Cria o pagamento
    payment_response = sdk.payment().create(payment_data)

    if payment_response['status'] == 400:
        await update.message.reply_text("Erro ao criar o pagamento.")
        return

    payment = payment_response["response"]
    resposta = json.dumps(payment, indent=4)
    payment_id = payment.get("id")
    print(payment_id)
    print(resposta)
    

    # Recupera o QR code
    qr_code = payment.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code")

    if qr_code:
        img = qrcode.make(qr_code)
        buf = io.BytesIO()
        img.save(buf)
        buf.seek(0)

        # Armazena informações do pagamento para o usuário
        user_payments[user_id] = {
            "date_of_expiration": date_of_expiration,
            "qr_code": qr_code,
            "id": payment_id,
            "status": "pending"
        }

        await context.bot.send_photo(chat_id=user_id, photo=buf)
        await update.message.reply_text(qr_code)
        
        asyncio.create_task(check_payment_status(user_id, payment_id, context,update))


    else:
        await update.callback_query.message.reply_text("QR code não encontrado na resposta.")

async def check_payment_status(user_id, payment_id, context, update):
    while True:
        # time.sleep(2)  # Verifica a cada 2 segundos
        await asyncio.sleep(2)
        payment_info = sdk.payment().get(payment_id)

        payment_status = payment_info['response']['status']
        print(payment_status)
        if payment_status == 'approved':
            print(payment_status)
            await context.bot.send_message(chat_id=user_id, text="PAGAMENTO APROVADO! ✅💰")
            services_button = InlineKeyboardButton("Mostrar Serviços", callback_data='show_services')
            reply_markup = InlineKeyboardMarkup([[services_button]])
            nome = update.effective_user.first_name
            valor_pago = payment_info['response']['transaction_amount']  # Valor pago
            await registrar_pagamento(user_id, valor_pago, nome)  # Registra o pagamento no banco de dados
            user_payments[user_id]["status"] = "approved"
            await context.bot.send_message(chat_id=user_id, text= 'Vejas as opçoes de serviços...',reply_markup=reply_markup)  # Atualiza o status para aprovado
            break
        elif payment_status == 'rejected':
            await context.bot.send_message(chat_id=user_id, text="PAGAMENTO REPROVADO! ❌")
            user_payments[user_id]["status"] = "rejected"  # Atualiza o status para reprovado
            break


async def get_services():
    response = requests.get(f'https://sms-activate.ru/stubs/handler_api.php?api_key={VINICIUS_SMS_ACTIVATE_API_KEY}&action=getServicesList')
    if response.status_code == 200:
        try:
            data = response.json()
            if data['status'] == 'success':
                services = data['services']
                # Filtrando serviços desejados
                filtered_services = [service for service in services if service['name'] in ['Instagram+Threads', 'Telegram', 'Whatsapp', 'Discord', 'facebook', 'Uber', 'Google,youtube,Gmail', 'inDriver', '99app']]
                return filtered_services
        except ValueError:
            print("Erro ao decodificar JSON:", response.text)
    return []


async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    services = await get_services()  # Obtém a lista de serviços

    # Botões para cada serviço
    services_keyboard = []
    for service in services:
        service_name = service['name']
        # print(service_name)
        service_code = service['code']
        button_text = f"{service_name}" 
        # - R${prices.get(service_code, 0):.2f}"
        services_keyboard.append([InlineKeyboardButton(button_text, callback_data=f"rent_{service_code}")])

    # Adiciona o botão de "Voltar"
    back_button = InlineKeyboardButton("Voltar", callback_data='back_to_main')

    # Configuração do teclado com a opção de serviços
    main_keyboard = [
        *services_keyboard, # Adiciona os botões de serviços
        [back_button]
    ]
    
    main_reply_markup = InlineKeyboardMarkup(main_keyboard)

    if update.callback_query:
        # Se for uma callback_query, responde no contexto da interação
        await update.callback_query.message.reply_text(
        'Escolha um serviço:',
        reply_markup=main_reply_markup
    )
    else:
        # Se não for uma callback_query (por exemplo, uma mensagem normal de comando),
        # responde com uma mensagem direta.
        await update.message.reply_text(
        'Escolha um serviço:',
        reply_markup=main_reply_markup
    )



async def show_service_options(update: Update, context: ContextTypes.DEFAULT_TYPE, service_name: str):
    """Exibe as opções de escolha de número (brasileiro ou estrangeiro) para o serviço escolhido."""
   
    # Verifica se o serviço existe no dicionário
    if service_name in service_prices:
        # Obtém os preços para os dois tipos de números (br e foreign)
        service_data = service_prices[service_name]
        print(service_data)

        # Verifica se existem preços válidos para 'br' e 'foreign'
        if isinstance(service_data, dict) and 'br' in service_data and 'us' in service_data and 'cn' in service_data and 'en' in service_data and 'fr' in service_data:
            br_price = service_data['br']
            us_price = service_data['us']
            cn_price = service_data['cn']
            en_price = service_data['en']
            fr_price = service_data['fr']
        else:
            # Se não encontrar preços válidos
            br_price = us_price = cn_price = en_price = fr_price = None
    else:
        # Se o serviço não existir no dicionário
        br_price = us_price = cn_price = en_price = fr_price = None

    # Se o preço do serviço estiver disponível
    if br_price is not None and us_price is not None and en_price is not None and cn_price is not None and en_price is not None and fr_price is not None:
        # Formatação dos preços para mostrar no botão
        br_price_text = f"R${br_price:.2f}"
        us_price_text = f"R${us_price:.2f}"
        cn_price_text = f"R${cn_price:.2f}"
        en_price_text = f"R${en_price:.2f}"
        fr_price_text = f"R${fr_price:.2f}"
    else:
        br_price_text = us_price_text = cn_price_text = en_price_text = fr_price_text = "Preço não disponível"
    # Determina o preço do serviço baseado no nome do serviço

    # Botões para números
    back_button = InlineKeyboardButton("Voltar", callback_data='show_services')

    # Adicionando as opções de número brasileiro e estrangeiro
    keyboard = [
        [InlineKeyboardButton(f"Número Brasileiro - R${br_price_text}", callback_data=f"rent_{service_name}_br")],
        [InlineKeyboardButton(f"Número Americano - R${us_price_text}", callback_data=f"rent_{service_name}_us")],
        [InlineKeyboardButton(f"Número Canadense - R${cn_price_text}", callback_data=f"rent_{service_name}_cn")],
        [InlineKeyboardButton(f"Número Inglês - R${en_price_text}", callback_data=f"rent_{service_name}_en")],
        [InlineKeyboardButton(f"Número Françês - R${fr_price_text}", callback_data=f"rent_{service_name}_fr")],
        [back_button]
    ]
    


    reply_markup = InlineKeyboardMarkup(keyboard)

    # Responde com as opções de número
    await update.callback_query.message.reply_text(
        f"Escolha o tipo de número para o serviço:",
        reply_markup=reply_markup
    )


# Função start que exibe o menu principal e os serviços
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    # Menu principal com opções e serviços
    message = update.message if update.message else update.callback_query.message

    main_keyboard = [
        [
            InlineKeyboardButton("Ver Saldo", callback_data='check_balance'),
        ],
        [
            InlineKeyboardButton("Recarregar saldo", callback_data='pix'),
        ],
        [
            InlineKeyboardButton("Ver Serviços", callback_data='show_services'),
        ],
    ] 
    # + services_keyboard  # Adiciona os botões de serviços ao menu principal

    # Criar o teclado com todas as opções
    main_reply_markup = InlineKeyboardMarkup(main_keyboard)

    # Enviar mensagem com opções do menu principal
    
    await message.reply_text('Escolha uma opção:', reply_markup=main_reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    print(f"Botão clicado: {query.data}")  # Verifique qual valor está sendo recebido


    if query.data == 'check_balance':
        await consultar_saldo(update.effective_user.id, context, update)
    
    elif query.data == 'back_to_main':
        # Retorna ao menu principal
        await start(update, context)
    elif query.data == 'back_to_faq_menu':
        await faq(update, context)

    elif query.data == 'pix':
        await valor_digitado(update, context)
    
    elif query.data == 'show_services':
        # Chama a função para mostrar os serviços
        await show_services(update, context)
        
    elif query.data.startswith('rent_'):
        # Lógica para quando um serviço for clicado, exibe as opções de número
        if 'rent_' in query.data:
            service_code = query.data.split('_')[1]  # Ex: rent_ig -> 'ig'
            print(f"Alugando serviço: {service_code}")
            # Aqui, vamos verificar a seleção do tipo de número (brasileiro ou estrangeiro)
            if len(query.data.split('_')) > 2:
                # Se o tipo de número (brasileiro ou estrangeiro) estiver na string do callback
                number_type = query.data.split('_')[2]  # 'br' ou 'foreign'
                await rent_number(update, context, service_code, number_type)
            else:
                # Caso a seleção ainda seja do serviço, exibe as opções
                await show_service_options(update, context, service_code)


async def saldo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    await consultar_saldo(user_id, context, update)


# Lógica para quando o comando /recarregar é enviado
async def recarregar(update: Update, context: CallbackContext):
    # Pode chamar a função de pagamento ou algo semelhante aqui
     # Exemplo de valor fixo para recarga
    await valor_digitado (update, context)

async def servicos(update: Update, context: CallbackContext):
    # Pode chamar a função de pagamento ou algo semelhante aqui
     # Exemplo de valor fixo para recarga
    await show_services(update, context)


async def faq(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Como colocar saldo na minha conta?", callback_data='faq_1')],
        [InlineKeyboardButton("É possível escolher um DDD específico?", callback_data='faq_2')],
        [InlineKeyboardButton("O número fica ativo por quanto tempo?", callback_data='faq_3')],
        [InlineKeyboardButton("Posso utilizar o número para 2 apps diferentes?", callback_data='faq_4')],
        [InlineKeyboardButton("Utilizei o número e o código não chegou, o que fazer?", callback_data='faq_5')],
        [InlineKeyboardButton("Posso usar o número para atendimento na minha empresa?", callback_data='faq_6')],
        [InlineKeyboardButton("Posso utilizar o número para qualquer finalidade?", callback_data='faq_7')],
        [InlineKeyboardButton("Posso ficar com o número após o uso?", callback_data='faq_8')],
        [InlineKeyboardButton("Comprei um número para WhatsApp e já tinha foto e nome", callback_data='faq_9')],
        [InlineKeyboardButton("Eu já pago pelo número assim que for gerado?", callback_data='faq_10')],
        [InlineKeyboardButton("O número comprado é reutilizado novamente?", callback_data='faq_11')],
        [InlineKeyboardButton("O código do Telegram não chega, o que fazer?", callback_data='faq_12')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.reply_text('Olá! Como posso te ajudar hoje?', reply_markup=reply_markup)
    else:
        await update.message.reply_text('Olá! Como posso te ajudar hoje?', reply_markup=reply_markup)




async def faq_answer(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    

    # Mapeia a pergunta à sua respectiva resposta
    faq_responses = {
        'faq_1': "Envie o comando '/recarregar' para o nosso bot, digite o valor que deseja recarregar e finalize o pagamento via PIX.",
        'faq_2': "Infelizmente não é possível escolher DDD específico. Não recomendamos cancelar vários pedidos para tentar escolher um DDD específico.",
        'faq_3': "O prazo de validade do número é de 19 minutos. Após esse tempo, o número não funcionará mais.",
        'faq_4': "Não é possível usar o número para 2 apps diferentes. Você precisará de números distintos para cada plataforma.",
        'faq_5': "Se o código não chegar após 2 minutos, você pode solicitar um novo código ou comprar um novo número.",
        'faq_6': "Pode usar o número para atendimento, mas não é recomendado por ser válido por um curto período (19 minutos).",
        'faq_7': "Você pode usar o número para qualquer finalidade que não infrinja as leis brasileiras, mas não para atividades ilegais.",
        'faq_8': "Não, o número é deletado após 19 minutos e não pode ser reativado.",
        'faq_9': "Isso pode acontecer. Nesse caso, entre em contato com o suporte e pediremos um reembolso integral.",
        'faq_10': "Não. O pagamento é considerado após você receber o primeiro código de ativação.",
        'faq_11': "Não reutilizamos números já vendidos para o mesmo aplicativo. Caso isso ocorra, entre em contato com o suporte.",
        'faq_12': "O Telegram agora só envia o SMS de ativação para o app oficial. Não funciona em clientes não oficiais.",
    }
    
    answer = faq_responses.get(query.data, "Desculpe, não encontrei uma resposta para sua dúvida.")
    
    # Cria o botão "Voltar"
    
    back_button = InlineKeyboardButton("Voltar", callback_data='back_to_faq_menu')
    # Organiza o layout com a resposta e o botão "Voltar"
    keyboard = [[back_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Edita a mensagem com a resposta e o botão "Voltar"
    await query.edit_message_text(text=answer, reply_markup=reply_markup)
    
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'back_to_menu':
        await start(update, context) 

# # Inicializa o bot e os comandos
def main():
    while True:
        try:
            print("Iniciando bot...")
            conexao_Api = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            conexao_Api.add_handler(CommandHandler('saldo', saldo))
            conexao_Api.add_handler(CommandHandler('recarregar', recarregar))
            conexao_Api.add_handler(CommandHandler('servicos', servicos))
            conexao_Api.add_handler(CommandHandler('start', start))
            conexao_Api.add_handler(CommandHandler('faq', faq))
            conexao_Api.add_handler(CallbackQueryHandler(faq_answer, pattern='^faq_'))
            conexao_Api.add_handler(CallbackQueryHandler(button, pattern='^back_to_menu$'))
            conexao_Api.add_handler(CallbackQueryHandler(button_handler))
            conexao_Api.add_handler(CommandHandler('admin', imprimir_dados_no_bot))
            conexao_Api.add_handler(CommandHandler('zerarsaldo', zerar_saldo))
            conexao_Api.add_handler(CommandHandler('adicionarsaldo', adicionar_saldo_via_comando))
            conexao_Api.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
          
            
            conexao_Api.run_polling()  
        except Exception as e:
            print(f"Erro na conexão com o Telegram: {e}")
            print("Reiniciando o bot em 5 segundos...")
            time.sleep(5)  # Aguarda 5 segundos antes de tentar reconectar


if __name__ == '__main__':
    main()

   
