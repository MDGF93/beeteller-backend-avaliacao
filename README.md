# PIX Message Collection API

API para coleta e entrega de mensagens PIX, com suporte a long polling, múltiplos streams paralelos e prevenção de duplicidade de mensagens.

## Visão Geral

Este projeto fornece uma API para instituições financeiras coletarem mensagens PIX de forma eficiente.
Principais recursos:

- **Long Polling:** coleta eficiente de mensagens sem necessidade de polling constante.
- **Streams Paralelos:** até 6 streams simultâneos por instituição (ISPB).
- **Prevenção de Duplicidade:** cada mensagem é entregue apenas uma vez.
- **Geração de Dados de Teste:** endpoint utilitário para criar mensagens PIX fictícias.

A API foi construída com FastAPI e SQLAlchemy.

## Como Executar com Docker

1. **Construa a imagem Docker (se necessário):**
   ```bash
   docker build -t pix-message-api .
   ```
2. **Execute o container:**
   ```bash
   docker run -d -p 8000:8000 --name pix-api pix-message-api
   ```
3. **Acesse a documentação interativa:**
   ```bash
   http://localhost:8000/docs
   ```

## Observação

* Por padrão, a API utiliza um banco de dados SQLite local (**app.db** e **test.db**).
* Para acessar uma versão da aplicação rodando online, utilize o link: https://beeteller-backend-avaliacao-production.up.railway.app//docs
