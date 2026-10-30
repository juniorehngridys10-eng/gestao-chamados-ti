import os
import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import database
import models
import pdf_generator
from main import app

class TestSistemaChamadosContrato(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.init_db()
        cls.client = TestClient(app)

    def test_01_configuracao_contrato(self):
        """Verifica se os dados contratuais do PDF estão gravados fielmente"""
        res = self.client.get("/api/config")
        self.assertEqual(res.status_code, 200)
        cfg = res.json()
        self.assertEqual(cfg["contratante_nome"], "FRANCISCO S SILVA COMÉRCIO ATACADISTA")
        self.assertEqual(cfg["contratante_cnpj"], "05.309.054/0001-57")
        self.assertEqual(cfg["contratado_nome"], "RAIMUNDO FRANCISCO DE LOIOLA JUNIOR")
        self.assertEqual(cfg["contratado_pix"], "99981383157")
        self.assertEqual(cfg["valor_mensal"], 3500.00)
        self.assertEqual(cfg["franquia_horas_mensal"], 8.0)
        self.assertEqual(cfg["valor_hora_excedente"], 150.00)
        self.assertEqual(cfg["valor_hora_urgente_extra"], 225.00)
        self.assertEqual(cfg["dia_vencimento"], 5)

    def test_02_parque_tecnologico_anexo_i(self):
        """Verifica se os 46 equipamentos do Anexo I estão cadastrados"""
        res = self.client.get("/api/ativos")
        self.assertEqual(res.status_code, 200)
        ativos = res.json()
        self.assertGreaterEqual(len(ativos), 46)

        # Categorias obrigatórias
        categorias = [a["categoria"] for a in ativos]
        self.assertEqual(categorias.count("Servidor"), 2)
        self.assertEqual(categorias.count("Computador/Notebook"), 17)
        self.assertEqual(categorias.count("Impressora"), 7)
        self.assertEqual(categorias.count("Coletor de Dados"), 3)
        self.assertEqual(categorias.count("Switch de Rede"), 10)
        self.assertEqual(categorias.count("Roteador"), 7)
        self.assertEqual(categorias.count("Ponto de Wi-Fi"), 3)

    def test_03_regra_piso_minimo_tempo(self):
        """Cláusula 6.2: Atendimento remoto min 30 min, presencial min 60 min"""
        # Remoto com 10 min -> deve contar 30 min
        self.assertEqual(models.calcular_minutos_faturados("Remoto", 10), 30)
        # Remoto com 45 min -> deve contar 45 min
        self.assertEqual(models.calcular_minutos_faturados("Remoto", 45), 45)
        # Presencial com 25 min -> deve contar 60 min
        self.assertEqual(models.calcular_minutos_faturados("Presencial", 25), 60)
        # Presencial com 90 min -> deve contar 90 min
        self.assertEqual(models.calcular_minutos_faturados("Presencial", 90), 90)

    def test_04_regra_sla_clausula_6_4(self):
        """Cláusula 6.4: Urgente (2h/4h), Normal (4h/8h), Baixa (8h/2 dias)"""
        agora = datetime(2026, 10, 30, 9, 0, 0)
        resp_urg, conc_urg = models.calcular_sla("Urgente", "Remoto", agora)
        self.assertEqual(resp_urg, "2026-10-30 11:00:00")
        self.assertEqual(conc_urg, "2026-10-30 13:00:00")

        resp_norm, conc_norm = models.calcular_sla("Normal", "Remoto", agora)
        self.assertEqual(resp_norm, "2026-10-30 13:00:00")

    def test_05_fluxo_chamado_e_apontamento(self):
        """Cria chamado, aponta horas e valida cômputo faturado"""
        novo_chamado = {
            "titulo": "Teste Automatizado de Chamado",
            "descricao": "Falha na conexão do coletor com a rede Wi-Fi",
            "solicitante_nome": "Celijane",
            "solicitante_telefone": "(99) 98134-3989",
            "unidade": "Unidade BR 316",
            "setor": "Estoque",
            "prioridade": "Normal",
            "tipo_atendimento": "Remoto",
            "is_fora_escopo": False
        }
        res = self.client.post("/api/chamados", json=novo_chamado)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        ch_id = data["id"]
        protocolo = data["numero_protocolo"]
        self.assertTrue(protocolo.startswith("CHAM-"))

        # Adiciona apontamento remoto de 15 minutos (deve aplicar piso de 30 min)
        agora_str = datetime.now().strftime("%Y-%m-%d")
        apt = {
            "chamado_id": ch_id,
            "tipo_atendimento": "Remoto",
            "data_inicio": f"{agora_str} 10:00",
            "data_fim": f"{agora_str} 10:15",
            "descricao_trabalho": "Configuração do SSID nos coletores"
        }
        res_apt = self.client.post(f"/api/chamados/{ch_id}/apontamentos", json=apt)
        self.assertEqual(res_apt.status_code, 200)
        apt_data = res_apt.json()
        self.assertEqual(apt_data["minutos_reais"], 15)
        self.assertEqual(apt_data["minutos_faturados"], 30) # Piso da Cláusula 6.2

        # Verifica chamado atualizado
        res_ch = self.client.get(f"/api/chamados/{ch_id}")
        ch_detalhes = res_ch.json()
        self.assertEqual(ch_detalhes["total_minutos_faturados"], 30)

        # Atualiza status para Concluído
        res_update = self.client.put(f"/api/chamados/{ch_id}", json={
            "status": "Concluído",
            "solucao_tecnica": "Coletor reautenticado na rede 5GHz com sucesso."
        })
        self.assertEqual(res_update.status_code, 200)

    def test_06_dashboard_e_fechamento_mensal(self):
        """Testa consolidação do dashboard e cálculo financeiro"""
        res = self.client.get("/api/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("franquia", data)
        self.assertIn("financeiro", data)
        self.assertGreaterEqual(data["financeiro"]["valor_total"], 3500.00)

    def test_07_geracao_relatorio_pdf(self):
        """Testa geração e download do PDF oficial de fechamento"""
        res = self.client.get("/api/relatorio/pdf")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "application/pdf")
        self.assertGreater(len(res.content), 1000)

    def test_08_link_whatsapp(self):
        """Testa gerador de link para WhatsApp (Cláusula 16.4)"""
        res_chamados = self.client.get("/api/chamados")
        chamado_id = res_chamados.json()[0]["id"]
        res_wa = self.client.get(f"/api/whatsapp-link?chamado_id={chamado_id}&destinatario=celijane")
        self.assertEqual(res_wa.status_code, 200)
        data_wa = res_wa.json()
        self.assertIn("api.whatsapp.com/send", data_wa["url"])
        self.assertIn("5599981343989", data_wa["url"])

    def test_09_portal_cliente_e_rede(self):
        """Testa o portal público do cliente, rede info e busca por protocolo"""
        # Página do cliente
        res_pagina = self.client.get("/abrir-chamado")
        self.assertEqual(res_pagina.status_code, 200)
        self.assertIn("Central de Chamados TI", res_pagina.text)

        # Info de rede
        res_rede = self.client.get("/api/rede-info")
        self.assertEqual(res_rede.status_code, 200)
        rede = res_rede.json()
        self.assertIn("url_rede", rede)
        self.assertTrue(rede["url_rede"].endswith("/abrir-chamado"))

        # Busca por protocolo
        res_chamados = self.client.get("/api/chamados")
        protocolo = res_chamados.json()[0]["numero_protocolo"]
        res_cons = self.client.get(f"/api/chamados/protocolo/{protocolo}")
        self.assertEqual(res_cons.status_code, 200)
        cons = res_cons.json()
        self.assertEqual(cons["numero_protocolo"], protocolo)
        self.assertIn("status", cons)

    def test_10_crud_multi_clientes(self):
        """Testa o cadastro e gestão de múltiplos clientes e contratos"""
        # 1. Cadastra novo cliente
        novo_cli = {
            "nome_razao_social": "SUPERMERCADO BACABAL DISTRIBUIDORA LTDA",
            "nome_fantasia": "Supermercado Bacabal",
            "cnpj_cpf": "12.345.678/0001-90",
            "endereco_completo": "Av. Barão de Capanema, nº 500, Centro",
            "cidade": "Bacabal",
            "estado": "MA",
            "valor_mensal": 2800.00,
            "franquia_horas_mensal": 6.0,
            "valor_hora_excedente": 140.00,
            "valor_hora_urgente_extra": 210.00,
            "dia_vencimento": 10,
            "observacoes": "Contrato de suporte a 10 caixas PDV e 1 servidor."
        }
        res_post = self.client.post("/api/clientes", json=novo_cli)
        self.assertEqual(res_post.status_code, 200)
        cli_id = res_post.json()["id"]

        # 2. Lista clientes
        res_list = self.client.get("/api/clientes")
        self.assertEqual(res_list.status_code, 200)
        clientes = res_list.json()
        self.assertGreaterEqual(len(clientes), 2)

        # 3. Abre chamado para o novo cliente
        ch_cli = {
            "cliente_id": cli_id,
            "titulo": "Impressora do Caixa 03 parou de emitir cupom",
            "descricao": "Erro de comunicação serial",
            "solicitante_nome": "Marcos Caixa",
            "solicitante_telefone": "(99) 98888-7777",
            "unidade": "Loja Centro",
            "setor": "Frente de Caixa",
            "prioridade": "Normal",
            "tipo_atendimento": "Remoto"
        }
        res_ch = self.client.post("/api/chamados", json=ch_cli)
        self.assertEqual(res_ch.status_code, 200)

        # 4. Filtra chamados por esse cliente
        res_chamados_cli = self.client.get(f"/api/chamados?cliente_id={cli_id}")
        self.assertEqual(res_chamados_cli.status_code, 200)
        self.assertGreaterEqual(len(res_chamados_cli.json()), 1)

        # 5. Dashboard filtrado pelo cliente
        res_dash = self.client.get(f"/api/dashboard?cliente_id={cli_id}")
        self.assertEqual(res_dash.status_code, 200)
        dash_cli = res_dash.json()
        self.assertEqual(dash_cli["config"]["valor_mensal"], 2800.00)
        self.assertEqual(dash_cli["config"]["franquia_horas_mensal"], 6.0)

        # 6. Atualiza o cliente
        res_put = self.client.put(f"/api/clientes/{cli_id}", json={"valor_mensal": 3000.00})
        self.assertEqual(res_put.status_code, 200)

        # 7. Exclui o cliente de teste
        res_del = self.client.delete(f"/api/clientes/{cli_id}")
        self.assertEqual(res_del.status_code, 200)

if __name__ == "__main__":
    unittest.main()
