import os
import socket
from datetime import datetime, timedelta
from typing import Optional, List
import urllib.parse
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

import database
import models
import pdf_generator

app = FastAPI(
    title="Sistema de Gestão de Chamados TI - Francisco S Silva & Raimundo Loiola Jr",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o banco no startup
@app.on_event("startup")
def startup_event():
    database.init_db()

# --- Rotas de Configuração e Regras do Contrato ---
@app.get("/api/config")
def get_config():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contrato_config LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Configurações não encontradas")
    return dict(row)

# --- CRUD de Clientes (Multi-Cliente / Multi-Contratos) ---
@app.get("/api/clientes")
def list_clientes():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, 
           COUNT(DISTINCT a.id) as total_ativos,
           COUNT(DISTINCT ch.id) as total_chamados
    FROM clientes c
    LEFT JOIN ativos a ON c.id = a.cliente_id
    LEFT JOIN chamados ch ON c.id = ch.cliente_id
    GROUP BY c.id
    ORDER BY c.nome_razao_social ASC
    """)
    clientes = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return clientes

@app.post("/api/clientes")
def create_cliente(payload: models.ClienteCreate):
    conn = database.get_connection()
    cursor = conn.cursor()
    
    slug_base = payload.nome_razao_social.lower().replace(" ", "-")[:30]
    slug = "".join([c for c in slug_base if c.isalnum() or c == "-"])
    
    cursor.execute("""
    INSERT INTO clientes (
        slug, nome_razao_social, nome_fantasia, cnpj_cpf, endereco_completo, cidade, estado,
        valor_mensal, franquia_horas_mensal, valor_hora_excedente, valor_hora_urgente_extra,
        dia_vencimento, observacoes, status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        slug, payload.nome_razao_social, payload.nome_fantasia or payload.nome_razao_social,
        payload.cnpj_cpf, payload.endereco_completo, payload.cidade, payload.estado,
        payload.valor_mensal, payload.franquia_horas_mensal, payload.valor_hora_excedente,
        payload.valor_hora_urgente_extra, payload.dia_vencimento, payload.observacoes,
        payload.status or "Ativo"
    ))
    cliente_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": cliente_id, "message": "Cliente cadastrado com sucesso", "slug": slug}

@app.get("/api/clientes/{id}")
def get_cliente(id: int):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return dict(row)

@app.put("/api/clientes/{id}")
def update_cliente(id: int, payload: models.ClienteUpdate):
    conn = database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (id,))
    existente = cursor.fetchone()
    if not existente:
        conn.close()
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    cursor.execute("""
    UPDATE clientes
    SET nome_razao_social = COALESCE(?, nome_razao_social),
        nome_fantasia = COALESCE(?, nome_fantasia),
        cnpj_cpf = COALESCE(?, cnpj_cpf),
        endereco_completo = COALESCE(?, endereco_completo),
        cidade = COALESCE(?, cidade),
        estado = COALESCE(?, estado),
        valor_mensal = COALESCE(?, valor_mensal),
        franquia_horas_mensal = COALESCE(?, franquia_horas_mensal),
        valor_hora_excedente = COALESCE(?, valor_hora_excedente),
        valor_hora_urgente_extra = COALESCE(?, valor_hora_urgente_extra),
        dia_vencimento = COALESCE(?, dia_vencimento),
        observacoes = COALESCE(?, observacoes),
        status = COALESCE(?, status)
    WHERE id = ?
    """, (
        payload.nome_razao_social, payload.nome_fantasia, payload.cnpj_cpf,
        payload.endereco_completo, payload.cidade, payload.estado,
        payload.valor_mensal, payload.franquia_horas_mensal, payload.valor_hora_excedente,
        payload.valor_hora_urgente_extra, payload.dia_vencimento, payload.observacoes,
        payload.status, id
    ))
    conn.commit()
    conn.close()
    return {"message": "Cliente atualizado com sucesso"}

@app.delete("/api/clientes/{id}")
def delete_cliente(id: int):
    conn = database.get_connection()
    cursor = conn.cursor()
    # Não deleta o cliente padrão ID 1
    if id == 1:
        conn.close()
        raise HTTPException(status_code=400, detail="Não é permitido remover o cliente principal do contrato.")
    cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Cliente removido com sucesso"}

