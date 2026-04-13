<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <title>Dashboard Operadoras</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
    body { margin:0; font-family: 'Segoe UI', Arial; background:#e5e7eb; color:#1f2937; }
    header { position:sticky; top:0; padding:16px; text-align:center; font-size:22px; background:#f9fafb; border-bottom:1px solid #ccc; }
    .container { padding:20px; }
    .card { background:#fff; padding:15px; border-radius:10px; margin-bottom:15px; }
    .grid { display:grid; grid-template-columns: repeat(auto-fit,minmax(250px,1fr)); gap:15px; }
    input, select, button { padding:8px; margin:5px; }
    button { background:#2563eb; color:white; border:none; cursor:pointer; }
    .delete { background:red; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:8px; border-bottom:1px solid #ddd; }
  </style>
</head>

<body>

<header>Dashboard Operadoras</header>

<div class="container">

<div class="card">
<h3>Adicionar Registro</h3>
<input id="mes" placeholder="Mês">
<input id="operadora" placeholder="Operadora">
<input id="circuito" placeholder="Circuito">
<input id="desconto" type="number" placeholder="Desconto">
<button onclick="addData()">Adicionar</button>

<h3>Backup</h3>
<button onclick="exportar()">Exportar Excel</button>
<input type="file" onchange="importar(event)">
</div>

<div class="card">
<h3>Filtros</h3>
<select id="filtroMes" onchange="render()"></select>
<select id="filtroOperadora" onchange="render()"></select>
</div>

<div class="grid">
<div class="card"><h3>Total</h3><div id="total"></div></div>
<div class="card"><h3>Circuitos</h3><div id="qtd"></div></div>
<div class="card"><h3>Operadoras</h3><div id="ops"></div></div>
</div>

<div class="grid">
<div class="card"><canvas id="chart1"></canvas></div>
<div class="card"><canvas id="chart2"></canvas></div>
<div class="card"><canvas id="chart3"></canvas></div>
</div>

<div class="card">
<table>
<thead>
<tr>
<th>Mês</th>
<th>Operadora</th>
<th>Circuito</th>
<th>Desconto</th>
<th>Ação</th>
</tr>
</thead>
<tbody id="tabela"></tbody>
</table>
</div>

</div>

<script>

// ===== DADOS =====
let dados = JSON.parse(localStorage.getItem('dados') || '[]');

window.onload = () => {
  const backup = localStorage.getItem('dados_backup');
  if (backup && dados.length === 0) {
    dados = JSON.parse(backup);
  }
  atualizarFiltros();
  render();
};

function salvar(){
  localStorage.setItem('dados', JSON.stringify(dados));
  localStorage.setItem('dados_backup', JSON.stringify(dados));
}

// ===== ADD =====
function addData(){
  const mes = mesInput.value;
  const op = operadoraInput.value;
  const cir = circuitoInput.value;
  const desc = parseFloat(descontoInput.value);

  if(!mes || !op || !cir || isNaN(desc)){
    alert("Preencha tudo");
    return;
  }

  dados.push({mes, operadora:op, circuito:cir, desconto:desc});
  salvar();

  mesInput.value='';
  operadoraInput.value='';
  circuitoInput.value='';
  descontoInput.value='';

  atualizarFiltros();
  render();
}

// ===== REMOVER =====
function remover(i){
  dados.splice(i,1);
  salvar();
  render();
}

// ===== EXPORTAR CSV =====
function exportar(){
  if(dados.length===0){
    alert("Sem dados");
    return;
  }

  let csv = "Mes,Operadora,Circuito,Desconto\n";
  dados.forEach(d=>{
    csv += `${d.mes},${d.operadora},${d.circuito},${d.desconto}\n`;
  });

  const blob = new Blob([csv], {type:'text/csv'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href=url;
  a.download="dados.csv";
  a.click();
}

// ===== IMPORTAR =====
function importar(e){
  const file = e.target.files[0];
  const reader = new FileReader();

  reader.onload = function(ev){
    dados = JSON.parse(ev.target.result);
    salvar();
    atualizarFiltros();
    render();
  };

  reader.readAsText(file);
}

// ===== FILTRO =====
function filtrar(){
  return dados.filter(d=>
    (!filtroMes.value || d.mes==filtroMes.value) &&
    (!filtroOperadora.value || d.operadora==filtroOperadora.value)
  );
}

// ===== AGRUPAR =====
function agrupar(lista,campo){
  let m={};
  lista.forEach(d=>m[d[campo]]=(m[d[campo]]||0)+d.desconto);
  return m;
}

// ===== KPIs =====
function renderKPIs(lista){
  total.innerText = "R$ "+lista.reduce((a,b)=>a+b.desconto,0);
  qtd.innerText = lista.length;
  ops.innerText = [...new Set(lista.map(d=>d.operadora))].length;
}

// ===== TABELA =====
function renderTabela(lista){
  tabela.innerHTML='';
  lista.forEach((d,i)=>{
    tabela.innerHTML+=`
    <tr>
      <td>${d.mes}</td>
      <td>${d.operadora}</td>
      <td>${d.circuito}</td>
      <td>${d.desconto}</td>
      <td><button class="delete" onclick="remover(${i})">X</button></td>
    </tr>`;
  });
}

// ===== GRÁFICOS =====
let c1,c2,c3;

function renderCharts(lista){
  const op = agrupar(lista,'operadora');
  const mes = agrupar(lista,'mes');
  const cir = agrupar(lista,'circuito');

  if(c1) c1.destroy();
  if(c2) c2.destroy();
  if(c3) c3.destroy();

  c1 = new Chart(chart1,{type:'bar',data:{labels:Object.keys(op),datasets:[{data:Object.values(op)}]}});
  c2 = new Chart(chart2,{type:'line',data:{labels:Object.keys(mes),datasets:[{data:Object.values(mes)}]}});
  c3 = new Chart(chart3,{type:'bar',data:{labels:Object.keys(cir),datasets:[{data:Object.values(cir)}]}});
}

// ===== FILTROS =====
function atualizarFiltros(){
  filtroMes.innerHTML='<option value="">Todos</option>';
  filtroOperadora.innerHTML='<option value="">Todas</option>';

  [...new Set(dados.map(d=>d.mes))].forEach(m=>filtroMes.innerHTML+=`<option>${m}</option>`);
  [...new Set(dados.map(d=>d.operadora))].forEach(o=>filtroOperadora.innerHTML+=`<option>${o}</option>`);
}

// ===== RENDER =====
function render(){
  const lista = filtrar();
  renderKPIs(lista);
  renderTabela(lista);
  renderCharts(lista);
}

// ===== ELEMENTOS =====
const mesInput = document.getElementById('mes');
const operadoraInput = document.getElementById('operadora');
const circuitoInput = document.getElementById('circuito');
const descontoInput = document.getElementById('desconto');

const tabela = document.getElementById('tabela');
const total = document.getElementById('total');
const qtd = document.getElementById('qtd');
const ops = document.getElementById('ops');

const chart1 = document.getElementById('chart1');
const chart2 = document.getElementById('chart2');
const chart3 = document.getElementById('chart3');

const filtroMes = document.getElementById('filtroMes');
const filtroOperadora = document.getElementById('filtroOperadora');

</script>

</body>
</html>
