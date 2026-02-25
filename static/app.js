// ============================================
//  QUINIELA INTELIGENTE — Frontend Logic
// ============================================

// Tab Navigation
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        const panelId = 'panel' + capitalize(tab.dataset.tab);
        document.getElementById(panelId).classList.add('active');

        // Auto-load data
        if (tab.dataset.tab === 'clasificacion') cargarClasificacion();
        if (tab.dataset.tab === 'graficas') cargarEquipos();
    });
});

function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

// ============================================
//  1. PREDICCIÓN EN VIVO
// ============================================

async function cargarPrediccion() {
    const loading = document.getElementById('prediccionLoading');
    const content = document.getElementById('prediccionContent');
    loading.classList.remove('hidden');
    content.innerHTML = '';

    try {
        const res = await fetch('/api/prediccion');
        const json = await res.json();
        loading.classList.add('hidden');

        if (json.status === 'ok') {
            renderBoleto(json.data, content);
        } else {
            content.innerHTML = `<p style="color:var(--danger)">Error: ${json.message}</p>`;
        }
    } catch (e) {
        loading.classList.add('hidden');
        content.innerHTML = `<p style="color:var(--danger)">Error de conexión: ${e.message}</p>`;
    }
}

function renderBoleto(data, container) {
    container.innerHTML = '';
    data.forEach(m => {
        const tipoClass = m.Tipo === 'Triple' ? 'bet-triple' : m.Tipo === 'Doble' ? 'bet-doble' : 'bet-fijo';
        const card = document.createElement('div');
        card.className = 'match-card';
        card.innerHTML = `
            <span class="match-num">${m.Partido_Id}</span>
            <div class="match-teams">
                <span class="team-home">${m.Home}</span>
                <span class="team-sep">vs</span>
                <span class="team-away">${m.Away}</span>
            </div>
            <div class="match-probs">
                <span class="prob prob-1">1: ${(m.P1 * 100).toFixed(1)}%</span>
                <span class="prob prob-x">X: ${(m.PX * 100).toFixed(1)}%</span>
                <span class="prob prob-2">2: ${(m.P2 * 100).toFixed(1)}%</span>
            </div>
            <div class="match-bet ${tipoClass}">${m.Apuesta} (${m.Tipo})</div>
        `;
        container.appendChild(card);
    });
}

// ============================================
//  2. BOLETO MANUAL
// ============================================

// Generate 14 form rows on load
(function initBoletoForm() {
    const form = document.getElementById('boletoForm');
    for (let i = 1; i <= 14; i++) {
        const row = document.createElement('div');
        row.className = 'form-row';
        row.innerHTML = `
            <span class="match-num">${i}</span>
            <input type="text" id="home_${i}" placeholder="Equipo Local" list="equiposList">
            <span class="vs-label">vs</span>
            <input type="text" id="away_${i}" placeholder="Equipo Visitante" list="equiposList">
        `;
        form.appendChild(row);
    }
    // Also load datalist for autocomplete
    loadEquiposList();
})();

async function loadEquiposList() {
    try {
        const res = await fetch('/api/equipos');
        const json = await res.json();
        if (json.status === 'ok') {
            let datalist = document.getElementById('equiposList');
            if (!datalist) {
                datalist = document.createElement('datalist');
                datalist.id = 'equiposList';
                document.body.appendChild(datalist);
            }
            datalist.innerHTML = json.equipos.map(e => `<option value="${e}">`).join('');
        }
    } catch (e) { /* silent */ }
}

async function predecirBoletoManual() {
    const matches = [];
    for (let i = 1; i <= 14; i++) {
        const home = document.getElementById(`home_${i}`).value.trim();
        const away = document.getElementById(`away_${i}`).value.trim();
        if (home && away) {
            matches.push({ home, away });
        }
    }

    if (matches.length === 0) {
        alert('Introduce al menos un partido.');
        return;
    }

    const container = document.getElementById('boletoResultado');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Analizando...</p></div>';

    try {
        const res = await fetch('/api/predict-custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ matches })
        });
        const json = await res.json();

        if (json.status === 'ok') {
            renderBoleto(json.data, container);
        } else {
            container.innerHTML = `<p style="color:var(--danger)">Error: ${json.message}</p>`;
        }
    } catch (e) {
        container.innerHTML = `<p style="color:var(--danger)">Error: ${e.message}</p>`;
    }
}

// ============================================
//  3. CLASIFICACIÓN
// ============================================

let clasificacionData = null;

async function cargarClasificacion() {
    if (clasificacionData) { renderClasificacion('primera'); return; }

    const container = document.getElementById('clasificacionContent');
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Cargando clasificación...</p></div>';

    try {
        const res = await fetch('/api/clasificacion');
        const json = await res.json();

        if (json.status === 'ok') {
            clasificacionData = json;
            renderClasificacion('primera');
        } else {
            container.innerHTML = `<p style="color:var(--danger)">Error: ${json.message}</p>`;
        }
    } catch (e) {
        container.innerHTML = `<p style="color:var(--danger)">Error: ${e.message}</p>`;
    }
}

function mostrarLiga(liga) {
    document.querySelectorAll('.btn-liga').forEach(b => b.classList.remove('active'));
    document.getElementById(liga === 'primera' ? 'btnPrimera' : 'btnSegunda').classList.add('active');
    renderClasificacion(liga);
}