@app.get("/api/contatos")
def get_contatos(cliente_id: Optional[int] = None):
    conn = database.get_connection()
    cursor = conn.cursor()
    if cliente_id:
        cursor.execute("SELECT * FROM contatos WHERE cliente_id = ? ORDER BY nome ASC", (cliente_id,))
    else:
        cursor.execute("SELECT * FROM contatos ORDER BY nome ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- Rota do Dashboard ---
@app.get("/api/dashboard")
def get_dashboard(mes_ano: str = Query(default=None), cliente_id: Optional[int] = Query(default=None)):
    """
    Retorna métricas consolidadas do mês de acordo com as cláusulas contratuais.
    Permite filtrar por cliente específico ou consolidar geral.
    """
    if not mes_ano:
        mes_ano = datetime.now().strftime("%Y-%m")

    conn = database.get_connection()
    cursor = conn.cursor()

    # Configs contratuais
    cursor.execute("SELECT * FROM contrato_config LIMIT 1")
    config = dict(cursor.fetchone())

    # Se cliente específico foi selecionado, substitui os dados pelos do cliente
    cliente_info = None
    if cliente_id:
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
        cli_row = cursor.fetchone()
        if cli_row:
            cliente_info = dict(cli_row)
            config["contratante_nome"] = cliente_info["nome_razao_social"]
            config["contratante_cnpj"] = cliente_info["cnpj_cpf"] or config["contratante_cnpj"]
            config["contratante_endereco"] = cliente_info["endereco_completo"] or config["contratante_endereco"]
            config["valor_mensal"] = cliente_info["valor_mensal"]
            config["franquia_horas_mensal"] = cliente_info["franquia_horas_mensal"]
            config["valor_hora_excedente"] = cliente_info["valor_hora_excedente"]
            config["valor_hora_urgente_extra"] = cliente_info["valor_hora_urgente_extra"]
            config["dia_vencimento"] = cliente_info["dia_vencimento"]

    # Chamados do mês selecionado
    chamados_query = """
    SELECT c.*, a.identificador as ativo_identificador, a.categoria as ativo_categoria, cl.nome_razao_social as cliente_nome
    FROM chamados c
    LEFT JOIN ativos a ON c.ativo_id = a.id
    LEFT JOIN clientes cl ON c.cliente_id = cl.id
    WHERE strftime('%Y-%m', c.data_abertura) = ?
    """
    chamados_params = [mes_ano]
    if cliente_id:
        chamados_query += " AND c.cliente_id = ?"
        chamados_params.append(cliente_id)

    chamados_query += " ORDER BY c.data_abertura DESC"
    cursor.execute(chamados_query, chamados_params)
    chamados_mes = [dict(r) for r in cursor.fetchall()]

    # Apontamentos de horas do mês
    ap_query = """
    SELECT ap.*, c.numero_protocolo, c.titulo, c.cliente_id
    FROM apontamentos_horas ap
    JOIN chamados c ON ap.chamado_id = c.id
    WHERE strftime('%Y-%m', ap.data_inicio) = ?
    """
    ap_params = [mes_ano]
    if cliente_id:
        ap_query += " AND c.cliente_id = ?"
        ap_params.append(cliente_id)

    cursor.execute(ap_query, ap_params)
    apontamentos = [dict(r) for r in cursor.fetchall()]

    # Rotinas do mês (Backup e Preventiva)
    rot_query = "SELECT * FROM rotinas_backup_preventiva WHERE mes_ano = ?"
    rot_params = [mes_ano]
    if cliente_id:
        rot_query += " AND cliente_id = ?"
        rot_params.append(cliente_id)
    cursor.execute(rot_query, rot_params)
    rotinas = [dict(r) for r in cursor.fetchall()]

    # Contadores
    abertos_query = "SELECT COUNT(*) FROM chamados WHERE status = 'Aberto'"
    em_at_query = "SELECT COUNT(*) FROM chamados WHERE status = 'Em Atendimento'"
    conc_query = "SELECT COUNT(*) FROM chamados WHERE status = 'Concluído' AND strftime('%Y-%m', data_abertura) = ?"
    urg_query = "SELECT COUNT(*) FROM chamados WHERE prioridade = 'Urgente' AND status IN ('Aberto', 'Em Atendimento')"
    
    c_params = []
    if cliente_id:
        abertos_query += " AND cliente_id = ?"
        em_at_query += " AND cliente_id = ?"
        conc_query += " AND cliente_id = ?"
        urg_query += " AND cliente_id = ?"
        c_params = [cliente_id]

    cursor.execute(abertos_query, c_params)
    total_abertos = cursor.fetchone()[0]

    cursor.execute(em_at_query, c_params)
    total_em_atendimento = cursor.fetchone()[0]

    cursor.execute(conc_query, [mes_ano] + c_params)
    total_concluidos_mes = cursor.fetchone()[0]

    cursor.execute(urg_query, c_params)
    total_urgentes_ativos = cursor.fetchone()[0]

    conn.close()

    # Cálculo do consumo de horas no mês de acordo com o contrato
    # Cláusula 6.1: Franquia de 8 horas = 480 minutos para atendimentos comerciais
    # Cláusula 7.3: Atendimentos urgentes fora do horário NÃO descontam da franquia
    minutos_comercial = 0
    minutos_fora_horario = 0

    for ap in apontamentos:
        if ap.get("is_fora_horario") == 1:
            minutos_fora_horario += ap.get("minutos_faturados", 0)
        else:
            minutos_comercial += ap.get("minutos_faturados", 0)

    # Franquia de 8 horas = 480 minutos
    franquia_total_minutos = int(config["franquia_horas_mensal"] * 60)
    minutos_franquia_usados = min(minutos_comercial, franquia_total_minutos)
    minutos_excedentes_comercial = max(0, minutos_comercial - franquia_total_minutos)
    minutos_franquia_restantes = max(0, franquia_total_minutos - minutos_comercial)

    horas_excedentes = minutos_excedentes_comercial / 60.0
    valor_excedentes = horas_excedentes * config["valor_hora_excedente"]

    horas_fora_horario = minutos_fora_horario / 60.0
    valor_fora_horario = horas_fora_horario * config["valor_hora_urgente_extra"]

    valor_fixo = config["valor_mensal"]
    valor_total_faturamento = valor_fixo + valor_excedentes + valor_fora_horario

    # Status de Backup e Preventiva
    backup_ok = any(r["tipo_rotina"] == "Backup Servidores" and r["status"] == "Concluído" for r in rotinas)
    preventiva_ok = any(r["tipo_rotina"] == "Preventiva Parque Tecnológico" and r["status"] == "Concluído" for r in rotinas)

    return {
        "mes_ano": mes_ano,
        "config": config,
        "franquia": {
            "total_horas": config["franquia_horas_mensal"],
            "total_minutos": franquia_total_minutos,
            "minutos_usados": minutos_franquia_usados,
            "horas_usadas_formatada": f"{minutos_franquia_usados // 60:02d}h {minutos_franquia_usados % 60:02d}m",
            "minutos_restantes": minutos_franquia_restantes,
            "horas_restantes_formatada": f"{minutos_franquia_restantes // 60:02d}h {minutos_franquia_restantes % 60:02d}m",
            "percentual_uso": round((minutos_franquia_usados / franquia_total_minutos) * 100, 1),
            "minutos_excedentes_comercial": minutos_excedentes_comercial,
            "horas_excedentes_comercial": round(horas_excedentes, 2),
            "valor_excedentes": round(valor_excedentes, 2),
            "minutos_urgente_fora_horario": minutos_fora_horario,
            "horas_urgente_fora_horario": round(horas_fora_horario, 2),
            "valor_fora_horario": round(valor_fora_horario, 2),
        },
        "financeiro": {
            "valor_fixo": valor_fixo,
            "valor_excedentes": round(valor_excedentes, 2),
            "valor_fora_horario": round(valor_fora_horario, 2),
            "valor_total": round(valor_total_faturamento, 2),
            "dia_vencimento": config["dia_vencimento"],
            "chave_pix": config["contratado_pix"]
        },
        "rotinas": {
            "backup_servidores_ok": backup_ok,
            "preventiva_ok": preventiva_ok,
            "itens": rotinas
        },
        "contadores": {
            "abertos": total_abertos,
            "em_atendimento": total_em_atendimento,
            "concluidos_mes": total_concluidos_mes,
            "urgentes_ativos": total_urgentes_ativos,
            "total_chamados_mes": len(chamados_mes)
        },
        "ultimos_chamados": chamados_mes[:10]
    }

# --- CRUD de Chamados ---
@app.get("/api/chamados")
def list_chamados(
    cliente_id: Optional[int] = None,
    status: Optional[str] = None,
    prioridade: Optional[str] = None,
    unidade: Optional[str] = None,
    mes_ano: Optional[str] = None,
    busca: Optional[str] = None
):
    conn = database.get_connection()
    cursor = conn.cursor()

    query = """
    SELECT c.*, a.identificador as ativo_identificador, a.categoria as ativo_categoria, a.descricao as ativo_descricao,
           cl.nome_razao_social as cliente_nome
    FROM chamados c
    LEFT JOIN ativos a ON c.ativo_id = a.id
    LEFT JOIN clientes cl ON c.cliente_id = cl.id
    WHERE 1=1
    """
    params = []

    if cliente_id:
        query += " AND c.cliente_id = ?"
        params.append(cliente_id)

    if status and status != "Todos":
        query += " AND c.status = ?"
        params.append(status)

    if prioridade and prioridade != "Todas":
        query += " AND c.prioridade = ?"
        params.append(prioridade)

    if unidade and unidade != "Todas":
        query += " AND c.unidade = ?"
        params.append(unidade)

    if mes_ano:
        query += " AND strftime('%Y-%m', c.data_abertura) = ?"
        params.append(mes_ano)

    if busca:
        query += " AND (c.numero_protocolo LIKE ? OR c.titulo LIKE ? OR c.solicitante_nome LIKE ? OR c.descricao LIKE ?)"
        busca_param = f"%{busca}%"
        params.extend([busca_param, busca_param, busca_param, busca_param])

    query += " ORDER BY c.data_abertura DESC"
    cursor.execute(query, params)
    chamados = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Adiciona indicativo de SLA
    agora_dt = datetime.now()
    for ch in chamados:
        sla_estourado = False
        sla_alerta = False
        if ch["status"] in ["Aberto", "Em Atendimento"] and ch.get("previsao_resposta"):
            try:
                prev_resp = datetime.strptime(ch["previsao_resposta"], "%Y-%m-%d %H:%M:%S")
                if agora_dt > prev_resp and not ch.get("data_primeira_resposta"):
                    sla_estourado = True
                elif (prev_resp - agora_dt).total_seconds() < 1800 and not ch.get("data_primeira_resposta"):
                    sla_alerta = True
            except:
                pass
        ch["sla_estourado"] = sla_estourado
        ch["sla_alerta"] = sla_alerta

    return chamados

@app.post("/api/chamados")
def create_chamado(payload: models.ChamadoCreate):
    conn = database.get_connection()
    cursor = conn.cursor()

    agora = datetime.now()
    ano_mes = agora.strftime("%Y%m")

    # Gera número de protocolo único sequencial
    cursor.execute("SELECT COUNT(*) FROM chamados WHERE strftime('%Y%m', data_abertura) = ?", (ano_mes,))
    count_seq = cursor.fetchone()[0] + 1
    numero_protocolo = f"CHAM-{ano_mes}-{count_seq:03d}"

    # Regra Cláusula 5.1 e 5.3: Verifica se é fora do horário
    is_fora = 0 if models.is_horario_comercial(agora) else 1

    # Regra Cláusula 6.4: Calcula SLA
    prev_resposta, prev_conclusao = models.calcular_sla(payload.prioridade, payload.tipo_atendimento, agora)

    cursor.execute("""
    INSERT INTO chamados (
        numero_protocolo, cliente_id, titulo, descricao, solicitante_nome, solicitante_telefone,
        unidade, setor, ativo_id, prioridade, tipo_atendimento, status,
        is_fora_horario, is_fora_escopo, data_abertura, previsao_resposta, previsao_conclusao
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Aberto', ?, ?, ?, ?, ?)
    """, (
        numero_protocolo,
        payload.cliente_id or 1,
        payload.titulo,
        payload.descricao,
        payload.solicitante_nome,
        payload.solicitante_telefone,
        payload.unidade,
        payload.setor,
        payload.ativo_id,
        payload.prioridade,
        payload.tipo_atendimento,
        is_fora,
        1 if payload.is_fora_escopo else 0,
        agora.strftime("%Y-%m-%d %H:%M:%S"),
        prev_resposta,
        prev_conclusao
    ))

    chamado_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"id": chamado_id, "numero_protocolo": numero_protocolo, "is_fora_horario": is_fora}

