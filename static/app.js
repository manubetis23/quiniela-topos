// ============================================
//  QUINIELA TOPOS — Frontend Logic v3.0
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

    // Resumen ejecutivo del boleto
    const seguros = data.filter(m => m.Tipo === 'Fijo' && Math.max(m.P1, m.PX, m.P2) > 0.65).length;
    const impredecibles = data.filter(m => m.Incertidumbre && m.Incertidumbre > 1.4).length;
    const triples = data.filter(m => m.Tipo === 'Triple').length;
    const dobles = data.filter(m => m.Tipo === 'Doble').length;

    if (data.length >= 14) {
        const summary = document.createElement('div');
        summary.className = 'boleto-summary';
        summary.innerHTML = `
            <div class="summary-items">
                <div class="summary-item">
                    <span class="summary-num">${seguros}</span>
                    <span class="summary-label">Partidos seguros (>65%)</span>
                </div>
                <div class="summary-item">
                    <span class="summary-num">${impredecibles}</span>
                    <span class="summary-label">Partidos impredecibles</span>
                </div>
                <div class="summary-item">
                    <span class="summary-num">${triples}T ${dobles}D</span>
                    <span class="summary-label">Triples / Dobles</span>
                </div>
            </div>
        `;
        container.appendChild(summary);
    }

    data.forEach(m => {
        const tipoClass = m.Tipo === 'Triple' ? 'bet-triple' : m.Tipo === 'Doble' ? 'bet-doble' : m.Tipo === 'Pleno' ? 'bet-pleno' : 'bet-fijo';
        const maxProb = Math.max(m.P1, m.PX, m.P2);

        // Confidence meter
        let confIcon, confLabel, confClass;
        if (maxProb > 0.60) { confIcon = '🟢'; confLabel = 'Alta confianza'; confClass = 'conf-high'; }
        else if (maxProb > 0.45) { confIcon = '🟡'; confLabel = 'Media'; confClass = 'conf-mid'; }
        else { confIcon = '🔴'; confLabel = 'Incierto'; confClass = 'conf-low'; }

        // Generar explicación contextual
        let explicacion = '';
        if (m.Explicacion) {
            explicacion = `<div class="match-explain">${m.Explicacion}</div>`;
        }

        // Barra de probabilidades visual
        const p1w = (m.P1 * 100).toFixed(0);
        const pXw = (m.PX * 100).toFixed(0);
        const p2w = (m.P2 * 100).toFixed(0);

        const card = document.createElement('div');
        card.className = 'match-card';
        if (m.Tipo === 'Pleno') card.classList.add('pleno-card');

        card.innerHTML = `
            <span class="match-num">${m.Partido_Id}${m.Tipo === 'Pleno' ? ' ★' : ''}</span>
            <div class="match-teams">
                <span class="team-home">${m.Home}</span>
                <span class="team-sep">vs</span>
                <span class="team-away">${m.Away}</span>
                <span class="conf-badge ${confClass}" title="${confLabel}">${confIcon} ${(maxProb * 100).toFixed(0)}%</span>
            </div>
            <div class="prob-bar-container">
                <div class="prob-bar prob-bar-1" style="width:${p1w}%">${p1w > 12 ? '1:' + p1w + '%' : ''}</div>
                <div class="prob-bar prob-bar-x" style="width:${pXw}%">${pXw > 12 ? 'X:' + pXw + '%' : ''}</div>
                <div class="prob-bar prob-bar-2" style="width:${p2w}%">${p2w > 12 ? '2:' + p2w + '%' : ''}</div>
            </div>
            ${explicacion}
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

function formVisual(formStr) {
    if (!formStr) return '';
    return formStr.split('').map(r => {
        if (r === 'W') return '<span class="form-dot form-w" title="Victoria">✅</span>';
        if (r === 'D') return '<span class="form-dot form-d" title="Empate">🟰</span>';
        return '<span class="form-dot form-l" title="Derrota">❌</span>';
    }).join('');
}

function renderClasificacion(liga) {
    const data = liga === 'primera' ? clasificacionData.primera : clasificacionData.segunda;
    const container = document.getElementById('clasificacionContent');
    const totalTeams = data.length;

    let html = `<table class="clasif-table">
        <thead><tr>
            <th>#</th><th>Equipo</th><th>PJ</th><th>PG</th><th>PE</th><th>PP</th><th>Pts</th><th>GF</th><th>GC</th><th>DG</th><th>Forma</th>
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

        const dgSign = team.DG > 0 ? '+' : '';

        html += `<tr>
            <td><span class="pos-badge ${posClass}">${pos}</span></td>
            <td><span class="team-name" onclick="verEquipo('${team.Equipo}')">${team.Equipo}</span></td>
            <td>${team.PJ || '-'}</td>
            <td>${team.PG || '-'}</td>
            <td>${team.PE || '-'}</td>
            <td>${team.PP || '-'}</td>
            <td><strong>${team.Puntos}</strong></td>
            <td>${team.GF}</td>
            <td>${team.GC}</td>
            <td>${dgSign}${team.DG}</td>
            <td>${formVisual(team.Forma_Visual)}</td>
        </tr>`;
    });

    html += '</tbody></table>';

    // Add evolution chart container
    html += `<div class="chart-card" style="margin-top:1.5rem;">
        <h3>📈 Evolución de Puntos — Top 6</h3>
        <canvas id="chartEvolucion"></canvas>
    </div>`;

    container.innerHTML = html;

    // Load evolution data for top 6 teams
    const top6 = data.slice(0, 6).map(t => t.Equipo);
    loadEvolutionChart(top6);
}

