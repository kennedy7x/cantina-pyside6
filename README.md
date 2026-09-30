# 🍔 Cantina+

Sistema desktop de autoatendimento para cantina escolar, feito em **Python + PySide6** com banco **SQLite**.

Trabalho da disciplina de **Programação Orientada a Objetos com Serviços (POOS)**.

## 👥 Integrantes

- Kennedy [Sobrenome] — [RA]
- [Nome 2] — [RA]
- [Nome 3] — [RA]

**Instituição:** [Nome da faculdade]
**Professor:** [Nome do professor]

## ✨ Funcionalidades

- Totem de autoatendimento com cadastro/login por **CPF**
- Pagamento via **PIX** (QR Code), **Cartão** (crédito/débito), **Dinheiro** e **Fiado**
- Fiado por aluno com limite de **R$ 20** e quitação pelo totem
- Painel da cozinha com 3 colunas: **Recebidos / Em preparo / Prontos**
- Administração protegida por senha: cardápio, estoque, fiados, despesas e relatórios
- Exportação de relatório em **PDF**

## 🛠️ Tecnologias

- Python 3.11+
- PySide6 (Qt 6)
- SQLite
- qrcode + Pillow

## 🚀 Como rodar

```bash
pip install -r requirements.txt
python run.py

O banco instance/cantina.db é criado automaticamente na primeira execução.

🔑 Senha inicial do Admin
text
cantina123
Troque em Admin → Segurança após o primeiro login.

📁 Estrutura
text
cantina_pyside6/
├── cantina/
│   ├── database.py           # Camada de dados (SQLite)
│   ├── seed.py               # Catálogo inicial + ícones
│   ├── payment_services.py   # PIX e Cartão (mocks)
│   └── main.py               # Interface (PySide6)
├── instance/                 # Banco gerado em runtime
├── requirements.txt
├── README.md
└── run.py                    # Ponto de entrada
⚠️ Observações
PIX e Cartão são simulados (mocks). Em produção seria necessária integração com um PSP (Mercado Pago, Efí, etc.) e com o SDK da adquirente (Stone, Cielo).

Senha do Admin usa SHA-256 sem salt — suficiente para uso escolar, não para produção bancária.

Não há senha para o aluno: quem souber o CPF entra na conta.

📄 Licença
Projeto acadêmico — uso livre para fins educacionais.

text

---

## Antes de commitar

Preenche só o que está entre `[colchetes]`:

- `[Sobrenome]`, `[RA]`
- `[Nome 2]`, `[RA]`, `[Nome 3]`, `[RA]`
- `[Nome da faculdade]`
- `[Nome do professor]`

Se preferir deixar sem os integrantes, é só apagar essa seção inteira.

Depois:

```bash
git add README.md
git commit -m "docs: adicionar README"
git push