@app.get("/api/chamados/{id}")
def get_chamado(id: int):
    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT c.*, a.identificador as ativo_identificador, a.categoria as ativo_categoria, a.descricao as ativo_descricao, a.ip_rede as ativo_ip
    FROM chamados c
    LEFT JOIN ativos a ON c.ativo_id = a.id
    WHERE c.id = ?
    """, (id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    chamado = dict(row)

    # Apontamentos do chamado
    cursor.execute("SELECT * FROM apontamentos_horas WHERE chamado_id = ? ORDER BY data_inicio ASC", (id,))
    chamado["apontamentos"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return chamado

@app.put("/api/chamados/{id}")
def update_chamado_status(id: int, payload: models.ChamadoUpdateStatus):
    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM chamados WHERE id = ?", (id,))
    chamado = cursor.fetchone()
    if not chamado:
        conn.close()
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    agora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Se estiver mudando para 'Em Atendimento' e não tiver 1ª resposta, grava agora
    dt_primeira_resp = chamado["data_primeira_resposta"]
    if payload.status == "Em Atendimento" and not dt_primeira_resp:
        dt_primeira_resp = agora_str

    dt_fechamento = chamado["data_fechamento"]
    if payload.status == "Concluído" and not dt_fechamento:
        dt_fechamento = agora_str
    elif payload.status != "Concluído":
        dt_fechamento = None

    cursor.execute("""
    UPDATE chamados
    SET status = ?, solucao_tecnica = COALESCE(?, solucao_tecnica),
        data_primeira_resposta = ?, data_fechamento = ?
    WHERE id = ?
    """, (payload.status, payload.solucao_tecnica, dt_primeira_resp, dt_fechamento, id))

    conn.commit()
    conn.close()
    return {"message": "Chamado atualizado com sucesso"}

@app.delete("/api/chamados/{id}")
def delete_chamado(id: int):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM apontamentos_horas WHERE chamado_id = ?", (id,))
    cursor.execute("DELETE FROM chamados WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Chamado removido"}

# --- Apontamentos de Horas (Time Tracking) ---
@app.post("/api/chamados/{id}/apontamentos")
def add_apontamento(id: int, payload: models.ApontamentoCreate):
    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM chamados WHERE id = ?", (id,))
    chamado = cursor.fetchone()
    if not chamado:
        conn.close()
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    try:
        dt_inicio = datetime.strptime(payload.data_inicio, "%Y-%m-%d %H:%M")
        dt_fim = datetime.strptime(payload.data_fim, "%Y-%m-%d %H:%M")
    except:
        # Fallback para caso venha com segundos
        dt_inicio = datetime.strptime(payload.data_inicio[:16], "%Y-%m-%d %H:%M")
        dt_fim = datetime.strptime(payload.data_fim[:16], "%Y-%m-%d %H:%M")

    diff_minutos = int((dt_fim - dt_inicio).total_seconds() / 60)
    if diff_minutos <= 0:
        diff_minutos = 1

    # Cláusula 6.2: Aplicação da regra do piso mínimo
    minutos_faturados = models.calcular_minutos_faturados(payload.tipo_atendimento, diff_minutos)

    # Verifica se o apontamento é fora de horário
    if payload.is_fora_horario_manual is not None:
        is_fora = 1 if payload.is_fora_horario_manual else 0
    else:
        is_fora = 0 if models.is_horario_comercial(dt_inicio) else 1

    cursor.execute("""
    INSERT INTO apontamentos_horas (
        chamado_id, tecnico_nome, tipo_atendimento, data_inicio, data_fim,
        minutos_reais, minutos_faturados, is_fora_horario, descricao_trabalho
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        id,
        payload.tecnico_nome,
        payload.tipo_atendimento,
        dt_inicio.strftime("%Y-%m-%d %H:%M:%S"),
        dt_fim.strftime("%Y-%m-%d %H:%M:%S"),
        diff_minutos,
        minutos_faturados,
        is_fora,
        payload.descricao_trabalho
    ))

    # Recalcula totais do chamado
    cursor.execute("""
    SELECT SUM(minutos_reais), SUM(minutos_faturados)
    FROM apontamentos_horas WHERE chamado_id = ?
    """, (id,))
    totais = cursor.fetchone()
    tot_reais = totais[0] or 0
    tot_faturados = totais[1] or 0

    cursor.execute("""
    UPDATE chamados
    SET total_minutos_reais = ?, total_minutos_faturados = ?
    WHERE id = ?
    """, (tot_reais, tot_faturados, id))

    conn.commit()
    conn.close()

    return {
        "message": "Apontamento registrado com sucesso",
        "minutos_reais": diff_minutos,
        "minutos_faturados": minutos_faturados,
        "is_fora_horario": is_fora
    }

