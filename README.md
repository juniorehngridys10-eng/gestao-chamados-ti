# 🖥️ Sistema de Atendimento e Gestão de Chamados TI (Multi-Cliente & HelpDesk)

Sistema completo de HelpDesk e Gestão Contratual de TI desenvolvido para **RAIMUNDO FRANCISCO DE LOIOLA JUNIOR (MEI)** (CPF 029.663.593-66 | Tel: (99) 98138-3157 | Chave PIX: 99981383157), atendendo a carteira de contratos de suporte técnico empresarial em Bacabal - MA.

---

## ✨ Principais Funcionalidades

1. **🧭 Menu Lateral (Sidebar Navigation):**
   - Menu lateral retrátil e responsivo com acesso direto a todas as seções.
   - Seletor de Cliente Ativo no topo da barra lateral para alternar rapidamente entre clientes ou visualizar a carteira consolidada.
   - Indicador de status de Horário Comercial em tempo real (08:00 às 18:00 vs Plantão).
   - Botões de acesso rápido: *Link para Cliente* e *+ Novo Chamado*.

2. **🏢 Gestão de Múltiplos Clientes & Contratos:**
   - Cadastre novos clientes com valores contratuais próprios:
     - Valor mensal do contrato (ex: R$ 3.500,00, R$ 2.800,00, etc.)
     - Franquia mensal de horas (ex: 8h, 10h)
     - Valor da hora excedente em horário comercial (ex: R$ 150,00/h)
     - Valor da hora de urgência / plantão fora do horário (ex: R$ 225,00/h)
     - Dia do vencimento
   - Cada cliente possui seus próprios chamados, ativos, relatórios e link exclusivo de atendimento.

3. **📲 Link Exclusivo para o Cliente Abrir Chamados:**
   - Link de rede local para envio no WhatsApp: `http://192.168.1.22:8000/abrir-chamado?cliente=ID`
   - O cliente relata o problema pelo celular, recebe o protocolo e notifica o técnico no WhatsApp com 1 clique!
   - Cartaz com QR Code pronto para impressão e fixação nos setores.

---

## 🚀 Como Iniciar o Programa

### Opção 1: Clique Duplo (Mais Rápido)
Basta dar dois cliques no arquivo:
```cmd
iniciar.bat
```

### Opção 2: Pelo Terminal / PowerShell
```powershell
cd "C:\Users\JUNIOR LOIOLA\.gemini\antigravity\scratch\gestao-chamados-ti"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Acesse no navegador: **[http://localhost:8000](http://localhost:8000)**

---

## 📲 Link para seu Cliente Abrir Chamados

O sistema conta com um **Portal Exclusivo do Cliente**, 100% responsivo e otimizado para celulares e computadores:

- **Link para envio no WhatsApp:** `http://192.168.1.22:8000/abrir-chamado`
- **Acesso no computador do técnico:** `http://localhost:8000/abrir-chamado`

### Como Funciona para o Cliente:
1. O cliente clica no link pelo celular ou PC da loja (conectado ao Wi-Fi).
2. Seleciona quem está solicitando (Celijane, D. Elem, Balcão, RH, Diretoria, etc.).
3. Descreve o problema e escolhe a gravidade (Normal, Urgente ou Baixa).
4. O sistema gera na hora o **Protocolo Oficial** com prazo de resposta (SLA).
5. O cliente tem um botão de 1 clique **"📲 Notificar Loiola Jr no WhatsApp"**, que já abre o WhatsApp do técnico `(99) 98138-3157` com a mensagem pronta.
6. O cliente também pode consultar o andamento e o parecer técnico do chamado a qualquer momento digitando o número do protocolo!

### Compartilhamento no Painel do Técnico:
No topo do painel administrativo, clique no botão **"🔗 Link para Cliente"** para:
- Copiar o link com 1 clique.
- Enviar direto no WhatsApp de **Celijane `(99) 98134-3989`** ou **D. Elem `(99) 98152-7346`**.
- Imprimir um **Cartaz com QR Code** para colar no Balcão de Vendas e setores.

