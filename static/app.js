// Estado Global da Aplicação
let mesAnoAtual = "";
let chamadoSelecionadoId = null;
let clienteSelecionadoId = ""; // vazio = todos / padrão, ou ID numérico
let listaClientesGlobal = [];
let listaAtivosGlobal = [];
let contatosGlobais = [];

document.addEventListener("DOMContentLoaded", () => {
  // Inicializa mês atual no seletor (YYYY-MM)
  const agora = new Date();
  const ano = agora.getFullYear();
  const mes = String(agora.getMonth() + 1).padStart(2, "0");
  mesAnoAtual = `${ano}-${mes}`;
  
  const filtroMes = document.getElementById("filtro-mes-ano");
  if (filtroMes) filtroMes.value = mesAnoAtual;

  const rotMes = document.getElementById("rot-mes");
  if (rotMes) rotMes.value = mesAnoAtual;

  const rotData = document.getElementById("rot-data");
  if (rotData) rotData.value = agora.toISOString().split("T")[0];

  verificarHorarioComercial();
  setInterval(verificarHorarioComercial, 60000);

  carregarClientes().then(() => {
    carregarTudo();
  });
});

// Toggle Sidebar no Mobile
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebar-overlay");
  if (!sidebar || !overlay) return;

  const isOpen = !sidebar.classList.contains("-translate-x-full");
  if (isOpen) {
    sidebar.classList.add("-translate-x-full");
    overlay.classList.add("hidden");
  } else {
    sidebar.classList.remove("-translate-x-full");
    overlay.classList.remove("hidden");
  }
}

// Verifica se está dentro do horário comercial (Seg-Sex 08:00 às 18:00)
function verificarHorarioComercial() {
  const agora = new Date();
  const diaSemana = agora.getDay(); // 0 = Domingo, 6 = Sábado
  const hora = agora.getHours();
  const isComercial = (diaSemana >= 1 && diaSemana <= 5) && (hora >= 8 && hora < 18);

  const txtSidebar = document.getElementById("txt-horario-sidebar");
  const avisoModal = document.getElementById("aviso-horario-modal");

  if (isComercial) {
    if (txtSidebar) txtSidebar.textContent = "Horário Comercial (08h às 18h)";
    if (avisoModal) {
      avisoModal.className = "p-3 rounded-lg border text-xs bg-emerald-50 border-emerald-200 text-emerald-900";
      avisoModal.innerHTML = `<strong><i class="fa-solid fa-clock text-emerald-600 mr-1"></i> Abertura em Horário Comercial (Seg-Sex 08h às 18h)</strong><br/>
      <span class="text-[11px] text-emerald-700">Atendimento regular descontado da franquia contratual.</span>`;
    }
  } else {
    if (txtSidebar) txtSidebar.textContent = "Fora de Horário (Plantão)";
    if (avisoModal) {
      avisoModal.className = "p-3 rounded-lg border text-xs bg-amber-50 border-amber-300 text-amber-950";
      avisoModal.innerHTML = `<strong><i class="fa-solid fa-triangle-exclamation text-amber-600 mr-1"></i> ATENÇÃO: Fora do Horário Comercial (Cláusula 5.3 e 7.3)</strong><br/>
      <span class="text-[11px] text-amber-800">Atendimentos de urgência fora do horário não descontam da franquia e têm adicional de 50%.</span>`;
    }
  }
}

// Navegação de Abas
function trocarAba(abaId) {
  const abas = ["dashboard", "chamados", "clientes", "ativos", "preventivas", "faturamento", "regras"];
  abas.forEach(id => {
    const view = document.getElementById(`view-${id}`);
    const tabBtn = document.getElementById(`tab-${id}`);
    if (view && tabBtn) {
      if (id === abaId) {
        view.classList.remove("hidden");
        tabBtn.className = "tab-btn active-tab w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition text-left text-white font-semibold";
      } else {
        view.classList.add("hidden");
        tabBtn.className = "tab-btn w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition text-left text-slate-400 hover:text-white hover:bg-slate-800/60 font-medium";
      }
    }
  });

  // Fecha sidebar no mobile ao clicar em um item
  if (window.innerWidth < 1024) {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    if (sidebar) sidebar.classList.add("-translate-x-full");
    if (overlay) overlay.classList.add("hidden");
  }

  if (abaId === "chamados") carregarChamados();
  if (abaId === "clientes") renderizarClientesGrid();
  if (abaId === "ativos") carregarAtivos();
  if (abaId === "preventivas") carregarRotinas();
  if (abaId === "faturamento") carregarFaturamento();
}

// ==============================================
// GESTÃO DE CLIENTES & CONTRATOS (MULTI-CLIENTE)
// ==============================================

async function carregarClientes() {
  try {
    const res = await fetch("/api/clientes");
    listaClientesGlobal = await res.json();

    // Atualiza badge de clientes na sidebar
    const badgeCli = document.getElementById("badge-total-clientes");
    if (badgeCli) badgeCli.textContent = listaClientesGlobal.length;

    // Popula Seletor Global de Clientes na Sidebar
    const seletor = document.getElementById("seletor-cliente-global");
    if (seletor) {
      let html = `<option value="">🏢 Todos os Clientes (${listaClientesGlobal.length})</option>`;
      listaClientesGlobal.forEach(c => {
        html += `<option value="${c.id}">${c.nome_fantasia || c.nome_razao_social}</option>`;
      });
      seletor.innerHTML = html;
      if (clienteSelecionadoId) seletor.value = clienteSelecionadoId;
    }

    // Popula selects de clientes nos modais
    popularSelectsCliente();

    // Atualiza o grid de clientes
    renderizarClientesGrid();

  } catch (e) {
    console.error("Erro ao carregar clientes:", e);
  }
}

function popularSelectsCliente() {
  const selects = ["chamado-cliente-id", "ativo-cliente-id", "rot-cliente-id"];
  selects.forEach(selId => {
    const el = document.getElementById(selId);
    if (!el) return;
    let html = "";
    listaClientesGlobal.forEach(c => {
      html += `<option value="${c.id}">${c.nome_fantasia || c.nome_razao_social}</option>`;
    });
    el.innerHTML = html;
    if (clienteSelecionadoId) el.value = clienteSelecionadoId;
  });
}