# --- Gestão de Ativos (Anexo I) ---
@app.get("/api/ativos")
def list_ativos(categoria: Optional[str] = None, unidade: Optional[str] = None, cliente_id: Optional[int] = None):
    conn = database.get_connection()
    cursor = conn.cursor()

    query = """
    SELECT a.*, COUNT(c.id) as total_chamados, cl.nome_razao_social as cliente_nome
    FROM ativos a
    LEFT JOIN chamados c ON a.id = c.ativo_id
    LEFT JOIN clientes cl ON a.cliente_id = cl.id
    WHERE 1=1
    """
    params = []
    if cliente_id:
        query += " AND a.cliente_id = ?"
        params.append(cliente_id)
    if categoria and categoria != "Todas":
        query += " AND a.categoria = ?"
        params.append(categoria)
    if unidade and unidade != "Todas":
        query += " AND a.unidade = ?"
        params.append(unidade)

    query += " GROUP BY a.id ORDER BY a.categoria ASC, a.identificador ASC"
    cursor.execute(query, params)
    ativos = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return ativos

@app.post("/api/ativos")
def create_ativo(payload: models.AtivoCreate):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO ativos (cliente_id, categoria, identificador, descricao, localizacao_setor, unidade, ip_rede, observacoes, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.cliente_id or 1,
        payload.categoria, payload.identificador, payload.descricao,
        payload.localizacao_setor, payload.unidade, payload.ip_rede,
        payload.observacoes, payload.status
    ))
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    return {"id": novo_id, "message": "Ativo cadastrado com sucesso"}

