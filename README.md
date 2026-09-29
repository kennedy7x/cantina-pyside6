# Cantina+ — Sistema de autoatendimento escolar

Aplicativo desktop completo em **Python 3 + PySide6 + SQLite** para uma cantina escolar. A interface foi projetada para uso em computador ou totem, com botões grandes, navegação simples e estilo visual aplicado por QSS.

## Recursos incluídos

- Autoatendimento com nome do aluno, turma, categorias e produtos.
- Carrinho com inclusão, remoção e ajuste de quantidade.
- Observações do pedido e cálculo automático do total.
- Pagamento simulado por PIX e cartão.
- QR Code real quando a biblioteca `qrcode` está instalada; caso contrário, o sistema exibe um QR de demonstração.
- Criação de senha do pedido e gravação no SQLite.
- Painel da cozinha com atualização automática a cada 10 segundos.
- Alteração de status: Recebido, Em Preparo, Pronto e Entregue.
- Administração de produtos, estoque, edição e desativação sem apagar histórico.
- Relatório diário de faturamento, quantidade de pedidos e divisão por pagamento.
- Banco inicial com quatro categorias e oito produtos de exemplo.

## Estrutura dos arquivos

| Arquivo | Função |
|---|---|
| `main.py` | Todas as telas, navegação e regras da interface PySide6 |
| `database.py` | Banco SQLite, tabelas, dados iniciais, produtos, pedidos e relatórios |
| `run.py` | Ponto de entrada recomendado para executar o sistema |
| `__init__.py` | Metadados do pacote e exportação da classe `Database` |
| `requirements.txt` | Dependências do projeto |
| `cantina.db` | Criado automaticamente na primeira execução |

## Como executar no Windows pelo Visual Studio Code

### 1. Instalar o Python

Baixe o Python 3.11 ou mais recente em <https://www.python.org/downloads/>. Durante a instalação, marque a opção **Add Python to PATH**.

Abra o PowerShell e confirme:

```powershell
python --version
pip --version
```

### 2. Instalar o Visual Studio Code

Baixe o VS Code em <https://code.visualstudio.com/>. No VS Code, instale a extensão oficial **Python**, publicada pela Microsoft.

### 3. Extrair e abrir o ZIP

1. Baixe `cantina_pyside6.zip`.
2. Clique com o botão direito e escolha **Extrair tudo**.
3. Abra o VS Code.
4. Escolha **File > Open Folder**.
5. Selecione a pasta extraída `cantina_pyside6`.

### 4. Criar o ambiente virtual

No VS Code, abra **Terminal > New Terminal** e execute:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, execute uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Depois repita:

```powershell
.venv\Scripts\Activate.ps1
```

Quando estiver ativo, o terminal mostrará algo parecido com `(.venv)` no início da linha.

### 5. Instalar as bibliotecas

Com o ambiente virtual ativado:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

As bibliotecas instaladas serão:

- `PySide6`: interface gráfica Qt para Python.
- `qrcode`: geração do QR Code de demonstração do PIX.

### 6. Executar o programa

Ainda no terminal do VS Code:

```powershell
python run.py
```

Também é possível executar diretamente:

```powershell
python main.py
```

O arquivo `cantina.db` será criado automaticamente na pasta do projeto. Não exclua esse arquivo se quiser preservar pedidos e produtos cadastrados.

### 7. Executar pelo botão de depuração

1. Abra o arquivo `run.py`.
2. No canto superior direito, clique no botão de execução ou pressione `F5`.
3. Se o VS Code perguntar qual interpretador usar, escolha o Python localizado em `.venv`.
4. Para execução sem depuração, use `Ctrl+F5`.

## Como executar pelo Visual Studio Community

O Visual Studio Community também pode abrir projetos Python, mas precisa do workload **Python development**.

1. Instale o Visual Studio Community em <https://visualstudio.microsoft.com/>.
2. No instalador, marque **Python development**.
3. Extraia o ZIP.
4. Abra o Visual Studio e escolha **Open a local folder**.
5. Selecione a pasta `cantina_pyside6`.
6. Abra o terminal integrado em **View > Terminal**.
7. Crie e ative o ambiente virtual:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

8. No Solution Explorer, clique com o botão direito em `run.py` e escolha **Set as Startup File**, quando essa opção estiver disponível.
9. Pressione `F5` ou clique em **Start**.

Se o Visual Studio não reconhecer automaticamente o interpretador, abra as configurações de Python do projeto e selecione `.venv\Scripts\python.exe`.

## Fluxo de teste

1. Na tela **Cliente**, mantenha o aluno de exemplo ou informe outro nome e turma.
2. Clique em **Adicionar** em um ou mais produtos.
3. Ajuste as quantidades no carrinho.
4. Clique em **Avançar para pagamento**.
5. Na aba PIX, clique em **Simular pagamento aprovado**. Na aba cartão, preencha os campos e clique no botão de aprovação.
6. Anote a senha exibida.
7. Abra **Cozinha**, localize o pedido e altere os status.
8. Abra **Admin**, selecione um produto para editar ou desativar e consulte os relatórios.

## Observações importantes

Este é um sistema de demonstração local. O pagamento não é conectado a banco, adquirente ou serviço PIX real. O botão de aprovação apenas valida o fluxo da aplicação e grava o pedido no banco SQLite.