let chartEvolucion = null;

async function loadEvolutionChart(teams) {
    try {
        const res = await fetch('/api/evolucion-clasificacion');
        const json = await res.json();
        if (json.status !== 'ok') return;

        const colors = ['#22d3ee', '#fbbf24', '#f87171', '#34d399', '#a78bfa', '#fb923c'];

        const maxLen = Math.max(...teams.map(t => (json.evolution[t] || []).length));
        const labels = (json.evolution[teams[0]] || []).map(p => p.fecha);

        const datasets = teams.map((team, i) => ({
            label: team,
            data: (json.evolution[team] || []).map(p => p.puntos),
            borderColor: colors[i],
            backgroundColor: 'transparent',
            tension: 0.3,
            pointRadius: 2,
            pointHoverRadius: 5,
            borderWidth: 2
        }));

        if (chartEvolucion) chartEvolucion.destroy();

        const ctx = document.getElementById('chartEvolucion');
        if (!ctx) return;

        chartEvolucion = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#d1d5db', font: { size: 11 } } }
                },
                scales: {
                    x: { ticks: { color: '#9ca3af', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.03)' } },
                    y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' }, title: { display: true, text: 'Puntos', color: '#9ca3af' } }
                }
            }
        });
    } catch (e) {
        console.warn('Error loading evolution chart:', e);
    }
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

// Moving average helper
function movingAvg(arr, window = 5) {
    return arr.map((_, i) => {
        const start = Math.max(0, i - window + 1);
        const slice = arr.slice(start, i + 1);
        return +(slice.reduce((a, b) => a + b, 0) / slice.length).toFixed(2);
    });
}

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } }
    },
    scales: {
        x: {
            ticks: { color: '#64748b', font: { size: 10 }, maxRotation: 45 },
            grid: { color: 'rgba(255,255,255,0.04)' }
        },
        y: {
            ticks: { color: '#64748b' },
            grid: { color: 'rgba(255,255,255,0.04)' }
        }
    }
};

