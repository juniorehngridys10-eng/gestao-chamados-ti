from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta, time

# Modelo para configurações
class ContratoConfigModel(BaseModel):
    contratante_nome: str
    contratante_cnpj: str
    contratante_endereco: str
    contratado_nome: str
    contratado_cnpj: str
    contratado_cpf: str
    contratado_pix: str
    contratado_telefone: str
    valor_mensal: float = 3500.00
    franquia_horas_mensal: float = 8.0
    valor_hora_excedente: float = 150.00
    valor_hora_urgente_extra: float = 225.00
    horario_comercial_inicio: str = "08:00"
    horario_comercial_fim: str = "18:00"
    dia_vencimento: int = 5

class ClienteCreate(BaseModel):
    nome_razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj_cpf: Optional[str] = None
    endereco_completo: Optional[str] = None
    cidade: Optional[str] = "Bacabal"
    estado: Optional[str] = "MA"
    valor_mensal: float = 3500.00
    franquia_horas_mensal: float = 8.0
    valor_hora_excedente: float = 150.00
    valor_hora_urgente_extra: float = 225.00
    dia_vencimento: int = 5
    observacoes: Optional[str] = None
    status: Optional[str] = "Ativo"

class ClienteUpdate(BaseModel):
    nome_razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj_cpf: Optional[str] = None
    endereco_completo: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    valor_mensal: Optional[float] = None
    franquia_horas_mensal: Optional[float] = None
    valor_hora_excedente: Optional[float] = None
    valor_hora_urgente_extra: Optional[float] = None
    dia_vencimento: Optional[int] = None
    observacoes: Optional[str] = None
    status: Optional[str] = None

class ChamadoCreate(BaseModel):
    cliente_id: Optional[int] = 1
    titulo: str
    descricao: str
    solicitante_nome: str
    solicitante_telefone: Optional[str] = None
    unidade: str # Unidade BR 316 ou Unidade Centro
    setor: Optional[str] = None
    ativo_id: Optional[int] = None
    prioridade: str # Urgente, Normal, Baixa
    tipo_atendimento: str # Remoto, Presencial
    is_fora_escopo: bool = False
    observacao_escopo: Optional[str] = None

class ApontamentoCreate(BaseModel):
    chamado_id: int
    tipo_atendimento: str # Remoto, Presencial
    data_inicio: str # YYYY-MM-DD HH:MM
    data_fim: str # YYYY-MM-DD HH:MM
    tecnico_nome: Optional[str] = "Raimundo Loiola Junior"
    descricao_trabalho: Optional[str] = ""
    is_fora_horario_manual: Optional[bool] = None

class ChamadoUpdateStatus(BaseModel):
    status: str # Aberto, Em Atendimento, Aguardando Cliente/Peça, Concluído, Cancelado
    solucao_tecnica: Optional[str] = None

class AtivoCreate(BaseModel):
    cliente_id: Optional[int] = 1
    categoria: str
    identificador: str
    descricao: str
    localizacao_setor: str
    unidade: str
    ip_rede: Optional[str] = "-"
    observacoes: Optional[str] = None
    status: Optional[str] = "Operacional"

class RotinaCreate(BaseModel):
    cliente_id: Optional[int] = 1
    mes_ano: str
    tipo_rotina: str # Backup Servidores ou Preventiva Parque Tecnológico
    data_execucao: str
    responsavel_cliente: str
    detalhes_execucao: str
    backup_nuvem_ok: bool = True
    backup_hd_externo_ok: bool = True
    espaco_disco_ok: bool = True
    antivirus_ok: bool = True
    observacoes: Optional[str] = None

# Funções Auxiliares de Regras Contratuais

def is_horario_comercial(dt: datetime) -> bool:
    """
    Cláusula 5.1: Segunda a sexta-feira, das 08:00 às 18:00, exceto feriados.
    Retorna True se for horário comercial regular.
    """
    # 0 = segunda, 4 = sexta, 5 = sábado, 6 = domingo
    if dt.weekday() >= 5:
        return False
    
    hora_atual = dt.time()
    hora_inicio = time(8, 0)
    hora_fim = time(18, 0)
    
    return hora_inicio <= hora_atual < hora_fim

def calcular_sla(prioridade: str, tipo_atendimento: str, dt_abertura: datetime):
    """
    Cláusula 6.4:
    - Urgente (servidor parado, rede fora do ar ou paralisação total):
      1ª resposta/diagnóstico remoto em até 02 horas; presencial até 04 horas úteis.
    - Normal (falha em estação, coletor ou impressora):
      1ª resposta em até 04 horas úteis.
    - Baixa prioridade:
      atendimento em até 02 dias úteis.
    """
    if prioridade == "Urgente":
        previsao_resposta = dt_abertura + timedelta(hours=2)
        previsao_conclusao = dt_abertura + timedelta(hours=4)
    elif prioridade == "Normal":
        previsao_resposta = dt_abertura + timedelta(hours=4)
        previsao_conclusao = dt_abertura + timedelta(hours=8)
    else: # Baixa
        previsao_resposta = dt_abertura + timedelta(hours=8)
        previsao_conclusao = dt_abertura + timedelta(days=2)
        
    return previsao_resposta.strftime("%Y-%m-%d %H:%M:%S"), previsao_conclusao.strftime("%Y-%m-%d %H:%M:%S")

def calcular_minutos_faturados(tipo_atendimento: str, minutos_reais: int) -> int:
    """
    Cláusula 6.2:
    - Atendimento remoto: contagem mínima de 30 (trinta) minutos.
    - Deslocamento/visita presencial: contagem mínima de 01 (uma) hora (60 minutos).
    """
    if minutos_reais <= 0:
        return 0
        
    if tipo_atendimento.lower() == "remoto":
        return max(30, minutos_reais)
    else: # Presencial
        return max(60, minutos_reais)