# --- Rotinas de Backup e Preventiva ---
@app.get("/api/rotinas")
def list_rotinas(mes_ano: Optional[str] = None, cliente_id: Optional[int] = None):
    conn = database.get_connection()
    cursor = conn.cursor()
    query = """
    SELECT r.*, cl.nome_razao_social as cliente_nome 
    FROM rotinas_backup_preventiva r 
    LEFT JOIN clientes cl ON r.cliente_id = cl.id 
    WHERE 1=1
    """
    params = []
    if cliente_id:
        query += " AND r.cliente_id = ?"
        params.append(cliente_id)
    if mes_ano:
        query += " AND r.mes_ano = ?"
        params.append(mes_ano)
    query += " ORDER BY r.mes_ano DESC, r.data_execucao DESC"
    cursor.execute(query, params)
    rotinas = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rotinas

@app.post("/api/rotinas")
def create_or_update_rotina(payload: models.RotinaCreate):
    conn = database.get_connection()
    cursor = conn.cursor()

    c_id = payload.cliente_id or 1
    # Verifica se já existe registro desse tipo no mesmo mês e cliente
    cursor.execute("SELECT id FROM rotinas_backup_preventiva WHERE mes_ano = ? AND tipo_rotina = ? AND cliente_id = ?", (payload.mes_ano, payload.tipo_rotina, c_id))
    existente = cursor.fetchone()

    if existente:
        cursor.execute("""
        UPDATE rotinas_backup_preventiva
        SET data_execucao = ?, status = 'Concluído', responsavel_cliente = ?,
            detalhes_execucao = ?, backup_nuvem_ok = ?, backup_hd_externo_ok = ?,
            espaco_disco_ok = ?, antivirus_ok = ?, observacoes = ?
        WHERE id = ?
        """, (
            payload.data_execucao, payload.responsavel_cliente, payload.detalhes_execucao,
            1 if payload.backup_nuvem_ok else 0, 1 if payload.backup_hd_externo_ok else 0,
            1 if payload.espaco_disco_ok else 0, 1 if payload.antivirus_ok else 0,
            payload.observacoes, existente["id"]
        ))
    else:
        cursor.execute("""
        INSERT INTO rotinas_backup_preventiva (
            cliente_id, mes_ano, tipo_rotina, data_execucao, status, responsavel_cliente,
            detalhes_execucao, backup_nuvem_ok, backup_hd_externo_ok,
            espaco_disco_ok, antivirus_ok, observacoes
        ) VALUES (?, ?, ?, ?, 'Concluído', ?, ?, ?, ?, ?, ?, ?)
        """, (
            c_id, payload.mes_ano, payload.tipo_rotina, payload.data_execucao,
            payload.responsavel_cliente, payload.detalhes_execucao,
            1 if payload.backup_nuvem_ok else 0, 1 if payload.backup_hd_externo_ok else 0,
            1 if payload.espaco_disco_ok else 0, 1 if payload.antivirus_ok else 0,
            payload.observacoes
        ))

    conn.commit()
    conn.close()
    return {"message": "Rotina registrada com sucesso"}

