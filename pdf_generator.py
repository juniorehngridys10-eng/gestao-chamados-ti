import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

def gerar_relatorio_mensal_pdf(dados_mes: dict) -> io.BytesIO:
    """
    Gera o relatório mensal oficial em PDF com base nas cláusulas do contrato.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        alignment=1, # Centralizado
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        fontName='Helvetica'
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1E293B'),
        fontName='Helvetica-Bold',
        spaceBefore=8,
        spaceAfter=4
    )

    body_small = ParagraphStyle(
        'BodySmall',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#334155'),
        fontName='Helvetica'
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0F172A'),
        fontName='Helvetica-Bold'
    )

    story = []

    # Cabeçalho da Empresa
    story.append(Paragraph("RELATÓRIO MENSAL DE SERVIÇOS DE SUPORTE EM TI", title_style))
    story.append(Paragraph(f"Demonstrativo de Atividades e Fechamento de Franquia de Horas - Ref: {dados_mes.get('mes_ano', '10/2026')}", subtitle_style))
    story.append(Spacer(1, 0.4*cm))

    # Tabela com Dados das Partes (Contratante & Contratado)
    partes_data = [
        [
            Paragraph("<b>CONTRATANTE:</b><br/>"
                      f"<b>{dados_mes['contratante_nome']}</b><br/>"
                      f"CNPJ: {dados_mes['contratante_cnpj']}<br/>"
                      f"Endereço: {dados_mes['contratante_endereco']}<br/>"
                      f"Contatos: Celijane (99) 98134-3989 | D. Elem (99) 98152-7346", body_small),
            Paragraph("<b>CONTRATADO:</b><br/>"
                      f"<b>{dados_mes['contratado_nome']}</b><br/>"
                      f"CPF: {dados_mes['contratado_cpf']} | MEI Bacabal - MA<br/>"
                      f"WhatsApp: {dados_mes['contratado_telefone']}<br/>"
                      f"PIX para Pagamento: <b>{dados_mes['contratado_pix']}</b><br/>"
                      f"Vencimento: Dia {dados_mes['dia_vencimento']} do mês seguinte", body_small)
        ]
    ]
    t_partes = Table(partes_data, colWidths=[9.0*cm, 9.0*cm])
    t_partes.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_partes)
    story.append(Spacer(1, 0.4*cm))

    # Resumo do Escopo e Rotinas Contratuais (Cláusula 3.2, 3.3 e 11)
    story.append(Paragraph("1. ROTINAS PERIÓDICAS E MANUTENÇÕES DO CONTRATO", section_heading))
    rotinas_list = dados_mes.get("rotinas", [])
    backup_status = "Verificado e Conforme (HD Externo & Nuvem)" if dados_mes.get("backup_ok", True) else "Pendente / Em Revisão"
    prev_status = "Realizada (Limpeza, Atualizações e Antivírus)" if dados_mes.get("preventiva_ok", True) else "Pendente"

    rotinas_data = [
        [Paragraph("<b>Item / Rotina Obrigatória</b>", body_bold), 
         Paragraph("<b>Status no Mês</b>", body_bold), 
         Paragraph("<b>Observações Técnicas</b>", body_bold)],
        [Paragraph("Monitoramento & Backup de Servidores (Cl. 3.3 e 11)", body_small),
         Paragraph(f"<font color='green'><b>{backup_status}</b></font>", body_small),
         Paragraph("Verificação de bancos de dados, dumps e espaço em disco nos servidores SRV-01 e SRV-02.", body_small)],
        [Paragraph("Manutenção Preventiva Periódica (Cl. 3.2)", body_small),
         Paragraph(f"<font color='green'><b>{prev_status}</b></font>", body_small),
         Paragraph("Verificação nas 17 estações de trabalho e notebooks das Unidades BR 316 e Centro.", body_small)],
        [Paragraph("Parque Tecnológico Coberto (Anexo I)", body_small),
         Paragraph("<b>46 Ativos Cobertos</b>", body_small),
         Paragraph("17 PCs, 02 Servidores, 07 Impressoras, 03 Coletores, 10 Switches, 07 Roteadores, 03 APs Wi-Fi.", body_small)]
    ]
    t_rotinas = Table(rotinas_data, colWidths=[5.5*cm, 4.5*cm, 8.0*cm])
    t_rotinas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_rotinas)
    story.append(Spacer(1, 0.4*cm))

    # Tabela de Chamados Atendidos no Período
    story.append(Paragraph("2. REGISTRO DE ATENDIMENTOS E CHAMADOS NO MÊS", section_heading))
    chamados = dados_mes.get("chamados", [])
    
    if chamados:
        chamados_table_data = [
            [
                Paragraph("<b>Protocolo / Data</b>", body_bold),
                Paragraph("<b>Solicitante / Setor</b>", body_bold),
                Paragraph("<b>Descrição / Solução Técnica</b>", body_bold),
                Paragraph("<b>Modalidade</b>", body_bold),
                Paragraph("<b>Tempo Real</b>", body_bold),
                Paragraph("<b>Faturado*</b>", body_bold),
            ]
        ]
        for ch in chamados:
            tipo_mod = ch.get("tipo_atendimento", "Remoto")
            is_fora = ch.get("is_fora_horario", 0)
            tipo_txt = f"{tipo_mod}" + ("<br/><font color='red'>(Plantão)</font>" if is_fora else "")
            
            chamados_table_data.append([
                Paragraph(f"<b>{ch.get('numero_protocolo')}</b><br/>{ch.get('data_abertura')[:10]}", body_small),
                Paragraph(f"<b>{ch.get('solicitante_nome')}</b><br/>{ch.get('unidade')}<br/>{ch.get('setor', '')}", body_small),
                Paragraph(f"<b>{ch.get('titulo')}</b><br/><font color='#475569'>{ch.get('solucao_tecnica') or ch.get('descricao')}</font>", body_small),
                Paragraph(tipo_txt, body_small),
                Paragraph(f"{ch.get('total_minutos_reais', 0)} min", body_small),
                Paragraph(f"<b>{ch.get('total_minutos_faturados', 0)} min</b>", body_bold)
            ])
        
        t_chamados = Table(chamados_table_data, colWidths=[2.8*cm, 3.2*cm, 6.8*cm, 2.2*cm, 1.5*cm, 1.5*cm])
        t_chamados.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_chamados)
    else:
        story.append(Paragraph("<i>Nenhum chamado corretivo avulso registrado no período.</i>", body_small))

    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("<font size='7' color='#64748B'>* Cláusula 6.2: Atendimentos remotos têm cômputo mínimo de 30 minutos e presenciais de 60 minutos.</font>", body_small))
    story.append(Spacer(1, 0.4*cm))

    # Apuração de Horas & Faturamento (Cláusulas 6, 7 e 8)
    story.append(Paragraph("3. APURAÇÃO DE HORAS E DEMONSTRATIVO FINANCEIRO", section_heading))
    
    total_min_franquia = dados_mes.get("minutos_franquia_utilizados", 0)
    franquia_total_min = 8 * 60 # 480 minutos
    horas_franquia_txt = f"{total_min_franquia // 60:02d}h {total_min_franquia % 60:02d}m"
    
    saldo_min = max(0, franquia_total_min - total_min_franquia)
    saldo_txt = f"{saldo_min // 60:02d}h {saldo_min % 60:02d}m"
    
    min_excedentes_comercial = dados_mes.get("minutos_excedentes_comercial", 0)
    horas_excedentes_dec = min_excedentes_comercial / 60.0
    valor_excedentes = horas_excedentes_dec * dados_mes.get("valor_hora_excedente", 150.00)

    min_urgente_fora = dados_mes.get("minutos_urgente_fora_horario", 0)
    horas_urgente_dec = min_urgente_fora / 60.0
    valor_fora_horario = horas_urgente_dec * dados_mes.get("valor_hora_urgente_extra", 225.00)

    valor_fixo = dados_mes.get("valor_mensal", 3500.00)
    valor_total = valor_fixo + valor_excedentes + valor_fora_horario

    financeiro_data = [
        [Paragraph("<b>Item de Faturamento Contratual</b>", body_bold), 
         Paragraph("<b>Horas Apuradas</b>", body_bold), 
         Paragraph("<b>Regra / Cláusula</b>", body_bold),
         Paragraph("<b>Subtotal (R$)</b>", body_bold)],
        
        [Paragraph("Franquia Mensal Contratada", body_small), 
         Paragraph(f"8h 00m (Usadas: {horas_franquia_txt})", body_small), 
         Paragraph(f"Cláusula 6.1 (Saldo: {saldo_txt})", body_small),
         Paragraph(f"R$ {valor_fixo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), body_bold)],
        
        [Paragraph("Horas Excedentes (Horário Comercial)", body_small), 
         Paragraph(f"{min_excedentes_comercial // 60:02d}h {min_excedentes_comercial % 60:02d}m ({horas_excedentes_dec:.2f}h)", body_small), 
         Paragraph("Cláusula 6.3 - R$ 150,00/hora", body_small),
         Paragraph(f"R$ {valor_excedentes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), body_small)],
        
        [Paragraph("Horas Urgentes Fora do Horário (Plantão)", body_small), 
         Paragraph(f"{min_urgente_fora // 60:02d}h {min_urgente_fora % 60:02d}m ({horas_urgente_dec:.2f}h)", body_small), 
         Paragraph("Cláusula 7.3 - R$ 225,00/hora (+50%)", body_small),
         Paragraph(f"R$ {valor_fora_horario:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), body_small)],
        
        [Paragraph("<b>TOTAL A FATURAR NESTE MÊS</b>", body_bold), 
         Paragraph("-", body_small), 
         Paragraph(f"Vencimento: Dia {dados_mes.get('dia_vencimento', 5)}", body_small),
         Paragraph(f"<b>R$ {valor_total:,.2f}</b>".replace(",", "X").replace(".", ",").replace("X", "."), body_bold)]
    ]

    t_fin = Table(financeiro_data, colWidths=[6.5*cm, 4.0*cm, 4.5*cm, 3.0*cm])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#FEF08A')), # Highlight no total
    ]))
    story.append(t_fin)
    story.append(Spacer(1, 0.4*cm))

    # Instrução de Pagamento PIX
    pix_box_data = [
        [Paragraph(f"<b>DADOS PARA PAGAMENTO (CLÁUSULA 7.2):</b><br/>"
                   f"Forma: Transferência Bancária ou <b>PIX</b> | Chave PIX: <b>{dados_mes['contratado_pix']}</b> (Telefone)<br/>"
                   f"Favorecido: {dados_mes['contratado_nome']} | Emissão de Nota Fiscal NFS-e SIMEI (Cl. 7.6)", body_small)]
    ]
    t_pix = Table(pix_box_data, colWidths=[18.0*cm])
    t_pix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#94A3B8')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_pix)
    story.append(Spacer(1, 0.8*cm))

    # Assinaturas das Partes (Cláusula 9.4)
    sign_data = [
        [
            Paragraph("____________________________________________<br/>"
                      f"<b>{dados_mes['contratado_nome']}</b><br/>"
                      "Especialista em Suporte Técnico em TI<br/>"
                      f"CPF: {dados_mes['contratado_cpf']}", body_small),
            Paragraph("____________________________________________<br/>"
                      f"<b>{dados_mes['contratante_nome']}</b><br/>"
                      "De acordo / Visto da Administração<br/>"
                      f"CNPJ: {dados_mes['contratante_cnpj']}", body_small)
        ]
    ]
    t_sign = Table(sign_data, colWidths=[9.0*cm, 9.0*cm])
    t_sign.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    story.append(KeepTogether([t_sign]))

    doc.build(story)
    buffer.seek(0)
    return buffer