---

## 📋 Regras de Negócio e Cláusulas Contratuais Implementadas

| Regra / Cláusula | Implementação no Sistema |
| :--- | :--- |
| **Franquia Mensal (Cl. 6.1)** | **08 (oito) horas mensais** inclusas no valor fixo de R$ 3.500,00, sem acúmulo de saldo. Medidor visual em tempo real no Dashboard. |
| **Piso Mínimo de Horas (Cl. 6.2)** | **Remoto:** cômputo mínimo de 30 minutos por atendimento.<br>**Presencial:** cômputo mínimo de 60 minutos (01 hora) por visita/deslocamento. |
| **Horas Excedentes (Cl. 6.3)** | Horas que ultrapassarem as 8h mensais em horário comercial são faturadas a **R$ 150,00/hora**. |
| **Plantão Fora do Horário (Cl. 5.3 e 7.3)** | Atendimentos fora de 08:00 às 18:00 (ou fins de semana) não descontam da franquia e são faturados com +50% (**R$ 225,00/hora**). O sistema detecta o horário em tempo real. |
| **SLA de Resposta (Cl. 6.4)** | • **Urgente:** Diagnóstico remoto em até **02 horas**; presencial até 04 horas úteis.<br>• **Normal:** Primeira resposta em até **04 horas úteis**.<br>• **Baixa:** Atendimento em até **02 dias úteis**. Alertas visuais e cronômetro de estouro. |
| **Parque Tecnológico (Anexo I)** | **46 ativos cobertos** pré-cadastrados:<br>• 17 Computadores e notebooks<br>• 02 Servidores (Winthor e Arquivos)<br>• 07 Impressoras<br>• 03 Coletores de dados<br>• 10 Switches (distribuídos por Balcão, Servidor, Vendas, RH e Diretorias)<br>• 07 Roteadores (Brasil Centro e Brasil BR)<br>• 03 Pontos de Wi-Fi. |
| **Backup e Preventiva (Cl. 3.2, 3.3 e 11)** | Módulo de checklist mensal com registro de integridade de backup em Nuvem e HD Externo dos 02 servidores e preventiva das estações. |
| **Fechamento e Relatório (Cl. 9.4 e 7)** | Apuração automática das horas e valores faturados + emissão com 1 clique do **Relatório Oficial em PDF** timbrado para prestação de contas mensal e chave PIX para pagamento até dia 05. |
| **WhatsApp Rápido (Cl. 16.4)** | Botão de envio instantâneo com texto formatado para os contatos oficiais: **Celijane ((99) 98134-3989)** e **D. Elem ((99) 98152-7346)**. |

---

## 🗂️ Estrutura do Código

```
gestao-chamados-ti/
├── chamados.db          # Banco de dados SQLite persistente com dados do contrato
├── database.py          # Estrutura do banco e carga inicial dos 46 ativos e contatos
├── models.py            # Modelos Pydantic e cálculos contratuais (SLA, pisos, horas)
├── pdf_generator.py     # Gerador do Relatório Mensal oficial em PDF (ReportLab)
├── main.py              # API FastAPI completa e servidor web
├── test_sistema.py      # Bateria de 8 testes automatizados
├── iniciar.bat          # Script de inicialização em 1 clique no Windows
└── static/              # Interface Web responsiva
    ├── index.html       # Painel interativo com todas as abas
    ├── app.js           # Lógica do front-end e integrações
    └── styles.css       # Estilos complementares e impressão
```

---

## 🧪 Testes Automatizados

Para executar os testes de validação contratual:
```powershell
cd "C:\Users\JUNIOR LOIOLA\.gemini\antigravity\scratch\gestao-chamados-ti"
python test_sistema.py
```
Resultado: **8 testes executados com 100% de sucesso**.