# --- Relatório em PDF Oficial ---
@app.get("/api/relatorio/pdf")
def download_relatorio_pdf(mes_ano: str = Query(default=None), cliente_id: Optional[int] = Query(default=None)):
    if not mes_ano:
        mes_ano = datetime.now().strftime("%Y-%m")

    # Monta payload consolidado para o cliente
    dash_data = get_dashboard(mes_ano, cliente_id=cliente_id)
    config = dash_data["config"]

    conn = database.get_connection()
    cursor = conn.cursor()
    query = """
    SELECT c.*, a.identificador as ativo_identificador
    FROM chamados c
    LEFT JOIN ativos a ON c.ativo_id = a.id
    WHERE strftime('%Y-%m', c.data_abertura) = ?
    """
    params = [mes_ano]
    if cliente_id:
        query += " AND c.cliente_id = ?"
        params.append(cliente_id)
    query += " ORDER BY c.data_abertura ASC"
    cursor.execute(query, params)
    chamados = [dict(r) for r in cursor.fetchall()]
    conn.close()

    dados_relatorio = {
        "mes_ano": mes_ano,
        "contratante_nome": config["contratante_nome"],
        "contratante_cnpj": config["contratante_cnpj"],
        "contratante_endereco": config["contratante_endereco"],
        "contratado_nome": config["contratado_nome"],
        "contratado_cpf": config["contratado_cpf"],
        "contratado_telefone": config["contratado_telefone"],
        "contratado_pix": config["contratado_pix"],
        "dia_vencimento": config["dia_vencimento"],
        "valor_mensal": config["valor_mensal"],
        "valor_hora_excedente": config["valor_hora_excedente"],
        "valor_hora_urgente_extra": config["valor_hora_urgente_extra"],
        "minutos_franquia_utilizados": dash_data["franquia"]["minutos_usados"],
        "minutos_excedentes_comercial": dash_data["franquia"]["minutos_excedentes_comercial"],
        "minutos_urgente_fora_horario": dash_data["franquia"]["minutos_urgente_fora_horario"],
        "backup_ok": dash_data["rotinas"]["backup_servidores_ok"],
        "preventiva_ok": dash_data["rotinas"]["preventiva_ok"],
        "chamados": chamados,
        "rotinas": dash_data["rotinas"]["itens"]
    }

    pdf_buffer = pdf_generator.gerar_relatorio_mensal_pdf(dados_relatorio)
    safe_name = config["contratante_nome"].replace(" ", "_")[:20]
    filename = f"Relatorio_Mensal_TI_{mes_ano.replace('-', '_')}_{safe_name}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

