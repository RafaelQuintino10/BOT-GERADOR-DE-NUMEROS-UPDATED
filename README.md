
# Sistema de Aluguel de Números Virtuais via Telegram

Este projeto é um **bot do Telegram** para aluguel de números virtuais, permitindo que os usuários aluguem números para diversas plataformas como WhatsApp, Telegram, Discord, entre outras. O bot oferece funcionalidades como consulta de saldo, recarga via PIX, escolha de serviço, e interações com o usuário para o gerenciamento de números alugados.

## Funcionalidades

- **Aluguel de Números Virtuais**: Permite que o usuário alugue números para diversas plataformas.
- **Consulta de Saldo**: O usuário pode verificar o saldo disponível na conta do bot.
- **Recarga de Saldo**: Permite que o usuário recarregue o saldo via PIX.
- **Gestão de Serviços**: O usuário pode escolher entre diversos serviços que oferecem números virtuais.
- **Integração com SMS-Activate API**: O bot integra-se com a API da SMS-Activate para fornecer números virtuais para os usuários.
- **Comandos de FAQ**: O bot fornece respostas para perguntas frequentes relacionadas ao serviço.

## Como Funciona

### 1. Início da Conversa

Quando o usuário inicia uma conversa com o bot, o comando `/start` é disparado. O bot então apresenta um menu principal com as seguintes opções:

- **Ver Saldo**: Mostra o saldo atual do usuário.
- **Recarregar Saldo**: Direciona o usuário para a página de pagamento para recarregar o saldo via PIX.
- **Ver Serviços**: Exibe a lista de serviços para os quais o usuário pode alugar números virtuais.

### 2. Aluguel de Números

O usuário pode alugar números virtuais de diversas plataformas (WhatsApp, Telegram, Discord, etc.). Ao escolher um serviço, o bot apresenta uma lista de opções de números, incluindo números de diferentes países (Brasil, Estados Unidos, Canadá, etc.), com preços distintos para cada tipo de número.

Após o usuário escolher o tipo de número desejado, o bot verifica se há saldo suficiente na conta do usuário. Se o saldo for insuficiente, o bot solicita que o usuário recarregue o saldo via PIX. Caso o saldo seja suficiente, o bot faz a requisição à **API SMS-Activate** para alugar o número virtual.

### 3. Consulta de Saldo

O comando `/saldo` permite que o usuário consulte o saldo disponível em sua conta no bot. O saldo é atualizado conforme os pagamentos realizados e as transações feitas.

### 4. Recarga de Saldo

O comando `/recarregar` permite que o usuário recarregue o saldo via **PIX**. Ao escolher esta opção, o bot gera um QR code que o usuário pode escanear para efetuar o pagamento. O bot monitora o pagamento e, assim que ele for confirmado, o saldo do usuário é atualizado automaticamente.

### 5. Perguntas Frequentes (FAQ)

O bot possui uma seção de **FAQ** onde o usuário pode obter respostas para as perguntas mais comuns sobre o serviço. As perguntas abordam tópicos como:

- Como colocar saldo na conta?
- Como escolher um DDD específico?
- Qual a validade do número alugado?
- Posso utilizar o número para múltiplos aplicativos?

### 6. Monitoramento do Pagamento

Após a realização do pagamento via PIX, o bot monitora o status da transação. Assim que o pagamento for confirmado, o bot notifica o usuário e libera os serviços contratados.

## Fluxo de Uso

1. **Iniciar o Bot**:
   - O usuário envia o comando `/start` para começar a interação.
   - O bot apresenta o menu principal com as opções de saldo, recarga e serviços.

2. **Verificar o Saldo**:
   - O usuário envia o comando `/saldo` para verificar o saldo disponível.
   
3. **Recarga de Saldo**:
   - O usuário escolhe recarregar o saldo através do comando `/recarregar`.
   - O bot gera um QR code de pagamento via PIX.
   - O usuário efetua o pagamento e, após a confirmação, o saldo é atualizado.

4. **Alugar Números**:
   - O usuário escolhe o serviço desejado com o comando `/servicos`.
   - O bot exibe uma lista de serviços e permite a escolha do tipo de número (ex: número brasileiro, americano, canadense).
   - O bot verifica o saldo e, se for suficiente, aluga o número através da API SMS-Activate.

5. **FAQ**:
   - O usuário pode consultar a seção de perguntas frequentes usando o comando `/faq`.
   - O bot responde com as informações sobre cada pergunta.

## Comandos Disponíveis

- **/start**: Inicia o bot e apresenta o menu principal.
- **/saldo**: Exibe o saldo atual do usuário.
- **/recarregar**: Inicia o processo de recarga de saldo via PIX.
- **/servicos**: Exibe a lista de serviços para aluguel de números virtuais.
- **/faq**: Exibe uma lista de perguntas frequentes sobre o serviço.

### Comandos de Administração

- **/admin**: Comando de administração para gerenciar dados do bot (somente administradores).
- **/zerarsaldo**: Zera o saldo de um usuário (somente administradores).
- **/adicionarsaldo**: Adiciona saldo manualmente a um usuário (somente administradores).

## Requisitos

- **Python 3.8 ou superior**.
- **Bibliotecas**:
  - `python-telegram-bot`
  - `requests`
  - `qrcode`
  - `sqlite3`
  - **Outras dependências podem ser instaladas através do arquivo `requirements.txt`**.



