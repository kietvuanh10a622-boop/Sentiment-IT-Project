from pathlib import Path
html = """<!DOCTYPE html>
<html lang="vi" class="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GlobalPulse AI Dashboard | Kiet Vu</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        tailwind.config = { darkMode: 'class', theme: { extend: {} } }
    </script>
    <style>
        .fade-in { animation: fadeIn 0.45s ease-out forwards; opacity: 0; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
        .pulse-active { animation: pulseBorder 1.5s infinite; border-color: #3b82f6; background-color: rgba(59, 130, 246, 0.08); }
        @keyframes pulseBorder { 0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.35); } 70% { box-shadow: 0 0 0 14px rgba(59, 130, 246, 0); } 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); } }
        .step-done { border-color: #22c55e; background-color: rgba(34, 197, 94, 0.12); color: #166534; }
        .status-pill { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.45rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; }
        .status-pill span { width: 0.55rem; height: 0.55rem; border-radius: 9999px; display: inline-block; }
        .bg-panel { background: rgba(255,255,255,0.92); backdrop-filter: blur(12px); }
        .dark .bg-panel { background: rgba(15,23,42,0.84); }
    </style>
</head>
<body class="bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans p-6 min-h-screen transition-colors duration-300">
    <header class="mb-8 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl shadow-slate-200/30 dark:shadow-black/20 p-6">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div>
                <p class="text-sm uppercase tracking-[0.35em] text-slate-400">Sentiment · Aggregation · Technical Intelligence</p>
                <h1 class="mt-3 text-4xl font-extrabold tracking-tight text-slate-950 dark:text-white">GlobalPulse AI Command Center</h1>
                <p class="mt-3 max-w-2xl text-slate-600 dark:text-slate-300">Theo dõi luồng dữ liệu tin tức đa ngôn ngữ, phân tích cảm xúc và tạo báo cáo tự động cho ngành bán dẫn.</p>
            </div>
            <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <button id="themeToggle" class="inline-flex items-center justify-center rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 px-4 py-3 text-slate-700 dark:text-slate-200 transition hover:bg-slate-200 dark:hover:bg-slate-700">
                    <span class="dark:hidden">🌙</span>
                    <span class="hidden dark:inline">☀️</span>
                    <span class="ml-2 text-sm font-semibold">Theme</span>
                </button>
                <button id="runBtn" onclick="runPipeline()" class="inline-flex items-center justify-center rounded-2xl bg-sky-600 px-5 py-3 text-white shadow-lg shadow-sky-500/20 hover:bg-sky-700 transition font-semibold">
                    ▶ Khởi động Pipeline
                </button>
            </div>
        </div>
        <div class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-panel p-5 shadow-sm">
                <div class="text-sm font-semibold text-slate-500 dark:text-slate-400">Ngày hiện tại</div>
                <div id="currentDate" class="mt-2 text-xl font-bold text-slate-900 dark:text-white"></div>
            </div>
            <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-panel p-5 shadow-sm">
                <div class="text-sm font-semibold text-slate-500 dark:text-slate-400">Trạng thái pipeline</div>
                <div id="pipelineStatus" class="mt-2 flex flex-wrap gap-2"></div>
            </div>
            <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-panel p-5 shadow-sm">
                <div class="text-sm font-semibold text-slate-500 dark:text-slate-400">Nguồn dữ liệu</div>
                <div class="mt-2 flex flex-wrap gap-2">
                    <span class="status-pill bg-blue-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-200"><span class="bg-sky-500"></span>VnExpress</span>
                    <span class="status-pill bg-slate-100 text-slate-700 dark:bg-slate-800/80 dark:text-slate-300"><span class="bg-slate-500"></span>BBC</span>
                </div>
            </div>
        </div>
    </header>
    <section class="mb-8 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl shadow-slate-200/30 dark:shadow-black/20 p-6">
        <div class="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div>
                <h2 class="text-xl font-bold text-slate-950 dark:text-white">Quy trình xử lý</h2>
                <p class="mt-2 text-slate-500 dark:text-slate-400">SP1 đến SP6 được hiển thị dưới dạng tiến trình trực quan.</p>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 w-full lg:w-auto">
                <div id="step1" class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 p-4 text-center transition">
                    <div class="text-sm font-semibold">SP1</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400">Ingestion</div>
                </div>
                <div id="step2" class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 p-4 text-center transition">
                    <div class="text-sm font-semibold">SP2</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400">Cleansing</div>
                </div>
                <div id="step3" class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 p-4 text-center transition">
                    <div class="text-sm font-semibold">SP3</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400">Storage</div>
                </div>
                <div id="step4" class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 p-4 text-center transition">
                    <div class="text-sm font-semibold">SP4</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400">AI Sentiment</div>
                </div>
                <div id="step5" class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 p-4 text-center transition">
                    <div class="text-sm font-semibold">SP5</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400">Analytics</div>
                </div>
                <div id="step6" class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 p-4 text-center transition">
                    <div class="text-sm font-semibold">SP6</div>
                    <div class="text-xs text-slate-500 dark:text-slate-400">Export</div>
                </div>
            </div>
        </div>
    </section>
    <section id="resultsArea" class="hidden fade-in">
        <div class="grid gap-6 lg:grid-cols-4 mb-8">
            <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <p class="text-sm uppercase tracking-[0.25em] text-slate-400 dark:text-slate-500">Tổng bài viết</p>
                <p id="kpiTotal" class="text-4xl font-extrabold mt-4 text-slate-900 dark:text-white">0</p>
                <p class="mt-2 text-slate-500 dark:text-slate-400">VnExpress + BBC</p>
            </div>
            <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <p class="text-sm uppercase tracking-[0.25em] text-slate-400 dark:text-slate-500">Điểm cảm xúc TB</p>
                <p id="kpiScore" class="text-4xl font-extrabold mt-4 text-slate-900 dark:text-white">0.00</p>
                <p class="mt-2 text-slate-500 dark:text-slate-400">Giá trị trung bình giữa -1 và 1</p>
            </div>
            <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <p class="text-sm uppercase tracking-[0.25em] text-slate-400 dark:text-slate-500">Tích cực</p>
                <p id="kpiPos" class="text-4xl font-extrabold mt-4 text-emerald-600 dark:text-emerald-300">0%</p>
                <p id="kpiPosCount" class="mt-2 text-slate-500 dark:text-slate-400">0 bài</p>
            </div>
            <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <p class="text-sm uppercase tracking-[0.25em] text-slate-400 dark:text-slate-500">Tiêu cực</p>
                <p id="kpiNeg" class="text-4xl font-extrabold mt-4 text-red-600 dark:text-red-300">0%</p>
                <p id="kpiNegCount" class="mt-2 text-slate-500 dark:text-slate-400">0 bài</p>
            </div>
        </div>
        <div class="grid gap-6 xl:grid-cols-3 mb-8">
            <div class="xl:col-span-2 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <div class="flex items-center justify-between mb-5">
                    <div>
                        <h2 class="text-xl font-bold text-slate-950 dark:text-white">Xu hướng Cảm xúc theo ngày</h2>
                        <p class="text-sm text-slate-500 dark:text-slate-400">Tính điểm sentiment trung bình theo ngày.</p>
                    </div>
                </div>
                <div class="h-72"><canvas id="trendChart" class="h-full w-full"></canvas></div>
            </div>
            <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <div class="flex items-center justify-between mb-5">
                    <div>
                        <h2 class="text-xl font-bold text-slate-950 dark:text-white">Tỉ trọng cảm xúc</h2>
                        <p class="text-sm text-slate-500 dark:text-slate-400">Positive / Neutral / Negative.</p>
                    </div>
                </div>
                <div class="h-72"><canvas id="pieChart" class="h-full w-full"></canvas></div>
            </div>
        </div>
        <div class="grid gap-6 lg:grid-cols-2 mb-8">
            <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <div class="flex items-center justify-between mb-5">
                    <div>
                        <h2 class="text-xl font-bold text-slate-950 dark:text-white">So sánh theo nguồn</h2>
                        <p class="text-sm text-slate-500 dark:text-slate-400">Đối chiếu cảm xúc giữa VnExpress và BBC.</p>
                    </div>
                </div>
                <div class="h-72"><canvas id="barChart" class="h-full w-full"></canvas></div>
            </div>
            <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm space-y-4">
                <div>
                    <h2 class="text-xl font-bold text-slate-950 dark:text-white">Tùy chọn bộ lọc</h2>
                    <p class="text-sm text-slate-500 dark:text-slate-400">Lọc theo danh mục và tìm kiếm tiêu đề.</p>
                </div>
                <div class="grid gap-4">
                    <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300">Danh mục</label>
                    <select id="categoryFilter" onchange="applyFilter(this.value)" class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100">
                        <option value="All">Tất cả</option>
                    </select>
                    <label class="block text-sm font-semibold text-slate-700 dark:text-slate-300">Tìm kiếm tiêu đề</label>
                    <input id="searchInput" type="text" oninput="applySearch(this.value)" placeholder="Nhập từ khoá..." class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100" />
                </div>
                <div class="grid grid-cols-1 gap-3 pt-3">
                    <button onclick="exportCSV()" class="w-full rounded-2xl bg-emerald-600 px-4 py-3 text-white font-semibold hover:bg-emerald-500 transition">Xuất CSV</button>
                    <button onclick="exportJSON()" class="w-full rounded-2xl bg-sky-600 px-4 py-3 text-white font-semibold hover:bg-sky-500 transition">Xuất JSON</button>
                    <button onclick="exportReport()" class="w-full rounded-2xl bg-violet-600 px-4 py-3 text-white font-semibold hover:bg-violet-500 transition">Tải Báo cáo Kỹ thuật</button>
                </div>
            </div>
        </div>
        <div class="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
            <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between mb-4">
                <div>
                    <h2 class="text-xl font-bold text-slate-950 dark:text-white">Cơ sở dữ liệu bài viết</h2>
                    <p class="text-sm text-slate-500 dark:text-slate-400">Danh sách bài viết đã phân tích có thể xuất ra CSV/JSON.</p>
                </div>
                <div class="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                    <div class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-4 py-3 text-slate-700 dark:text-slate-300">Bộ lọc: <span class="font-semibold" id="currentFilterLabel">All</span></div>
                    <div class="rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-4 py-3 text-slate-700 dark:text-slate-300">Kết quả: <span class="font-semibold" id="currentCountLabel">0</span></div>
                </div>
            </div>
            <div class="overflow-x-auto rounded-3xl border border-slate-200 dark:border-slate-800">
                <table class="min-w-full border-collapse text-left text-sm">
                    <thead class="bg-slate-50 text-slate-600 dark:bg-slate-950 dark:text-slate-300 uppercase text-xs tracking-[0.2em] font-semibold">
                        <tr>
                            <th class="px-4 py-4">Ngày</th>
                            <th class="px-4 py-4">Tiêu đề</th>
                            <th class="px-4 py-4">Nguồn</th>
                            <th class="px-4 py-4">Danh mục</th>
                            <th class="px-4 py-4">Sentiment</th>
                            <th class="px-4 py-4">Điểm</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody" class="divide-y divide-slate-200 dark:divide-slate-800"></tbody>
                </table>
            </div>
        </div>
    </section>
    <script>
        const themeToggleBtn = document.getElementById('themeToggle');
        const themeStorage = localStorage.getItem('theme');
        if (themeStorage === 'dark' || (!themeStorage && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        themeToggleBtn.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
        });
        const MOCK_DATA = [
            { id: 1, date: "2026-07-20", category: "Supply Chain", title: "TSMC ghi nhận doanh thu kỷ lục nhờ chip AI", source: "VnExpress", sentiment: "Positive", score: 0.85 },
            { id: 2, date: "2026-07-20", category: "Geopolitics", title: "Global semiconductor supply chain faces new delays", source: "BBC", sentiment: "Negative", score: -0.65 },
            { id: 3, date: "2026-07-21", category: "Technology", title: "Nvidia ra mắt dòng GPU Blackwell thế hệ mới", source: "VnExpress", sentiment: "Positive", score: 0.90 },
            { id: 4, date: "2026-07-21", category: "Supply Chain", title: "Intel delays construction of Ohio mega-fab", source: "BBC", sentiment: "Negative", score: -0.70 },
            { id: 5, date: "2026-07-22", category: "Market", title: "Thị trường vi mạch Việt Nam thiếu hụt nhân sự", source: "VnExpress", sentiment: "Negative", score: -0.45 },
            { id: 6, date: "2026-07-22", category: "Market", title: "Samsung plans $40 billion investment in US", source: "BBC", sentiment: "Positive", score: 0.75 },
            { id: 7, date: "2026-07-23", category: "Market", title: "Cổ phiếu ngành bán dẫn đồng loạt đi ngang", source: "VnExpress", sentiment: "Neutral", score: 0.05 },
            { id: 8, date: "2026-07-23", category: "Geopolitics", title: "US tightens export controls on advanced AI chips", source: "BBC", sentiment: "Negative", score: -0.80 }
        ];
        let stats = { total: 0, pos: 0, neg: 0, neu: 0, avg: 0 };
        let currentFilter = 'All';
        let currentSearch = '';
        let chartInstances = {};
        document.getElementById('currentDate').innerText = new Date().toLocaleDateString('vi-VN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
        updatePipelineStatus('Sẵn sàng khởi động');
        function updatePipelineStatus(message) {
            const status = document.getElementById('pipelineStatus');
            status.innerHTML = `<span class="status-pill bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200"><span class="bg-slate-500"></span>${message}</span>`;
        }
        function initFilters() {
            const categories = [...new Set(MOCK_DATA.map(d => d.category))].sort();
            const select = document.getElementById('categoryFilter');
            select.innerHTML = '<option value="All">Tất cả</option>';
            categories.forEach(cat => {
                select.innerHTML += `<option value="${cat}">${cat}</option>`;
            });
            currentFilter = 'All';
            select.value = 'All';
            document.getElementById('currentFilterLabel').innerText = 'All';
        }
        function applyFilter(value) {
            currentFilter = value;
            document.getElementById('currentFilterLabel').innerText = value;
            processData();
        }
        function applySearch(value) {
            currentSearch = value.trim().toLowerCase();
            processData();
        }
        async function runPipeline() {
            const btn = document.getElementById('runBtn');
            btn.disabled = true;
            btn.innerText = '⏳ Đang chạy...';
            btn.classList.add('opacity-70', 'cursor-not-allowed');
            const steps = ['step1', 'step2', 'step3', 'step4', 'step5', 'step6'];
            for (let step of steps) {
                const el = document.getElementById(step);
                el.classList.add('pulse-active');
                await new Promise(resolve => setTimeout(resolve, 650));
                el.classList.remove('pulse-active');
                el.classList.add('step-done');
            }
            initFilters();
            processData();
            document.getElementById('resultsArea').classList.remove('hidden');
            updatePipelineStatus('Pipeline đã hoàn tất');
            btn.innerText = '✅ Hoàn tất';
            btn.classList.remove('opacity-70', 'cursor-not-allowed');
        }
        function processData() {
            let filtered = MOCK_DATA;
            if (currentFilter !== 'All') {
                filtered = filtered.filter(item => item.category === currentFilter);
            }
            if (currentSearch) {
                filtered = filtered.filter(item => item.title.toLowerCase().includes(currentSearch) || item.source.toLowerCase().includes(currentSearch));
            }
            stats.total = filtered.length;
            stats.pos = filtered.filter(item => item.sentiment === 'Positive').length;
            stats.neg = filtered.filter(item => item.sentiment === 'Negative').length;
            stats.neu = filtered.filter(item => item.sentiment === 'Neutral').length;
            stats.avg = stats.total > 0 ? (filtered.reduce((sum, item) => sum + item.score, 0) / stats.total).toFixed(3) : '0.000';
            document.getElementById('kpiTotal').innerText = stats.total;
            document.getElementById('kpiScore').innerText = stats.avg;
            document.getElementById('kpiPos').innerText = stats.total > 0 ? `${((stats.pos / stats.total) * 100).toFixed(1)}%` : '0%';
            document.getElementById('kpiPosCount').innerText = `${stats.pos} bài`;
            document.getElementById('kpiNeg').innerText = stats.total > 0 ? `${((stats.neg / stats.total) * 100).toFixed(1)}%` : '0%';
            document.getElementById('kpiNegCount').innerText = `${stats.neg} bài`;
            document.getElementById('currentCountLabel').innerText = stats.total;
            const tableBody = document.getElementById('tableBody');
            tableBody.innerHTML = filtered.map(item => {
                const badgeClass = item.sentiment === 'Positive' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' : item.sentiment === 'Negative' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300' : 'bg-slate-100 text-slate-700 dark:bg-slate-700/60 dark:text-slate-200';
                return `
                    <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors">
                        <td class="px-4 py-4 text-slate-500 dark:text-slate-400">${item.date}</td>
                        <td class="px-4 py-4 font-semibold text-slate-900 dark:text-slate-100">${item.title}</td>
                        <td class="px-4 py-4 text-slate-600 dark:text-slate-300">${item.source}</td>
                        <td class="px-4 py-4 text-slate-600 dark:text-slate-300">${item.category}</td>
                        <td class="px-4 py-4"><span class="rounded-full px-3 py-1 text-xs font-semibold ${badgeClass}">${item.sentiment}</span></td>
                        <td class="px-4 py-4 font-mono text-slate-700 dark:text-slate-200">${item.score.toFixed(2)}</td>
                    </tr>`;
            }).join('');
            renderCharts(filtered);
        }
        function renderCharts(data) {
            const destroyChart = id => { if (chartInstances[id]) chartInstances[id].destroy(); };
            destroyChart('trend');
            destroyChart('bar');
            destroyChart('pie');
            const dateSummary = data.reduce((acc, item) => {
                if (!acc[item.date]) acc[item.date] = { sum: 0, count: 0 };
                acc[item.date].sum += item.score;
                acc[item.date].count += 1;
                return acc;
            }, {});
            const trendLabels = Object.keys(dateSummary).sort();
            const trendValues = trendLabels.map(date => (dateSummary[date].sum / dateSummary[date].count).toFixed(3));
            chartInstances.trend = new Chart(document.getElementById('trendChart'), {
                type: 'line',
                data: {
                    labels: trendLabels,
                    datasets: [{ label: 'Sentiment trung bình', data: trendValues, borderColor: '#0ea5e9', backgroundColor: 'rgba(14,165,233,0.18)', fill: true, tension: 0.35, pointRadius: 4, pointBackgroundColor: '#0ea5e9' }]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { min: -1, max: 1, ticks: { stepSize: 0.5 } } } }
            });
            const sourceLabels = [...new Set(data.map(item => item.source))];
            const positive = sourceLabels.map(source => data.filter(item => item.source === source && item.sentiment === 'Positive').length);
            const neutral = sourceLabels.map(source => data.filter(item => item.source === source && item.sentiment === 'Neutral').length);
            const negative = sourceLabels.map(source => data.filter(item => item.source === source && item.sentiment === 'Negative').length);
            chartInstances.bar = new Chart(document.getElementById('barChart'), {
                type: 'bar',
                data: { labels: sourceLabels, datasets: [ { label: 'Positive', data: positive, backgroundColor: '#22c55e' }, { label: 'Neutral', data: neutral, backgroundColor: '#64748b' }, { label: 'Negative', data: negative, backgroundColor: '#ef4444' } ] },
                options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } } }
            });
            chartInstances.pie = new Chart(document.getElementById('pieChart'), {
                type: 'doughnut',
                data: { labels: ['Positive', 'Neutral', 'Negative'], datasets: [ { data: [stats.pos, stats.neu, stats.neg], backgroundColor: ['#22c55e', '#64748b', '#ef4444'] } ] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
            });
        }
        function formatCSVCell(value) {
            const escaped = String(value).replace(/"/g, '""');
            return `"${escaped}"`;
        }
        function downloadFile(content, filename, type) {
            const blob = new Blob([content], { type });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        function exportCSV() {
            const filtered = currentFilter === 'All' ? MOCK_DATA : MOCK_DATA.filter(item => item.category === currentFilter);
            const visible = currentSearch ? filtered.filter(item => item.title.toLowerCase().includes(currentSearch) || item.source.toLowerCase().includes(currentSearch)) : filtered;
            const csv = ['Date,Title,Category,Source,Sentiment,Score', ...visible.map(item => [item.date, item.title, item.category, item.source, item.sentiment, item.score.toFixed(2)].map(formatCSVCell).join(','))].join('\n');
            downloadFile(csv, 'articles_backup.csv', 'text/csv');
        }
        function exportJSON() {
            const result = {
                generated_at: new Date().toISOString(),
                filter: currentFilter,
                search: currentSearch,
                stats: stats,
                articles: MOCK_DATA.filter(item => (currentFilter === 'All' || item.category === currentFilter) && (!currentSearch || item.title.toLowerCase().includes(currentSearch) || item.source.toLowerCase().includes(currentSearch)))
            };
            downloadFile(JSON.stringify(result, null, 2), 'daily_summary.json', 'application/json');
        }
        function exportReport() {
            const reportLines = [
                'GLOBALPULSE AI - TECHNICAL REPORT',
                'Generated: ' + new Date().toLocaleString('vi-VN'),
                '---',
                `Total articles: ${stats.total}`,
                `Average sentiment score: ${stats.avg}`,
                `Positive articles: ${stats.pos}`,
                `Neutral articles: ${stats.neu}`,
                `Negative articles: ${stats.neg}`,
                '---',
                'Top categories:',
            ];
            const categorySummary = MOCK_DATA.reduce((acc, item) => {
                acc[item.category] = (acc[item.category] || 0) + 1;
                return acc;
            }, {});
            Object.entries(categorySummary).forEach(([cat, count]) => reportLines.push(`- ${cat}: ${count}`));
            reportLines.push('---');
            reportLines.push('Notes:');
            reportLines.push('- Dashboard đã cập nhật dữ liệu giả lập cho trình diễn UI.');
            reportLines.push('- Hệ thống hỗ trợ xuất CSV/JSON và báo cáo kỹ thuật tự động.');
            downloadFile(reportLines.join('\n'), 'Technical_Report_Draft.txt', 'text/plain');
        }
    </script>
</body>
</html>"""
Path('index.html').write_text(html, encoding='utf-8')
print('index.html written')