function renderClasificacion(liga) {
    const data = liga === 'primera' ? clasificacionData.primera : clasificacionData.segunda;
    const container = document.getElementById('clasificacionContent');
    const totalTeams = data.length;

    let html = `<table class="clasif-table">
        <thead><tr>
            <th>#</th><th>Equipo</th><th>Pts</th><th>GF</th><th>GC</th><th>DG</th><th>Forma L5</th>
        </tr></thead><tbody>`;

    data.forEach((team, idx) => {
        const pos = idx + 1;
        let posClass = 'pos-normal';
        if (pos === 1) posClass = 'pos-1';
        else if (pos === 2) posClass = 'pos-2';
        else if (pos === 3) posClass = 'pos-3';
        else if (pos <= 4) posClass = 'pos-champ';
        else if (pos <= 6) posClass = 'pos-euro';
        else if (pos > totalTeams - 3) posClass = 'pos-releg';

        let formClass = 'form-mid';
        if (team.Forma_L5 >= 10) formClass = 'form-good';
        else if (team.Forma_L5 <= 5) formClass = 'form-bad';

        const dgSign = team.DG > 0 ? '+' : '';

        html += `<tr>
            <td><span class="pos-badge ${posClass}">${pos}</span></td>
            <td><span class="team-name" onclick="verEquipo('${team.Equipo}')">${team.Equipo}</span></td>
            <td><strong>${team.Puntos}</strong></td>
            <td>${team.GF}</td>
            <td>${team.GC}</td>
            <td>${dgSign}${team.DG}</td>
            <td><span class="form-badge ${formClass}">${team.Forma_L5} pts</span></td>
        </tr>`;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

function verEquipo(equipo) {
    // Jump to gráficas tab and select this team
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.getElementById('tabGraficas').classList.add('active');
    document.getElementById('panelGraficas').classList.add('active');

    cargarEquipos().then(() => {
        document.getElementById('selectEquipo').value = equipo;
        cargarStatsEquipo();
    });
}

// ============================================
//  4. GRÁFICAS
// ============================================

let chartPuntos = null, chartForma = null, chartGoles = null, chartXG = null;

async function cargarEquipos() {
    const select = document.getElementById('selectEquipo');
    if (select.options.length > 1) return; // Already loaded

    try {
        const res = await fetch('/api/equipos');
        const json = await res.json();
        if (json.status === 'ok') {
            json.equipos.forEach(e => {
                const opt = document.createElement('option');
                opt.value = e;
                opt.textContent = e;
                select.appendChild(opt);
            });
        }
    } catch (e) { /* silent */ }
}

async function cargarStatsEquipo() {
    const equipo = document.getElementById('selectEquipo').value;
    if (!equipo) return;

    try {
        const res = await fetch(`/api/stats/${encodeURIComponent(equipo)}`);
        const json = await res.json();
        if (json.status === 'ok') {
            renderCharts(json.partidos, equipo);
        }
    } catch (e) { /* silent */ }
}

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } }
    },
    scales: {
        x: {
            ticks: { color: '#64748b', font: { size: 10 } },
            grid: { color: 'rgba(255,255,255,0.04)' }
        },
        y: {
            ticks: { color: '#64748b' },
            grid: { color: 'rgba(255,255,255,0.04)' }
        }
    }
};

function renderCharts(partidos, equipo) {
    const labels = partidos.map(p => p.Fecha);
    const puntosAcum = partidos.map(p => p.Puntos_Acum);
    const gf = partidos.map(p => p.GF);
    const gc = partidos.map(p => p.GC);
    const xg = partidos.map(p => p.xG);
    const xga = partidos.map(p => p.xGA);
    const forma = partidos.map(p => p.Forma_L5);

    // Destroy previous charts
    if (chartPuntos) chartPuntos.destroy();
    if (chartForma) chartForma.destroy();
    if (chartGoles) chartGoles.destroy();
    if (chartXG) chartXG.destroy();

    // 1. Evolución de puntos
    chartPuntos = new Chart(document.getElementById('chartPuntos'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: `Puntos Acumulados — ${equipo}`,
                data: puntosAcum,
                borderColor: '#22d3ee',
                backgroundColor: 'rgba(34, 211, 238, 0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 4,
                pointHoverRadius: 7
            }]
        },
        options: { ...chartDefaults }
    });

    // 2. Forma reciente
    chartForma = new Chart(document.getElementById('chartForma'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Forma (Últimos 5)',
                data: forma,
                backgroundColor: forma.map(f => f >= 10 ? 'rgba(52,211,153,0.6)' : f >= 6 ? 'rgba(251,191,36,0.6)' : 'rgba(248,113,113,0.6)'),
                borderRadius: 4
            }]
        },
        options: { ...chartDefaults }
    });

    // 3. Goles
    chartGoles = new Chart(document.getElementById('chartGoles'), {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Goles Marcados',
                    data: gf,
                    backgroundColor: 'rgba(34, 211, 238, 0.6)',
                    borderRadius: 4
                },
                {
                    label: 'Goles Recibidos',
                    data: gc,
                    backgroundColor: 'rgba(248, 113, 113, 0.5)',
                    borderRadius: 4
                }
            ]
        },
        options: { ...chartDefaults }
    });

    // 4. xG vs xGA
    chartXG = new Chart(document.getElementById('chartXG'), {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'xG (Esperados a Favor)',
                    data: xg,
                    borderColor: '#34d399',
                    backgroundColor: 'rgba(52, 211, 153, 0.1)',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'xGA (Esperados en Contra)',
                    data: xga,
                    borderColor: '#f87171',
                    backgroundColor: 'rgba(248, 113, 113, 0.1)',
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: { ...chartDefaults }
    });
}