function renderCharts(partidos, equipo) {
    // Use short labels: Rival + cond
    const labels = partidos.map(p => {
        const icon = p.Condicion === 'Local' ? '🏠' : '✈️';
        const res = p.Resultado === 'W' ? '✅' : p.Resultado === 'D' ? '🟰' : '❌';
        return `${icon} ${p.Rival} ${res}`;
    });
    const puntosAcum = partidos.map(p => p.Puntos_Acum);
    const gf = partidos.map(p => p.GF);
    const gc = partidos.map(p => p.GC);
    const xg = partidos.map(p => p.xG);
    const xga = partidos.map(p => p.xGA);
    const forma = partidos.map(p => p.Forma_L5);

    // Moving averages for goals
    const gfMA = movingAvg(gf, 5);
    const gcMA = movingAvg(gc, 5);

    // Destroy previous charts
    if (chartPuntos) chartPuntos.destroy();
    if (chartForma) chartForma.destroy();
    if (chartGoles) chartGoles.destroy();
    if (chartXG) chartXG.destroy();

    // 1. Evolución de puntos (post-match, ahora correcto)
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
                pointHoverRadius: 7,
                pointBackgroundColor: partidos.map(p =>
                    p.Resultado === 'W' ? '#34d399' : p.Resultado === 'D' ? '#fbbf24' : '#f87171'
                )
            }]
        },
        options: { ...chartDefaults }
    });

    // 2. Forma reciente (sliding window)
    chartForma = new Chart(document.getElementById('chartForma'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Forma (Últimos 5 partidos)',
                data: forma,
                backgroundColor: forma.map(f => f >= 10 ? 'rgba(52,211,153,0.6)' : f >= 6 ? 'rgba(251,191,36,0.6)' : 'rgba(248,113,113,0.6)'),
                borderRadius: 4
            }]
        },
        options: {
            ...chartDefaults,
            scales: {
                ...chartDefaults.scales,
                y: { ...chartDefaults.scales.y, min: 0, max: 15, ticks: { ...chartDefaults.scales.y.ticks, stepSize: 3 } }
            }
        }
    });

    // 3. Goles — Barras individuales + Media Móvil línea
    chartGoles = new Chart(document.getElementById('chartGoles'), {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'GF (Partido)',
                    data: gf,
                    backgroundColor: 'rgba(34, 211, 238, 0.35)',
                    borderRadius: 4,
                    order: 2
                },
                {
                    label: 'GC (Partido)',
                    data: gc,
                    backgroundColor: 'rgba(248, 113, 113, 0.3)',
                    borderRadius: 4,
                    order: 2
                },
                {
                    label: 'GF Media (5 partidos)',
                    data: gfMA,
                    type: 'line',
                    borderColor: '#22d3ee',
                    borderWidth: 2,
                    pointRadius: 2,
                    fill: false,
                    tension: 0.3,
                    order: 1
                },
                {
                    label: 'GC Media (5 partidos)',
                    data: gcMA,
                    type: 'line',
                    borderColor: '#f87171',
                    borderWidth: 2,
                    pointRadius: 2,
                    fill: false,
                    tension: 0.3,
                    order: 1
                }
            ]
        },
        options: { ...chartDefaults }
    });

    // 4. xG vs xGA (promedios de equipo por temporada — Understat)
    chartXG = new Chart(document.getElementById('chartXG'), {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'xG Equipo (media temporada)',
                    data: xg,
                    borderColor: '#34d399',
                    backgroundColor: 'rgba(52, 211, 153, 0.1)',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'xGA Equipo (media temporada)',
                    data: xga,
                    borderColor: '#f87171',
                    backgroundColor: 'rgba(248, 113, 113, 0.1)',
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: {
            ...chartDefaults,
            plugins: {
                ...chartDefaults.plugins,
                subtitle: {
                    display: true,
                    text: 'Datos Understat — xG promedio del equipo a la fecha de cada partido',
                    color: '#64748b',
                    font: { size: 11, family: 'Inter' },
                    padding: { bottom: 10 }
                }
            }
        }
    });
}
