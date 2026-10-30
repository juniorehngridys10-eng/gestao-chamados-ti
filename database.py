import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "chamados.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de Configurações do Contrato
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contrato_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contratante_nome TEXT,
        contratante_cnpj TEXT,
        contratante_endereco TEXT,
        contratado_nome TEXT,
        contratado_cnpj TEXT,
        contratado_cpf TEXT,
        contratado_pix TEXT,
        contratado_telefone TEXT,
        valor_mensal REAL DEFAULT 3500.00,
        franquia_horas_mensal REAL DEFAULT 8.0,
        valor_hora_excedente REAL DEFAULT 150.00,
        valor_hora_urgente_extra REAL DEFAULT 225.00,
        horario_comercial_inicio TEXT DEFAULT '08:00',
        horario_comercial_fim TEXT DEFAULT '18:00',
        dia_vencimento INTEGER DEFAULT 5
    )
    """)

    # Tabela de Clientes (Multi-cliente / Multi-contratos)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE,
        nome_razao_social TEXT NOT NULL,
        nome_fantasia TEXT,
        cnpj_cpf TEXT,
        endereco_completo TEXT,
        cidade TEXT DEFAULT 'Bacabal',
        estado TEXT DEFAULT 'MA',
        valor_mensal REAL DEFAULT 3500.00,
        franquia_horas_mensal REAL DEFAULT 8.0,
        valor_hora_excedente REAL DEFAULT 150.00,
        valor_hora_urgente_extra REAL DEFAULT 225.00,
        horario_comercial_inicio TEXT DEFAULT '08:00',
        horario_comercial_fim TEXT DEFAULT '18:00',
        dia_vencimento INTEGER DEFAULT 5,
        observacoes TEXT,
        status TEXT DEFAULT 'Ativo',
        created_at TEXT
    )
    """)

    # Tabela de Contatos Oficiais
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contatos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT NOT NULL,
        cargo_departamento TEXT,
        unidade TEXT,
        email TEXT
    )
    """)

    # Tabela de Ativos / Parque Tecnológico (Anexo I)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ativos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT NOT NULL, -- Computador/Notebook, Servidor, Impressora, Coletor, Switch, Roteador, Ponto Wi-Fi
        identificador TEXT NOT NULL, -- Ex: SRV-01, PC-BALCAO-01, IMP-03
        descricao TEXT,
        localizacao_setor TEXT,
        unidade TEXT, -- Unidade BR 316 ou Unidade Centro
        ip_rede TEXT,
        observacoes TEXT,
        status TEXT DEFAULT 'Operacional'
    )
    """)

    # Tabela de Chamados
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chamados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_protocolo TEXT UNIQUE NOT NULL,
        titulo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        solicitante_nome TEXT NOT NULL,
        solicitante_telefone TEXT,
        unidade TEXT NOT NULL, -- Unidade BR 316 / Unidade Centro
        setor TEXT,
        ativo_id INTEGER,
        prioridade TEXT NOT NULL, -- Urgente, Normal, Baixa
        tipo_atendimento TEXT NOT NULL, -- Remoto, Presencial
        status TEXT DEFAULT 'Aberto', -- Aberto, Em Atendimento, Aguardando Cliente/Peça, Concluído, Cancelado
        is_fora_horario INTEGER DEFAULT 0, -- 1 se aberto fora do horário comercial
        is_fora_escopo INTEGER DEFAULT 0, -- 1 se for serviço não incluso (peças, licenças, etc)
        data_abertura TEXT NOT NULL,
        previsao_resposta TEXT, -- SLA 1ª Resposta
        previsao_conclusao TEXT, -- SLA Limite
        data_primeira_resposta TEXT,
        data_fechamento TEXT,
        solucao_tecnica TEXT,
        total_minutos_reais INTEGER DEFAULT 0,
        total_minutos_faturados INTEGER DEFAULT 0, -- aplicando regra min 30m remoto / min 60m presencial
        FOREIGN KEY (ativo_id) REFERENCES ativos(id)
    )
    """)

    # Tabela de Apontamentos de Horas (Time Tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS apontamentos_horas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chamado_id INTEGER NOT NULL,
        tecnico_nome TEXT DEFAULT 'Raimundo Loiola Junior',
        tipo_atendimento TEXT NOT NULL, -- Remoto, Presencial
        data_inicio TEXT NOT NULL,
        data_fim TEXT NOT NULL,
        minutos_reais INTEGER NOT NULL,
        minutos_faturados INTEGER NOT NULL, -- mínimo de 30 min (remoto) ou 60 min (presencial)
        is_fora_horario INTEGER DEFAULT 0, -- 1 se executado fora de 08:00-18:00 ou fim de semana
        descricao_trabalho TEXT,
        FOREIGN KEY (chamado_id) REFERENCES chamados(id)
    )
    """)

    # Tabela de Preventivas & Rotinas de Backup (Cláusulas 3.2, 3.3 e 11)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rotinas_backup_preventiva (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mes_ano TEXT NOT NULL, -- Formato 'YYYY-MM'
        tipo_rotina TEXT NOT NULL, -- 'Backup Servidores' ou 'Preventiva Parque Tecnológico'
        data_execucao TEXT,
        status TEXT DEFAULT 'Pendente', -- Pendente, Concluído, Alerta
        responsavel_tecnico TEXT DEFAULT 'Raimundo Loiola Junior',
        responsavel_cliente TEXT, -- Ex: Celijane ou D. Elem
        detalhes_execucao TEXT,
        backup_nuvem_ok INTEGER DEFAULT 0,
        backup_hd_externo_ok INTEGER DEFAULT 0,
        espaco_disco_ok INTEGER DEFAULT 0,
        antivirus_ok INTEGER DEFAULT 0,
        observacoes TEXT
    )
    """)

    # Migração segura: Adicionar coluna cliente_id se não existir
    for tabela in ["contatos", "ativos", "chamados", "rotinas_backup_preventiva"]:
        cursor.execute(f"PRAGMA table_info({tabela})")
        colunas = [col[1] for col in cursor.fetchall()]
        if "cliente_id" not in colunas:
            cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN cliente_id INTEGER DEFAULT 1")

    conn.commit()

    # Seed inicial de dados se o banco estiver vazio
    seed_initial_data(cursor, conn)
    conn.close()

def seed_initial_data(cursor, conn):
    # Clientes
    cursor.execute("SELECT COUNT(*) FROM clientes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO clientes (
            id, slug, nome_razao_social, nome_fantasia, cnpj_cpf, endereco_completo, cidade, estado,
            valor_mensal, franquia_horas_mensal, valor_hora_excedente, valor_hora_urgente_extra,
            horario_comercial_inicio, horario_comercial_fim, dia_vencimento, observacoes, status, created_at
        ) VALUES (
            1, 'francisco-silva', 'FRANCISCO S SILVA COMÉRCIO ATACADISTA', 'Francisco Silva Atacado',
            '05.309.054/0001-57', 'Rod. BR 316, KM 361, nº 25', 'Bacabal', 'MA',
            3500.00, 8.0, 150.00, 225.00, '08:00', '18:00', 5,
            'Contrato principal de suporte técnico em TI, gestão do parque de 46 equipamentos e 2 servidores.',
            'Ativo', datetime('now')
        )
        """)
        # Atualiza registros existentes para cliente_id = 1
        for tab in ["contatos", "ativos", "chamados", "rotinas_backup_preventiva"]:
            cursor.execute(f"UPDATE {tab} SET cliente_id = 1 WHERE cliente_id IS NULL OR cliente_id = 0")

    # Verifica se já tem contrato_config
    cursor.execute("SELECT COUNT(*) FROM contrato_config")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO contrato_config (
            contratante_nome, contratante_cnpj, contratante_endereco,
            contratado_nome, contratado_cnpj, contratado_cpf, contratado_pix, contratado_telefone,
            valor_mensal, franquia_horas_mensal, valor_hora_excedente, valor_hora_urgente_extra,
            horario_comercial_inicio, horario_comercial_fim, dia_vencimento
        ) VALUES (
            'FRANCISCO S SILVA COMÉRCIO ATACADISTA',
            '05.309.054/0001-57',
            'Rod. BR 316, KM 361, nº 25, Bacabal - MA, CEP 65700-000',
            'RAIMUNDO FRANCISCO DE LOIOLA JUNIOR',
            'MEI - SIMEI',
            '029.663.593-66',
            '99981383157',
            '(99) 98138-3157',
            3500.00,
            8.0,
            150.00,
            225.00,
            '08:00',
            '18:00',
            5
        )
        """)

    # Contatos Oficiais
    cursor.execute("SELECT COUNT(*) FROM contatos")
    if cursor.fetchone()[0] == 0:
        contatos_data = [
            ("Celijane", "(99) 98134-3989", "Administração / Abertura de Chamados", "Unidade BR 316", "financeiro@franciscosilva.com.br"),
            ("D. Elem", "(99) 98152-7346", "Gerência / Abertura de Chamados", "Unidade Centro", "gerencia@franciscosilva.com.br"),
            ("Dr. Soares", "(99) 98100-0001", "Diretoria", "Unidade BR 316", "diretoria.soares@franciscosilva.com.br"),
            ("D. Riza", "(99) 98100-0002", "Diretoria", "Unidade BR 316", "diretoria.riza@franciscosilva.com.br"),
            ("Balcão de Vendas", "(99) 98100-0003", "Vendas Atacado", "Unidade BR 316", "balcao@franciscosilva.com.br"),
            ("Departamento de RH", "(99) 98100-0004", "Recursos Humanos", "Unidade BR 316", "rh@franciscosilva.com.br")
        ]
        cursor.executemany("""
        INSERT INTO contatos (nome, telefone, cargo_departamento, unidade, email)
        VALUES (?, ?, ?, ?, ?)
        """, contatos_data)

    # Ativos Cobertos no Anexo I
    cursor.execute("SELECT COUNT(*) FROM ativos")
    if cursor.fetchone()[0] == 0:
        ativos_data = []

        # 2 Servidores
        ativos_data.append(("Servidor", "SRV-01-DATABASE", "Servidor Principal (Banco de Dados Winthor/ERP)", "Sala do Servidor", "Unidade BR 316", "192.168.1.10", "Rotina diária de backup em Nuvem e HD Externo acordada na Cláusula 11", "Operacional"))
        ativos_data.append(("Servidor", "SRV-02-FILES", "Servidor de Arquivos e Pastas Compartilhadas", "Sala do Servidor", "Unidade BR 316", "192.168.1.11", "Pastas compartilhadas e relatórios de vendas. Backup periódico.", "Operacional"))

        # 17 Computadores e notebooks
        for i in range(1, 18):
            if i <= 4:
                setor = "Balcão de Vendas"
                unidade = "Unidade BR 316"
                desc = f"PC Balcão Atacado {i} - Faturamento e PDV"
            elif i <= 7:
                setor = "Departamento de Vendas"
                unidade = "Unidade BR 316"
                desc = f"PC Vendas/Televendas {i-4}"
            elif i <= 9:
                setor = "Departamento de RH"
                unidade = "Unidade BR 316"
                desc = f"PC Recursos Humanos {i-7} - Folha e Ponto"
            elif i == 10:
                setor = "Diretoria Dr. Soares"
                unidade = "Unidade BR 316"
                desc = "Notebook Executivo Dr. Soares"
            elif i == 11:
                setor = "Diretoria D. Riza"
                unidade = "Unidade BR 316"
                desc = "Notebook Executivo D. Riza"
            elif i <= 14:
                setor = "Administração / Financeiro"
                unidade = "Unidade BR 316"
                desc = f"PC Administrativo Celijane / Equipe {i-11}"
            else:
                setor = "Unidade Centro - Atendimento"
                unidade = "Unidade Centro"
                desc = f"PC Unidade Centro {i-14} - Atendimento D. Elem"
            ativos_data.append(("Computador/Notebook", f"PC-{i:02d}", desc, setor, unidade, f"192.168.1.{20+i}", "Coberto por suporte corretivo e preventiva mensal", "Operacional"))

        # 7 Impressoras
        impressoras = [
            ("IMP-01", "Impressora Laser Balcão (Notas Fiscais)", "Balcão de Vendas", "Unidade BR 316", "192.168.1.101"),
            ("IMP-02", "Impressora Térmica Balcão (Cupom/Romaneio)", "Balcão de Vendas", "Unidade BR 316", "192.168.1.102"),
            ("IMP-03", "Impressora Multifuncional RH", "Departamento de RH", "Unidade BR 316", "192.168.1.103"),
            ("IMP-04", "Impressora Vendas Atacado", "Departamento de Vendas", "Unidade BR 316", "192.168.1.104"),
            ("IMP-05", "Impressora Diretoria Dr. Soares", "Diretoria Dr. Soares", "Unidade BR 316", "192.168.1.105"),
            ("IMP-06", "Impressora Diretoria D. Riza", "Diretoria D. Riza", "Unidade BR 316", "192.168.1.106"),
            ("IMP-07", "Impressora Multifuncional Unidade Centro", "Escritório Centro", "Unidade Centro", "192.168.2.107")
        ]
        for tag, desc, setor, unidade, ip in impressoras:
            ativos_data.append(("Impressora", tag, desc, setor, unidade, ip, "Suporte a drivers, configuração e solução de falhas", "Operacional"))

        # 3 Coletores de dados
        for i in range(1, 4):
            ativos_data.append(("Coletor de Dados", f"COL-0{i}", f"Coletor de Dados Sem Fio 0{i} (Expedição/Inventário)", "Estoque/Expedição", "Unidade BR 316", f"192.168.1.{150+i}", "Suporte de rede e conectividade Wi-Fi (excluído software de terceiros conforme Cláusula 3.7)", "Operacional"))

        # 10 Switches (3 no balcão de vendas, 2 na sala do servidor, 1 no dep. de vendas, 1 no dep. de RH, 2 na diretoria do Dr. Soares e 1 na diretoria da D. Riza)
        switches = [
            ("SW-01", "Switch 24p Balcão de Vendas A", "Balcão de Vendas", "Unidade BR 316"),
            ("SW-02", "Switch 24p Balcão de Vendas B", "Balcão de Vendas", "Unidade BR 316"),
            ("SW-03", "Switch 16p Balcão de Vendas C", "Balcão de Vendas", "Unidade BR 316"),
            ("SW-04", "Switch Core Gerenciável 24p Sala Servidor A", "Sala do Servidor", "Unidade BR 316"),
            ("SW-05", "Switch Core Gerenciável 24p Sala Servidor B", "Sala do Servidor", "Unidade BR 316"),
            ("SW-06", "Switch 16p Departamento de Vendas", "Departamento de Vendas", "Unidade BR 316"),
            ("SW-07", "Switch 16p Departamento de RH", "Departamento de RH", "Unidade BR 316"),
            ("SW-08", "Switch 8p Diretoria Dr. Soares A", "Diretoria Dr. Soares", "Unidade BR 316"),
            ("SW-09", "Switch 8p Diretoria Dr. Soares B", "Diretoria Dr. Soares", "Unidade BR 316"),
            ("SW-10", "Switch 8p Diretoria D. Riza", "Diretoria D. Riza", "Unidade BR 316")
        ]
        for tag, desc, setor, unidade in switches:
            ativos_data.append(("Switch de Rede", tag, desc, setor, unidade, "-", "Administração e suporte da rede local conforme Cláusula 3.5", "Operacional"))

        # 7 Roteadores (3 na unidade Brasil Centro e 4 na unidade Brasil BR)
        roteadores = [
            ("ROUTER-01-BR", "Roteador Gateway Principal BR 316", "Sala do Servidor", "Unidade BR 316"),
            ("ROUTER-02-BR", "Roteador Borda Link Secundário BR", "Sala do Servidor", "Unidade BR 316"),
            ("ROUTER-03-BR", "Roteador Distribuição Vendas/Balcão BR", "Balcão de Vendas", "Unidade BR 316"),
            ("ROUTER-04-BR", "Roteador Distribuição Galpão/Expedição BR", "Estoque/Expedição", "Unidade BR 316"),
            ("ROUTER-01-CENTRO", "Roteador Gateway Centro Link Principal", "Central de Comunicações", "Unidade Centro"),
            ("ROUTER-02-CENTRO", "Roteador Distribuição Escritório Centro", "Administração Centro", "Unidade Centro"),
            ("ROUTER-03-CENTRO", "Roteador Wi-Fi Visitantes Centro", "Recepção Centro", "Unidade Centro")
        ]
        for tag, desc, setor, unidade in roteadores:
            ativos_data.append(("Roteador", tag, desc, setor, unidade, "-", "Roteamento e diagnóstico de acesso à Internet", "Operacional"))

        # 3 Pontos de Wi-Fi
        wifi_aps = [
            ("AP-WIFI-01", "Access Point Wi-Fi Coletores Galpão (2.4/5GHz)", "Estoque/Expedição", "Unidade BR 316"),
            ("AP-WIFI-02", "Access Point Wi-Fi Balcão & Administrativo", "Balcão de Vendas", "Unidade BR 316"),
            ("AP-WIFI-03", "Access Point Wi-Fi Diretoria & Reuniões", "Diretoria", "Unidade BR 316")
        ]
        for tag, desc, setor, unidade in wifi_aps:
            ativos_data.append(("Ponto de Wi-Fi", tag, desc, setor, unidade, "-", "Frequência 2.4 GHz / 5 GHz para coletores e equipe", "Operacional"))

        cursor.executemany("""
        INSERT INTO ativos (categoria, identificador, descricao, localizacao_setor, unidade, ip_rede, observacoes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ativos_data)

    # Exemplos de chamados representativos do mês atual para demonstração imediata das regras
    cursor.execute("SELECT COUNT(*) FROM chamados")
    if cursor.fetchone()[0] == 0:
        agora = datetime.now()
        mes_atual_str = agora.strftime("%Y-%m")

        # Chamado 1: Remoto em horário comercial (45 min reais -> mínimo 30m, então faturado 45m ou 0.75h)
        data_c1 = (agora - timedelta(days=5)).strftime("%Y-%m-%d 09:30:00")
        data_resp_c1 = (agora - timedelta(days=5)).strftime("%Y-%m-%d 10:00:00")
        data_fim_c1 = (agora - timedelta(days=5)).strftime("%Y-%m-%d 10:45:00")
        cursor.execute("""
        INSERT INTO chamados (
            numero_protocolo, titulo, descricao, solicitante_nome, solicitante_telefone,
            unidade, setor, ativo_id, prioridade, tipo_atendimento, status,
            is_fora_horario, is_fora_escopo, data_abertura, previsao_resposta, previsao_conclusao,
            data_primeira_resposta, data_fechamento, solucao_tecnica, total_minutos_reais, total_minutos_faturados
        ) VALUES (
            'CHAM-202610-001', 'Lentidão no faturamento e erro de impressão de NF',
            'Computador do Balcão 02 travando ao enviar faturamento para a impressora laser.',
            'Celijane', '(99) 98134-3989', 'Unidade BR 316', 'Balcão de Vendas', 3, 'Normal', 'Remoto',
            'Concluído', 0, 0, ?, ?, ?, ?, ?, 'Reinstalação do spooler de impressão e limpeza de arquivos temporários do Winthor.', 45, 45
        )
        """, (data_c1, data_c1, data_fim_c1, data_resp_c1, data_fim_c1))
        c1_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO apontamentos_horas (chamado_id, tecnico_nome, tipo_atendimento, data_inicio, data_fim, minutos_reais, minutos_faturados, is_fora_horario, descricao_trabalho)
        VALUES (?, 'Raimundo Loiola Junior', 'Remoto', ?, ?, 45, 45, 0, 'Acesso remoto AnyDesk, reset do spooler, teste de impressão OK.')
        """, (c1_id, data_resp_c1, data_fim_c1))

        # Chamado 2: Presencial em horário comercial (40 min reais -> contagem mínima de 60 min pela Cláusula 6.2)
        data_c2 = (agora - timedelta(days=3)).strftime("%Y-%m-%d 14:00:00")
        data_resp_c2 = (agora - timedelta(days=3)).strftime("%Y-%m-%d 14:30:00")
        data_fim_c2 = (agora - timedelta(days=3)).strftime("%Y-%m-%d 15:10:00")
        cursor.execute("""
        INSERT INTO chamados (
            numero_protocolo, titulo, descricao, solicitante_nome, solicitante_telefone,
            unidade, setor, ativo_id, prioridade, tipo_atendimento, status,
            is_fora_horario, is_fora_escopo, data_abertura, previsao_resposta, previsao_conclusao,
            data_primeira_resposta, data_fechamento, solucao_tecnica, total_minutos_reais, total_minutos_faturados
        ) VALUES (
            'CHAM-202610-002', 'Ponto de rede desconectando na sala do Dr. Soares',
            'Cabo de rede com conector frouxo provocando queda intermitente da conexão.',
            'Celijane', '(99) 98134-3989', 'Unidade BR 316', 'Diretoria Dr. Soares', 12, 'Normal', 'Presencial',
            'Concluído', 0, 0, ?, ?, ?, ?, ?, 'Substituição do conector RJ-45 (crimpage) e teste de continuidade com testador de cabos.', 40, 60
        )
        """, (data_c2, data_c2, data_fim_c2, data_resp_c2, data_fim_c2))
        c2_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO apontamentos_horas (chamado_id, tecnico_nome, tipo_atendimento, data_inicio, data_fim, minutos_reais, minutos_faturados, is_fora_horario, descricao_trabalho)
        VALUES (?, 'Raimundo Loiola Junior', 'Presencial', ?, ?, 40, 60, 0, 'Visita presencial na Unidade BR 316. Recrimpagem do conector. Aplicação do piso contratual de 1h mínima.')
        """, (c2_id, data_resp_c2, data_fim_c2))

        # Chamado 3: Chamado Aberto / Em Andamento - Urgente
        data_c3 = (agora - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        previsao_resp_c3 = (agora + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO chamados (
            numero_protocolo, titulo, descricao, solicitante_nome, solicitante_telefone,
            unidade, setor, ativo_id, prioridade, tipo_atendimento, status,
            is_fora_horario, is_fora_escopo, data_abertura, previsao_resposta, previsao_conclusao,
            data_primeira_resposta, data_fechamento, solucao_tecnica, total_minutos_reais, total_minutos_faturados
        ) VALUES (
            'CHAM-202610-003', 'Oscilação no Switch do Balcão de Vendas (SW-01)',
            'Alguns terminais de venda perderam conexão de rede momentaneamente.',
            'D. Elem', '(99) 98152-7346', 'Unidade BR 316', 'Balcão de Vendas', 28, 'Urgente', 'Remoto',
            'Em Atendimento', 0, 0, ?, ?, ?, ?, NULL, NULL, 0, 0
        )
        """, (data_c3, previsao_resp_c3, (agora + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), data_c3))

        # Rotinas de Backup e Preventiva do mês
        cursor.execute("""
        INSERT INTO rotinas_backup_preventiva (
            mes_ano, tipo_rotina, data_execucao, status, responsavel_tecnico, responsavel_cliente,
            detalhes_execucao, backup_nuvem_ok, backup_hd_externo_ok, espaco_disco_ok, antivirus_ok, observacoes
        ) VALUES (
            ?, 'Backup Servidores', ?, 'Concluído', 'Raimundo Loiola Junior', 'Celijane',
            'Verificação dos 2 servidores (SRV-01 e SRV-02). Rotina de dump Oracle/Winthor conferida com sucesso no HD Externo e na Nuvem.',
            1, 1, 1, 1, 'Espaço livre em disco: SRV-01 (184 GB livres), SRV-02 (420 GB livres). Tudo em conformidade com Cláusula 11.'
        )
        """, (mes_atual_str, (agora - timedelta(days=7)).strftime("%Y-%m-%d 11:00:00")))

        cursor.execute("""
        INSERT INTO rotinas_backup_preventiva (
            mes_ano, tipo_rotina, data_execucao, status, responsavel_tecnico, responsavel_cliente,
            detalhes_execucao, backup_nuvem_ok, backup_hd_externo_ok, espaco_disco_ok, antivirus_ok, observacoes
        ) VALUES (
            ?, 'Preventiva Parque Tecnológico', ?, 'Concluído', 'Raimundo Loiola Junior', 'D. Elem',
            'Visita mensal preventiva: verificação de antivírus em 17 estações, atualização de patches críticos do Windows e limpeza de arquivos temporários.',
            1, 0, 1, 1, 'Todos os 17 PCs operacionais com antivírus atualizado e sem malwares detectados.'
        )
        """, (mes_atual_str, (agora - timedelta(days=10)).strftime("%Y-%m-%d 16:00:00")))

    conn.commit()