# --- Gerador de Link WhatsApp (Cláusula 16.4) ---
@app.get("/api/whatsapp-link")
def gerar_link_whatsapp(chamado_id: int, destinatario: str = "cliente"):
    """
    destinatario: 'celijane', 'elem', ou 'tecnico'
    """
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, a.identificador as ativo_identificador, cl.nome_razao_social as cliente_nome
    FROM chamados c
    LEFT JOIN ativos a ON c.ativo_id = a.id
    LEFT JOIN clientes cl ON c.cliente_id = cl.id
    WHERE c.id = ?
    """, (chamado_id,))
    chamado = cursor.fetchone()
    conn.close()

    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    chamado = dict(chamado)

    # Telefones oficiais
    if destinatario == "celijane":
        telefone = "5599981343989"
    elif destinatario == "elem":
        telefone = "5599981527346"
    else: # tecnico
        telefone = "5599981383157"

    status_icon = "🔵" if chamado["status"] == "Aberto" else ("🟡" if chamado["status"] == "Em Atendimento" else "🟢")
    cliente_txt = chamado.get("cliente_nome") or "Francisco S Silva Comércio Atacadista"

    texto = (
        f"*SUPORTE TÉCNICO TI - ATUALIZAÇÃO DE CHAMADO*\n"
        f"🏢 *Cliente:* {cliente_txt}\n"
        f"{status_icon} *Status:* {chamado['status']}\n"
        f"📄 *Protocolo:* {chamado['numero_protocolo']}\n"
        f"📍 *Unidade:* {chamado['unidade']}\n"
        f"👤 *Solicitante:* {chamado['solicitante_nome']}\n"
        f"📌 *Assunto:* {chamado['titulo']}\n"
        f"⚡ *Prioridade:* {chamado['prioridade']}\n"
        f"🛠️ *Modalidade:* {chamado['tipo_atendimento']}\n"
    )
    if chamado.get("solucao_tecnica"):
        texto += f"✅ *Solução/Parecer:* {chamado['solucao_tecnica']}\n"
    if chamado.get("total_minutos_faturados"):
        texto += f"⏱️ *Tempo Computado:* {chamado['total_minutos_faturados']} min\n"

    texto += f"\n_Atendimento técnico especializado - Raimundo Loiola Jr (MEI)_"

    url = f"https://api.whatsapp.com/send?phone={telefone}&text={urllib.parse.quote(texto)}"
    return {"url": url, "telefone": telefone, "texto": texto}

# --- Utilitário de Rede & Link para Cliente ---
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

@app.get("/api/rede-info")
def get_rede_info(cliente_id: Optional[int] = None):
    local_ip = get_local_ip()
    port = 8000
    conn = database.get_connection()
    cursor = conn.cursor()
    nome_empresa = "Francisco S Silva Comércio Atacadista"
    if cliente_id:
        cursor.execute("SELECT nome_razao_social FROM clientes WHERE id = ?", (cliente_id,))
        row = cursor.fetchone()
        if row:
            nome_empresa = row["nome_razao_social"]
    conn.close()

    cli_param = f"?cliente={cliente_id}" if cliente_id else ""
    msg_padrao = (
        f"Olá! Segue o link oficial para abertura de chamados técnicos de TI da {nome_empresa}:\n"
        f"🔗 http://{local_ip}:{port}/abrir-chamado{cli_param}\n\n"
        f"Basta clicar, relatar o problema e o chamado será registrado imediatamente na Central de Suporte."
    )
    return {
        "local_ip": local_ip,
        "port": port,
        "cliente_id": cliente_id,
        "url_local": f"http://localhost:{port}/abrir-chamado{cli_param}",
        "url_rede": f"http://{local_ip}:{port}/abrir-chamado{cli_param}",
        "url_admin": f"http://localhost:{port}/",
        "whatsapp_celijane_link": f"https://api.whatsapp.com/send?phone=5599981343989&text={urllib.parse.quote(msg_padrao)}",
        "whatsapp_elem_link": f"https://api.whatsapp.com/send?phone=5599981527346&text={urllib.parse.quote(msg_padrao)}",
        "mensagem_padrao": msg_padrao
    }

# Consulta pública de status por protocolo (para o cliente acompanhar)
@app.get("/api/chamados/protocolo/{protocolo}")
def get_chamado_por_protocolo(protocolo: str):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.numero_protocolo, c.titulo, c.descricao, c.solicitante_nome, c.unidade,
           c.setor, c.prioridade, c.tipo_atendimento, c.status, c.data_abertura,
           c.previsao_resposta, c.data_primeira_resposta, c.data_fechamento, c.solucao_tecnica,
           a.identificador as ativo_identificador
    FROM chamados c
    LEFT JOIN ativos a ON c.ativo_id = a.id
    WHERE UPPER(c.numero_protocolo) = UPPER(?)
    """, (protocolo.strip(),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado")
    return dict(row)

# Servir Frontend Estático
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

@app.get("/abrir-chamado")
@app.get("/portal-cliente")
def portal_cliente():
    return FileResponse(os.path.join(static_dir, "cliente.html"))

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