function aoMudarClienteGlobal() {
  const sel = document.getElementById("seletor-cliente-global");
  if (!sel) return;
  clienteSelecionadoId = sel.value;
  atualizarCabecalhoCliente();
  carregarTudo();
}

function selecionarCliente(id) {
  clienteSelecionadoId = id ? String(id) : "";
  const sel = document.getElementById("seletor-cliente-global");
  if (sel) sel.value = clienteSelecionadoId;
  atualizarCabecalhoCliente();
  trocarAba("dashboard");
  carregarTudo();
}

function atualizarCabecalhoCliente() {
  const topNome = document.getElementById("top-cliente-nome");
  const topStatus = document.getElementById("top-cliente-status");
  const topSub = document.getElementById("top-cliente-sub");

  if (!clienteSelecionadoId) {
    if (topNome) topNome.textContent = "VISÃO CONSOLIDADA • TODOS OS CLIENTES";
    if (topStatus) {
      topStatus.className = "text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-semibold";
      topStatus.textContent = `${listaClientesGlobal.length} Clientes Ativos`;
    }
    if (topSub) topSub.textContent = "Exibindo métricas e chamados somados de toda a carteira de TI";
  } else {
    const cli = listaClientesGlobal.find(c => String(c.id) === String(clienteSelecionadoId));
    if (cli) {
      if (topNome) topNome.textContent = cli.nome_razao_social;
      if (topStatus) {
        topStatus.className = "text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-semibold";
        topStatus.textContent = `Contrato ${cli.status}`;
      }
      if (topSub) {
        topSub.textContent = `${cli.cidade || 'Bacabal'} - ${cli.estado || 'MA'} • Franquia ${cli.franquia_horas_mensal}h / R$ ${cli.valor_mensal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
      }
    }
  }
}

function renderizarClientesGrid() {
  const grid = document.getElementById("grid-clientes");
  if (!grid) return;

  if (!listaClientesGlobal || listaClientesGlobal.length === 0) {
    grid.innerHTML = `<div class="col-span-3 text-center py-8 text-slate-400">Nenhum cliente cadastrado.</div>`;
    return;
  }

  grid.innerHTML = listaClientesGlobal.map(cli => {
    const isAtivo = cli.status === "Ativo";
    const statusClass = isAtivo ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800";
    const isPrincipal = cli.id === 1;

    return `
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-col justify-between hover:border-blue-400 transition">
        <div>
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-2.5">
              <div class="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center text-lg font-bold">
                <i class="fa-solid fa-building"></i>
              </div>
              <div>
                <h3 class="font-bold text-slate-900 text-xs sm:text-sm leading-tight">${cli.nome_fantasia || cli.nome_razao_social}</h3>
                <span class="text-[11px] text-slate-400 font-medium">${cli.cnpj_cpf || 'Sem CNPJ'}</span>
              </div>
            </div>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${statusClass}">${cli.status}</span>
          </div>

          <div class="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs space-y-1.5 mb-3">
            <div class="flex justify-between">
              <span class="text-slate-500">Valor Mensal:</span>
              <strong class="text-emerald-700 font-bold">R$ ${cli.valor_mensal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</strong>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Franquia Contratada:</span>
              <strong class="text-slate-800 font-semibold">${cli.franquia_horas_mensal} horas / mês</strong>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Hora Extra Comercial:</span>
              <span class="text-slate-700">R$ ${cli.valor_hora_excedente.toFixed(2)}/h</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Plantão / Fora Horário:</span>
              <span class="text-amber-700 font-medium">R$ ${cli.valor_hora_urgente_extra.toFixed(2)}/h</span>
            </div>
            <div class="flex justify-between border-t border-slate-200/60 pt-1">
              <span class="text-slate-500">Vencimento:</span>
              <span class="font-semibold text-slate-800">Todo dia ${cli.dia_vencimento}</span>
            </div>
          </div>

          <div class="text-[11px] text-slate-500 space-y-0.5">
            <div><strong>Cidade:</strong> ${cli.cidade || 'Bacabal'} - ${cli.estado || 'MA'}</div>
            ${cli.endereco_completo ? `<div><strong>Endereço:</strong> ${cli.endereco_completo}</div>` : ''}
            <div class="flex space-x-3 text-slate-600 mt-2 font-medium">
              <span><i class="fa-solid fa-ticket text-blue-500 mr-1"></i> ${cli.total_chamados || 0} chamados</span>
              <span><i class="fa-solid fa-server text-emerald-500 mr-1"></i> ${cli.total_ativos || 0} ativos</span>
            </div>
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          <div class="flex items-center space-x-1.5">
            <button onclick="selecionarCliente(${cli.id})" class="bg-blue-600 hover:bg-blue-500 text-white px-2.5 py-1.5 rounded-lg font-semibold text-[11px] transition shadow-sm">
              Selecionar
            </button>
            <button onclick="abrirModalLinkClientePara(${cli.id})" title="Link de Abertura para este cliente" class="bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-300 px-2 py-1.5 rounded-lg text-[11px] font-semibold transition">
              <i class="fa-solid fa-share-nodes"></i>
            </button>
          </div>

          <div class="flex items-center space-x-1">
            <button onclick="abrirModalEditarCliente(${cli.id})" class="p-1.5 text-slate-500 hover:text-blue-600 transition" title="Editar Contrato">
              <i class="fa-solid fa-pen-to-square"></i>
            </button>
            ${!isPrincipal ? `
            <button onclick="excluirCliente(${cli.id})" class="p-1.5 text-slate-400 hover:text-rose-600 transition" title="Excluir Cliente">
              <i class="fa-solid fa-trash-can"></i>
            </button>` : ''}
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function abrirModalNovoCliente() {
  document.getElementById("form-cliente").reset();
  document.getElementById("cli-edit-id").value = "";
  document.getElementById("modal-cliente-titulo").textContent = "Cadastrar Novo Cliente";
  document.getElementById("modal-cliente").classList.remove("hidden");
}

async function abrirModalEditarCliente(id) {
  try {
    const res = await fetch(`/api/clientes/${id}`);
    const cli = await res.json();

    document.getElementById("cli-edit-id").value = cli.id;
    document.getElementById("cli-razao").value = cli.nome_razao_social;
    document.getElementById("cli-fantasia").value = cli.nome_fantasia || "";
    document.getElementById("cli-cnpj").value = cli.cnpj_cpf || "";
    document.getElementById("cli-endereco").value = cli.endereco_completo || "";
    document.getElementById("cli-cidade").value = `${cli.cidade || 'Bacabal'} - ${cli.estado || 'MA'}`;
    document.getElementById("cli-val-mensal").value = cli.valor_mensal;
    document.getElementById("cli-franquia").value = cli.franquia_horas_mensal;
    document.getElementById("cli-val-extra").value = cli.valor_hora_excedente;
    document.getElementById("cli-val-plantao").value = cli.valor_hora_urgente_extra;
    document.getElementById("cli-vencimento").value = cli.dia_vencimento;
    document.getElementById("cli-status").value = cli.status || "Ativo";
    document.getElementById("cli-obs").value = cli.observacoes || "";

    document.getElementById("modal-cliente-titulo").textContent = `Editar Contrato: ${cli.nome_fantasia || cli.nome_razao_social}`;
    document.getElementById("modal-cliente").classList.remove("hidden");
  } catch (e) {
    console.error(e);
  }
}

function fecharModalCliente() {
  document.getElementById("modal-cliente").classList.add("hidden");
}

async function salvarCliente(e) {
  e.preventDefault();

  const editId = document.getElementById("cli-edit-id").value;
  const cidadeCompleta = document.getElementById("cli-cidade").value.split("-");
  const cidade = cidadeCompleta[0] ? cidadeCompleta[0].trim() : "Bacabal";
  const estado = cidadeCompleta[1] ? cidadeCompleta[1].trim() : "MA";

  const payload = {
    nome_razao_social: document.getElementById("cli-razao").value,
    nome_fantasia: document.getElementById("cli-fantasia").value,
    cnpj_cpf: document.getElementById("cli-cnpj").value,
    endereco_completo: document.getElementById("cli-endereco").value,
    cidade: cidade,
    estado: estado,
    valor_mensal: parseFloat(document.getElementById("cli-val-mensal").value) || 0,
    franquia_horas_mensal: parseFloat(document.getElementById("cli-franquia").value) || 0,
    valor_hora_excedente: parseFloat(document.getElementById("cli-val-extra").value) || 0,
    valor_hora_urgente_extra: parseFloat(document.getElementById("cli-val-plantao").value) || 0,
    dia_vencimento: parseInt(document.getElementById("cli-vencimento").value) || 5,
    status: document.getElementById("cli-status").value,
    observacoes: document.getElementById("cli-obs").value
  };

  try {
    let res;
    if (editId) {
      res = await fetch(`/api/clientes/${editId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch("/api/clientes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    if (res.ok) {
      fecharModalCliente();
      mostrarToast(editId ? "Cliente atualizado com sucesso!" : "Novo cliente cadastrado!");
      await carregarClientes();
      await carregarTudo();
    } else {
      alert("Erro ao salvar cliente.");
    }
  } catch (err) {
    console.error(err);
  }
}

async function excluirCliente(id) {
  if (!confirm("Tem certeza que deseja remover este cliente?")) return;
  try {
    const res = await fetch(`/api/clientes/${id}`, { method: "DELETE" });
    if (res.ok) {
      mostrarToast("Cliente removido.");
      if (clienteSelecionadoId == id) clienteSelecionadoId = "";
      await carregarClientes();
      await carregarTudo();
    } else {
      const data = await res.json();
      alert(data.detail || "Não foi possível remover.");
    }
  } catch (err) {
    console.error(err);
  }
}

// ==============================================
// CARREGAMENTO GERAL
// ==============================================

async function carregarTudo() {
  const filtroMes = document.getElementById("filtro-mes-ano");
  if (filtroMes) mesAnoAtual = filtroMes.value;

  // Atualiza link de PDF
  const btnPdf = document.getElementById("btn-gerar-pdf");
  if (btnPdf) {
    let pdfUrl = `/api/relatorio/pdf?mes_ano=${mesAnoAtual}`;
    if (clienteSelecionadoId) pdfUrl += `&cliente_id=${clienteSelecionadoId}`;
    btnPdf.href = pdfUrl;
  }

  await carregarAtivosSelect();
  await carregarDashboard();
  await carregarChamados();
  await carregarRotinas();
}

// Carrega Ativos para o select do Novo Chamado
async function carregarAtivosSelect() {
  try {
    let url = "/api/ativos";
    const cId = document.getElementById("chamado-cliente-id")?.value || clienteSelecionadoId;
    if (cId) url += `?cliente_id=${cId}`;

    const res = await fetch(url);
    listaAtivosGlobal = await res.json();
    const sel = document.getElementById("chamado-ativo-id");
    if (!sel) return;

    let html = `<option value="">Nenhum ativo específico / Suporte Geral a Usuário</option>`;
    const categorias = [...new Set(listaAtivosGlobal.map(a => a.categoria))];
    categorias.forEach(cat => {
      html += `<optgroup label="${cat}">`;
      listaAtivosGlobal.filter(a => a.categoria === cat).forEach(a => {
        html += `<option value="${a.id}">[${a.identificador}] ${a.descricao} (${a.localizacao_setor})</option>`;
      });
      html += `</optgroup>`;
    });

    sel.innerHTML = html;
  } catch (e) {
    console.error("Erro ao carregar ativos para select:", e);
  }
}

function aoMudarClienteNoChamado() {
  carregarAtivosSelect();
}

// Carrega Métricas do Dashboard
async function carregarDashboard() {
  try {
    let url = `/api/dashboard?mes_ano=${mesAnoAtual}`;
    if (clienteSelecionadoId) url += `&cliente_id=${clienteSelecionadoId}`;

    const res = await fetch(url);
    const data = await res.json();

    // Franquia de Horas
    const f = data.franquia;
    document.getElementById("dash-horas-usadas").textContent = f.horas_usadas_formatada;
    document.getElementById("dash-horas-saldo").textContent = f.horas_restantes_formatada;
    document.getElementById("dash-horas-total-label").textContent = `/ ${String(f.total_horas).padStart(2, '0')}h 00m`;
    document.getElementById("dash-percentual-franquia").textContent = `${f.percentual_uso}%`;
    document.getElementById("dash-franquia-tag").textContent = `${f.total_horas}h Inclusas`;

    const progressoEl = document.getElementById("dash-progresso-franquia");
    progressoEl.style.width = `${Math.min(100, f.percentual_uso)}%`;
    if (f.percentual_uso > 90) {
      progressoEl.className = "bg-rose-600 h-3 rounded-full transition-all duration-500";
    } else if (f.percentual_uso > 70) {
      progressoEl.className = "bg-amber-500 h-3 rounded-full transition-all duration-500";
    } else {
      progressoEl.className = "bg-blue-600 h-3 rounded-full transition-all duration-500";
    }

    // Faturamento
    const fin = data.financeiro;
    document.getElementById("dash-total-faturamento").textContent = fin.valor_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
    document.getElementById("dash-val-mensalidade-fixa").textContent = `R$ ${fin.valor_fixo.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
    document.getElementById("dash-qtd-horas-extras").textContent = `${f.horas_excedentes_comercial}h`;
    document.getElementById("dash-val-horas-extras").textContent = `R$ ${f.valor_excedentes.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
    document.getElementById("dash-qtd-horas-plantao").textContent = `${f.horas_urgente_fora_horario}h`;
    document.getElementById("dash-val-horas-plantao").textContent = `R$ ${f.valor_fora_horario.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
    document.getElementById("dash-vencimento-tag").textContent = `Venc. Dia ${fin.dia_vencimento || 5}`;

    // Contadores
    const c = data.contadores;
    document.getElementById("metric-abertos").textContent = c.abertos;
    document.getElementById("metric-em-atendimento").textContent = c.em_atendimento;
    document.getElementById("metric-urgentes").textContent = c.urgentes_ativos;
    document.getElementById("metric-concluidos").textContent = c.concluidos_mes;
    document.getElementById("badge-total-abertos").textContent = c.abertos + c.em_atendimento;

    // Obrigações Contratuais
    const rot = data.rotinas;
    const tagBackup = document.getElementById("status-backup-tag");
    const iconBackup = document.getElementById("icon-backup");
    if (rot.backup_servidores_ok) {
      tagBackup.className = "text-xs px-2 py-0.5 rounded-full font-semibold bg-emerald-100 text-emerald-800";
      tagBackup.textContent = "Conforme";
      iconBackup.className = "w-7 h-7 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-xs";
    } else {
      tagBackup.className = "text-xs px-2 py-0.5 rounded-full font-semibold bg-amber-100 text-amber-800";
      tagBackup.textContent = "Pendente";
      iconBackup.className = "w-7 h-7 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-xs";
    }

    const tagPrev = document.getElementById("status-preventiva-tag");
    const iconPrev = document.getElementById("icon-preventiva");
    if (rot.preventiva_ok) {
      tagPrev.className = "text-xs px-2 py-0.5 rounded-full font-semibold bg-emerald-100 text-emerald-800";
      tagPrev.textContent = "Realizada";
      iconPrev.className = "w-7 h-7 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-xs";
    } else {
      tagPrev.className = "text-xs px-2 py-0.5 rounded-full font-semibold bg-amber-100 text-amber-800";
      tagPrev.textContent = "Pendente";
      iconPrev.className = "w-7 h-7 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center text-xs";
    }

    renderizarTabelaChamados(data.ultimos_chamados, "tabela-dashboard-chamados", true);
    carregarFaturamento(data);

  } catch (e) {
    console.error("Erro ao carregar dashboard:", e);
  }
}

// Carrega Lista de Chamados com Filtros
async function carregarChamados() {
  try {
    const status = document.getElementById("filtro-status")?.value || "Todos";
    const prioridade = document.getElementById("filtro-prioridade")?.value || "Todas";
    const busca = document.getElementById("filtro-busca")?.value || "";

    let url = `/api/chamados?mes_ano=${mesAnoAtual}`;
    if (clienteSelecionadoId) url += `&cliente_id=${clienteSelecionadoId}`;
    if (status !== "Todos") url += `&status=${encodeURIComponent(status)}`;
    if (prioridade !== "Todas") url += `&prioridade=${encodeURIComponent(prioridade)}`;
    if (busca.trim()) url += `&busca=${encodeURIComponent(busca.trim())}`;

    const res = await fetch(url);
    const chamados = await res.json();
    renderizarTabelaChamados(chamados, "tabela-chamados-completa", false);
  } catch (e) {
    console.error("Erro ao carregar chamados:", e);
  }
}

function renderizarTabelaChamados(chamados, elementId, isResumida = false) {
  const tbody = document.getElementById(elementId);
  if (!tbody) return;

  if (!chamados || chamados.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-slate-400">Nenhum chamado encontrado.</td></tr>`;
    return;
  }

  tbody.innerHTML = chamados.map(ch => {
    let statusClass = "bg-slate-100 text-slate-700";
    if (ch.status === "Aberto") statusClass = "bg-amber-100 text-amber-800";
    if (ch.status === "Em Atendimento") statusClass = "bg-blue-100 text-blue-800";
    if (ch.status === "Concluído") statusClass = "bg-emerald-100 text-emerald-800";

    let prioridadeClass = "bg-slate-100 text-slate-700";
    if (ch.prioridade === "Urgente") prioridadeClass = "bg-rose-100 text-rose-800 font-bold";
    if (ch.prioridade === "Normal") prioridadeClass = "bg-sky-100 text-sky-800 font-medium";

    let slaBadge = "";
    if (ch.sla_estourado) {
      slaBadge = `<span class="inline-block mt-0.5 px-1.5 py-0.2 rounded text-[10px] bg-rose-600 text-white font-bold animate-pulse">SLA Vencido!</span>`;
    } else if (ch.sla_alerta) {
      slaBadge = `<span class="inline-block mt-0.5 px-1.5 py-0.2 rounded text-[10px] bg-amber-500 text-white font-bold">SLA &lt; 30m</span>`;
    }

    let modTxt = ch.tipo_atendimento;
    if (ch.is_fora_horario === 1) {
      modTxt += ` <span class="text-[10px] text-amber-700 font-bold bg-amber-100 px-1 rounded">(Plantão)</span>`;
    }

    let ativoTxt = ch.ativo_identificador ? `<span class="font-semibold text-slate-700">${ch.ativo_identificador}</span>` : `<span class="text-slate-400">Geral</span>`;

    return `
      <tr class="hover:bg-slate-50 transition cursor-pointer" onclick="abrirModalDetalhes(${ch.id})">
        <td class="py-3 px-4">
          <div class="font-mono font-bold text-blue-700">${ch.numero_protocolo}</div>
          <div class="text-[11px] text-slate-400">${ch.data_abertura ? ch.data_abertura.substring(0, 16) : '-'}</div>
        </td>
        <td class="py-3 px-4">
          <div class="font-bold text-slate-900">${ch.cliente_nome || 'Cliente'}</div>
          <div class="text-[11px] text-slate-600">${ch.solicitante_nome} (${ch.solicitante_telefone || '-'})</div>
        </td>
        ${!isResumida ? `
        <td class="py-3 px-4">
          <div class="font-medium text-slate-700">${ch.unidade}</div>
          <div class="text-[11px] text-slate-500">${ch.setor || '-'}</div>
        </td>` : ''}
        <td class="py-3 px-4">
          <div class="font-bold text-slate-800">${ch.titulo}</div>
          <div class="text-[11px] text-slate-500">Ativo: ${ativoTxt}</div>
        </td>
        <td class="py-3 px-4">
          <span class="px-2 py-0.5 rounded-full text-[11px] ${prioridadeClass}">${ch.prioridade}</span>
          ${slaBadge}
        </td>
        <td class="py-3 px-4">${modTxt}</td>
        <td class="py-3 px-4">
          <span class="font-bold text-slate-800">${ch.total_minutos_faturados || 0}m</span>
          <span class="text-[11px] text-slate-400">(${ch.total_minutos_reais || 0}m reais)</span>
        </td>
        <td class="py-3 px-4">
          <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold ${statusClass}">${ch.status}</span>
        </td>
        <td class="py-3 px-4 text-center" onclick="event.stopPropagation()">
          <div class="flex items-center justify-center space-x-1.5">
            <button onclick="abrirWhatsappRapido(${ch.id})" title="Enviar WhatsApp" class="p-1.5 text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50 rounded">
              <i class="fa-brands fa-whatsapp text-sm"></i>
            </button>
            <button onclick="abrirModalDetalhes(${ch.id})" title="Ver Detalhes" class="p-1.5 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded">
              <i class="fa-solid fa-arrow-up-right-from-square text-xs"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

// Carrega Ativos
async function carregarAtivos() {
  try {
    const categoria = document.getElementById("filtro-ativo-categoria")?.value || "Todas";
    let url = "/api/ativos";
    const params = [];
    if (clienteSelecionadoId) params.push(`cliente_id=${clienteSelecionadoId}`);
    if (categoria !== "Todas") params.push(`categoria=${encodeURIComponent(categoria)}`);
    if (params.length > 0) url += `?${params.join("&")}`;

    const res = await fetch(url);
    const ativos = await res.json();

    const grid = document.getElementById("grid-ativos");
    if (!grid) return;

    if (!ativos || ativos.length === 0) {
      grid.innerHTML = `<div class="col-span-3 text-center py-8 text-slate-400">Nenhum ativo cadastrado.</div>`;
      return;
    }

    grid.innerHTML = ativos.map(a => {
      let icon = "fa-desktop";
      if (a.categoria === "Servidor") icon = "fa-server";
      if (a.categoria === "Impressora") icon = "fa-print";
      if (a.categoria === "Coletor de Dados") icon = "fa-barcode";
      if (a.categoria === "Switch de Rede") icon = "fa-network-wired";
      if (a.categoria === "Roteador") icon = "fa-wifi";
      if (a.categoria === "Ponto de Wi-Fi") icon = "fa-tower-broadcast";

      return `
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex flex-col justify-between hover:border-blue-400 transition">
          <div>
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center space-x-2">
                <div class="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-sm">
                  <i class="fa-solid ${icon}"></i>
                </div>
                <div>
                  <h3 class="font-bold text-slate-900 text-xs">${a.identificador}</h3>
                  <span class="text-[10px] text-slate-400 font-medium">${a.categoria} • ${a.cliente_nome || ''}</span>
                </div>
              </div>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">${a.status}</span>
            </div>

            <p class="text-xs text-slate-700 font-medium mt-1">${a.descricao}</p>
            <div class="text-[11px] text-slate-500 mt-2 space-y-0.5">
              <div><strong>Setor:</strong> ${a.localizacao_setor}</div>
              <div><strong>Unidade:</strong> ${a.unidade}</div>
              ${a.ip_rede && a.ip_rede !== '-' ? `<div><strong>IP:</strong> <span class="font-mono">${a.ip_rede}</span></div>` : ''}
            </div>
          </div>

          <div class="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs">
            <span class="text-slate-400 text-[11px]">${a.total_chamados || 0} chamados</span>
            <button onclick="abrirChamadoParaAtivo(${a.id}, '${a.identificador}', '${a.unidade}', '${a.localizacao_setor}', ${a.cliente_id})" class="text-blue-600 hover:text-blue-800 font-semibold text-[11px] flex items-center space-x-1">
              <i class="fa-solid fa-plus text-[10px]"></i>
              <span>Abrir Chamado</span>
            </button>
          </div>
        </div>
      `;
    }).join("");

  } catch (e) {
    console.error("Erro ao carregar ativos:", e);
  }
}

// Carrega Rotinas
async function carregarRotinas() {
  try {
    let url = `/api/rotinas?mes_ano=${mesAnoAtual}`;
    if (clienteSelecionadoId) url += `&cliente_id=${clienteSelecionadoId}`;

    const res = await fetch(url);
    const rotinas = await res.json();

    const tbody = document.getElementById("tabela-rotinas");
    if (!tbody) return;

    if (!rotinas || rotinas.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-slate-400">Nenhuma verificação registrada para ${mesAnoAtual}.</td></tr>`;
      return;
    }

    tbody.innerHTML = rotinas.map(r => {
      const nuvemCheck = r.backup_nuvem_ok ? `<span class="text-emerald-700 mr-2"><i class="fa-solid fa-cloud"></i> Nuvem OK</span>` : '';
      const hdCheck = r.backup_hd_externo_ok ? `<span class="text-emerald-700 mr-2"><i class="fa-solid fa-hard-drive"></i> HD OK</span>` : '';
      const discoCheck = r.espaco_disco_ok ? `<span class="text-emerald-700 mr-2"><i class="fa-solid fa-database"></i> Disco OK</span>` : '';
      const avCheck = r.antivirus_ok ? `<span class="text-emerald-700"><i class="fa-solid fa-shield-virus"></i> Antivírus OK</span>` : '';

      return `
        <tr>
          <td class="py-3 px-4 font-mono font-bold text-slate-800">${r.mes_ano}</td>
          <td class="py-3 px-4 font-bold text-slate-900">${r.cliente_nome || '-'}</td>
          <td class="py-3 px-4 font-bold text-blue-700">${r.tipo_rotina}</td>
          <td class="py-3 px-4 text-slate-600">${r.data_execucao ? r.data_execucao.substring(0, 10) : '-'}</td>
          <td class="py-3 px-4">
            <div class="font-medium text-slate-800">${r.responsavel_tecnico}</div>
            <div class="text-[11px] text-slate-500">Visto: ${r.responsavel_cliente || 'Cliente'}</div>
          </td>
          <td class="py-3 px-4 text-[11px]">
            ${nuvemCheck} ${hdCheck} ${discoCheck} ${avCheck}
          </td>
          <td class="py-3 px-4">
            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">${r.status}</span>
          </td>
        </tr>
      `;
    }).join("");

  } catch (e) {
    console.error("Erro ao carregar rotinas:", e);
  }
}

// Carrega Faturamento Detalhado
async function carregarFaturamento(dashData = null) {
  try {
    if (!dashData) {
      let url = `/api/dashboard?mes_ano=${mesAnoAtual}`;
      if (clienteSelecionadoId) url += `&cliente_id=${clienteSelecionadoId}`;
      const res = await fetch(url);
      dashData = await res.json();
    }

    const f = dashData.franquia;
    const fin = dashData.financeiro;

    document.getElementById("fat-mensalidade-fixa").textContent = `R$ ${fin.valor_fixo.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
    document.getElementById("fat-horas-extras-qtd").textContent = `${f.horas_excedentes_comercial}h`;
    document.getElementById("fat-horas-extras-val").textContent = `R$ ${f.valor_excedentes.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
    document.getElementById("fat-horas-plantao-qtd").textContent = `${f.horas_urgente_fora_horario}h`;
    document.getElementById("fat-horas-plantao-val").textContent = `R$ ${f.valor_fora_horario.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
    document.getElementById("fat-total-geral").textContent = `R$ ${fin.valor_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
    document.getElementById("fat-dia-vencimento").textContent = `${fin.dia_vencimento || 5} do mês seguinte`;

  } catch (e) {
    console.error("Erro ao carregar faturamento:", e);
  }
}

// Novo Chamado
function abrirModalNovoChamado() {
  verificarHorarioComercial();
  document.getElementById("form-novo-chamado").reset();
  const cSel = document.getElementById("chamado-cliente-id");
  if (cSel && clienteSelecionadoId) cSel.value = clienteSelecionadoId;
  carregarAtivosSelect();
  document.getElementById("modal-novo-chamado").classList.remove("hidden");
}

function fecharModalNovoChamado() {
  document.getElementById("modal-novo-chamado").classList.add("hidden");
}

function abrirChamadoParaAtivo(ativoId, tag, unidade, setor, clienteId) {
  abrirModalNovoChamado();
  if (clienteId) {
    const cSel = document.getElementById("chamado-cliente-id");
    if (cSel) cSel.value = clienteId;
    carregarAtivosSelect();
  }
  document.getElementById("chamado-ativo-id").value = ativoId;
  document.getElementById("chamado-unidade").value = unidade;
  document.getElementById("chamado-setor").value = setor;
  document.getElementById("chamado-titulo").value = `Suporte em ${tag}`;
}

async function salvarNovoChamado(e) {
  e.preventDefault();

  const payload = {
    cliente_id: parseInt(document.getElementById("chamado-cliente-id").value) || 1,
    solicitante_nome: document.getElementById("chamado-solicitante").value,
    solicitante_telefone: document.getElementById("chamado-telefone").value,
    unidade: document.getElementById("chamado-unidade").value,
    setor: document.getElementById("chamado-setor").value,
    ativo_id: document.getElementById("chamado-ativo-id").value ? parseInt(document.getElementById("chamado-ativo-id").value) : null,
    prioridade: document.getElementById("chamado-prioridade").value,
    tipo_atendimento: document.getElementById("chamado-modalidade").value,
    titulo: document.getElementById("chamado-titulo").value,
    descricao: document.getElementById("chamado-descricao").value,
    is_fora_escopo: document.getElementById("chamado-fora-escopo").checked
  };

  try {
    const res = await fetch("/api/chamados", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      fecharModalNovoChamado();
      mostrarToast(`Chamado ${data.numero_protocolo} criado com sucesso!`);
      await carregarTudo();
      abrirModalDetalhes(data.id);
    } else {
      alert("Erro ao salvar chamado.");
    }
  } catch (err) {
    console.error(err);
  }
}

// Modal de Detalhes
async function abrirModalDetalhes(chamadoId) {
  chamadoSelecionadoId = chamadoId;
  try {
    const res = await fetch(`/api/chamados/${chamadoId}`);
    const ch = await res.json();

    document.getElementById("det-protocolo").textContent = ch.numero_protocolo;
    document.getElementById("det-titulo").textContent = ch.titulo;
    document.getElementById("det-solicitante").textContent = `${ch.solicitante_nome} (${ch.solicitante_telefone || '-'})`;
    document.getElementById("det-unidade").textContent = `${ch.unidade} - ${ch.setor || ''}`;
    document.getElementById("det-prioridade").textContent = ch.prioridade;
    document.getElementById("det-modalidade").textContent = ch.tipo_atendimento + (ch.is_fora_horario ? " (Fora de Horário)" : "");
    document.getElementById("det-descricao").textContent = ch.descricao;
    document.getElementById("det-total-horas").textContent = `${ch.total_minutos_faturados || 0} min (${ch.total_minutos_reais || 0} min reais)`;
    document.getElementById("det-status-select").value = ch.status;
    document.getElementById("det-solucao").value = ch.solucao_tecnica || "";

    const badge = document.getElementById("det-status-badge");
    badge.textContent = ch.status;
    if (ch.status === "Aberto") badge.className = "px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-100 text-amber-800";
    else if (ch.status === "Em Atendimento") badge.className = "px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-100 text-blue-800";
    else if (ch.status === "Concluído") badge.className = "px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800";
    else badge.className = "px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-800";

    const agora = new Date();
    const fimStr = agora.toISOString().substring(0, 16);
    const inicioD = new Date(agora.getTime() - 30 * 60000);
    const inicioStr = inicioD.toISOString().substring(0, 16);
    document.getElementById("apt-inicio").value = inicioStr;
    document.getElementById("apt-fim").value = fimStr;
    document.getElementById("apt-tipo").value = ch.tipo_atendimento;

    renderizarApontamentos(ch.apontamentos || []);
    document.getElementById("modal-detalhes-chamado").classList.remove("hidden");
  } catch (e) {
    console.error("Erro ao abrir detalhes:", e);
  }
}

function fecharModalDetalhes() {
  document.getElementById("modal-detalhes-chamado").classList.add("hidden");
}

function renderizarApontamentos(apontamentos) {
  const tbody = document.getElementById("tabela-apontamentos");
  if (!tbody) return;

  if (!apontamentos || apontamentos.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-slate-400">Nenhum tempo apontado neste chamado.</td></tr>`;
    return;
  }

  tbody.innerHTML = apontamentos.map(ap => {
    const isComercial = ap.is_fora_horario === 0 ? `<span class="text-emerald-700 font-semibold">Sim (Comercial)</span>` : `<span class="text-amber-700 font-semibold">Não (Plantão)</span>`;
    return `
      <tr>
        <td class="py-2 px-3">
          <div>${ap.data_inicio.substring(0, 16)}</div>
          <div class="text-[10px] text-slate-400">${ap.descricao_trabalho || ''}</div>
        </td>
        <td class="py-2 px-3 font-semibold">${ap.tipo_atendimento}</td>
        <td class="py-2 px-3 text-slate-500">${ap.minutos_reais} min</td>
        <td class="py-2 px-3 font-bold text-slate-800">${ap.minutos_faturados} min</td>
        <td class="py-2 px-3">${isComercial}</td>
      </tr>
    `;
  }).join("");
}

async function adicionarApontamento() {
  if (!chamadoSelecionadoId) return;

  const inicio = document.getElementById("apt-inicio").value;
  const fim = document.getElementById("apt-fim").value;
  const tipo = document.getElementById("apt-tipo").value;
  const desc = document.getElementById("apt-descricao").value;

  if (!inicio || !fim) {
    alert("Informe data e horário de início e término.");
    return;
  }

  try {
    const res = await fetch(`/api/chamados/${chamadoSelecionadoId}/apontamentos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chamado_id: chamadoSelecionadoId,
        tipo_atendimento: tipo,
        data_inicio: inicio.replace("T", " "),
        data_fim: fim.replace("T", " "),
        descricao_trabalho: desc
      })
    });

    if (res.ok) {
      mostrarToast("Horas apontadas e piso calculado!");
      document.getElementById("apt-descricao").value = "";
      await abrirModalDetalhes(chamadoSelecionadoId);
      await carregarDashboard();
    }
  } catch (err) {
    console.error(err);
  }
}

async function salvarAtualizacaoChamado() {
  if (!chamadoSelecionadoId) return;

  const status = document.getElementById("det-status-select").value;
  const solucao = document.getElementById("det-solucao").value;

  try {
    const res = await fetch(`/api/chamados/${chamadoSelecionadoId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: status, solucao_tecnica: solucao })
    });

    if (res.ok) {
      mostrarToast("Chamado atualizado com sucesso!");
      fecharModalDetalhes();
      await carregarTudo();
    }
  } catch (err) {
    console.error(err);
  }
}

async function excluirChamadoAtual() {
  if (!chamadoSelecionadoId) return;
  if (!confirm("Tem certeza que deseja excluir este chamado?")) return;

  try {
    const res = await fetch(`/api/chamados/${chamadoSelecionadoId}`, { method: "DELETE" });
    if (res.ok) {
      mostrarToast("Chamado excluído.");
      fecharModalDetalhes();
      await carregarTudo();
    }
  } catch (err) {
    console.error(err);
  }
}

// WhatsApp
async function abrirWhatsappRapido(chamadoId) {
  try {
    const res = await fetch(`/api/whatsapp-link?chamado_id=${chamadoId}&destinatario=cliente`);
    const data = await res.json();
    window.open(data.url, "_blank");
  } catch (e) {
    console.error(e);
  }
}

function enviarWhatsappChamado() {
  if (chamadoSelecionadoId) abrirWhatsappRapido(chamadoSelecionadoId);
}

// Modal Link para Cliente e QR Code
async function abrirModalLinkCliente() {
  abrirModalLinkClientePara(clienteSelecionadoId || 1);
}

async function abrirModalLinkClientePara(cliId) {
  try {
    let url = `/api/rede-info?cliente_id=${cliId}`;
    const res = await fetch(url);
    const data = await res.json();

    const linkInput = document.getElementById("link-cliente-input");
    if (linkInput) linkInput.value = data.url_rede;

    const btnCelijane = document.getElementById("btn-whats-celijane");
    if (btnCelijane) btnCelijane.href = data.whatsapp_celijane_link;

    const btnElem = document.getElementById("btn-whats-elem");
    if (btnElem) btnElem.href = data.whatsapp_elem_link;

    const sub = document.getElementById("link-cliente-sub");
    if (sub) {
      const cli = listaClientesGlobal.find(c => String(c.id) === String(cliId));
      sub.textContent = `Abertura exclusiva para: ${cli ? (cli.nome_fantasia || cli.nome_razao_social) : 'Cliente'}`;
    }

    const qrImg = document.getElementById("qr-code-img");
    if (qrImg) {
      qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(data.url_rede)}`;
    }

    document.getElementById("modal-link-cliente").classList.remove("hidden");
  } catch (e) {
    console.error("Erro ao carregar link:", e);
  }
}

function fecharModalLinkCliente() {
  document.getElementById("modal-link-cliente").classList.add("hidden");
}

function copiarLinkCliente() {
  const input = document.getElementById("link-cliente-input");
  if (!input) return;
  navigator.clipboard.writeText(input.value);
  mostrarToast("Link copiado! Envie no WhatsApp para seu cliente.");
}

function imprimirQrCode() {
  const link = document.getElementById("link-cliente-input")?.value || "";
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(link)}`;

  const win = window.open("", "_blank");
  win.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Cartaz de Abertura de Chamados TI</title>
      <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding: 40px; color: #1e293b; }
        .card { border: 3px solid #0f172a; border-radius: 20px; padding: 30px; max-width: 480px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { margin: 0 0 5px; font-size: 22px; color: #0f172a; }
        h2 { margin: 0 0 20px; font-size: 14px; color: #475569; font-weight: normal; }
        .qr-box { margin: 20px 0; }
        .qr-box img { width: 220px; height: 220px; }
        .link { font-family: monospace; font-size: 13px; font-weight: bold; background: #f1f5f9; padding: 8px 14px; border-radius: 8px; display: inline-block; word-break: break-all; }
        .instrucao { margin-top: 20px; font-size: 13px; color: #334155; line-height: 1.5; }
        .footer { margin-top: 25px; font-size: 11px; color: #64748b; border-top: 1px solid #cbd5e1; padding-top: 12px; }
      </style>
    </head>
    <body onload="window.print()">
      <div class="card">
        <h1>SUPORTE TÉCNICO EM TI</h1>
        <h2>CENTRAL DE ATENDIMENTO DE CHAMADOS</h2>
        <div class="qr-box">
          <img src="${qrUrl}" alt="QR Code">
        </div>
        <div class="instrucao">
          <strong>Precisa de Suporte em Computador, Impressora ou Rede?</strong><br>
          Aponte a câmera do celular para o QR Code acima ou acesse:<br>
          <div class="link" style="margin-top: 8px;">${link}</div>
        </div>
        <div class="footer">
          Especialista em TI: Raimundo Loiola Jr (MEI)<br>
          Atendimento Oficial Bacabal - MA
        </div>
      </div>
    </body>
    </html>
  `);
  win.document.close();
}

// Modal Rotinas e Ativos
function abrirModalNovaRotina() {
  const cSel = document.getElementById("rot-cliente-id");
  if (cSel && clienteSelecionadoId) cSel.value = clienteSelecionadoId;
  document.getElementById("modal-nova-rotina").classList.remove("hidden");
}

function fecharModalNovaRotina() {
  document.getElementById("modal-nova-rotina").classList.add("hidden");
}

async function salvarRotina(e) {
  e.preventDefault();

  const payload = {
    cliente_id: parseInt(document.getElementById("rot-cliente-id").value) || 1,
    tipo_rotina: document.getElementById("rot-tipo").value,
    mes_ano: document.getElementById("rot-mes").value,
    data_execucao: document.getElementById("rot-data").value,
    responsavel_cliente: document.getElementById("rot-cliente").value,
    backup_nuvem_ok: document.getElementById("chk-nuvem").checked,
    backup_hd_externo_ok: document.getElementById("chk-hd").checked,
    espaco_disco_ok: document.getElementById("chk-disco").checked,
    antivirus_ok: document.getElementById("chk-av").checked,
    detalhes_execucao: document.getElementById("rot-detalhes").value
  };

  try {
    const res = await fetch("/api/rotinas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      fecharModalNovaRotina();
      mostrarToast("Rotina registrada com sucesso!");
      await carregarTudo();
    }
  } catch (err) {
    console.error(err);
  }
}

function abrirModalNovoAtivo() {
  const cSel = document.getElementById("ativo-cliente-id");
  if (cSel && clienteSelecionadoId) cSel.value = clienteSelecionadoId;
  document.getElementById("modal-novo-ativo").classList.remove("hidden");
}

function fecharModalNovoAtivo() {
  document.getElementById("modal-novo-ativo").classList.add("hidden");
}

async function salvarNovoAtivo(e) {
  e.preventDefault();

  const payload = {
    cliente_id: parseInt(document.getElementById("ativo-cliente-id").value) || 1,
    categoria: document.getElementById("ativo-cat").value,
    identificador: document.getElementById("ativo-tag").value,
    unidade: document.getElementById("ativo-unidade").value,
    descricao: document.getElementById("ativo-desc").value,
    localizacao_setor: document.getElementById("ativo-setor").value,
    ip_rede: document.getElementById("ativo-ip").value || "-",
    observacoes: document.getElementById("ativo-obs").value
  };

  try {
    const res = await fetch("/api/ativos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      fecharModalNovoAtivo();
      mostrarToast("Ativo cadastrado no parque!");
      await carregarAtivos();
      await carregarAtivosSelect();
    }
  } catch (err) {
    console.error(err);
  }
}

function copiarPix() {
  navigator.clipboard.writeText("99981383157");
  mostrarToast("Chave PIX copiada: 99981383157");
}

function copiarMensagemFechamento() {
  const tot = document.getElementById("fat-total-geral").textContent;
  const hExt = document.getElementById("fat-horas-extras-qtd").textContent;
  const hPlt = document.getElementById("fat-horas-plantao-qtd").textContent;
  const cliNome = document.getElementById("top-cliente-nome").textContent;

  const msg = `*FECHAMENTO MENSAL DE SUPORTE EM TI*\n` +
    `Ref: ${mesAnoAtual} - ${cliNome}\n\n` +
    `⏱️ *Horas Extras Comerciais:* ${hExt}\n` +
    `⚡ *Horas Plantão/Urgência:* ${hPlt}\n` +
    `💰 *VALOR TOTAL A FATURAR:* ${tot}\n\n` +
    `🔑 *Chave PIX:* 99981383157 (Telefone)\n` +
    `👤 *Favorecido:* Raimundo Francisco de Loiola Junior\n` +
    `📅 *Vencimento:* Dia 05\n\n` +
    `_Relatório analítico em PDF disponível para conferência._`;

  navigator.clipboard.writeText(msg);
  mostrarToast("Mensagem de fechamento copiada para a área de transferência!");
}

function mostrarToast(msg) {
  const toast = document.getElementById("toast");
  const toastMsg = document.getElementById("toast-msg");
  if (!toast || !toastMsg) return;

  toastMsg.textContent = msg;
  toast.classList.remove("opacity-0", "pointer-events-none", "translate-y-2");
  setTimeout(() => {
    toast.classList.add("opacity-0", "pointer-events-none", "translate-y-2");
  }, 3500);
}
