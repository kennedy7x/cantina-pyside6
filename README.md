# 🍔 Cantina+

Sistema desktop de autoatendimento para cantina escolar, feito em Python + PySide6.

## Funcionalidades

- Totem com cadastro/login por CPF
- Pagamento por PIX (QR Code), Cartão (crédito/débito) e Dinheiro
- Fiado por aluno com limite de R$ 20 e quitação pelo totem
- Painel da cozinha com colunas por status
- Administração: cardápio, estoque, fiados, despesas, relatórios e PDF
- Controle de acesso do Admin por senha

## Stack

Python 3.11+, PySide6, SQLite, qrcode

## Como rodar

```bash
pip install -r requirements.txt
python run.py

O banco é criado automaticamente em instance/cantina.db.

Senha inicial do Admin
cantina123