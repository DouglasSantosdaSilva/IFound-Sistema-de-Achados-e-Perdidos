(() => {
    const svgNamespace = 'http://www.w3.org/2000/svg';
    const numberFormat = new Intl.NumberFormat('pt-BR');

    function readChartData(id) {
        const element = document.getElementById(id);
        if (!element) return null;

        try {
            return JSON.parse(element.textContent);
        } catch (error) {
            return null;
        }
    }

    function svgElement(name, attributes = {}) {
        const element = document.createElementNS(svgNamespace, name);
        Object.entries(attributes).forEach(([attribute, value]) => {
            element.setAttribute(attribute, value);
        });
        return element;
    }

    function addSvgText(svg, text, x, y, className, anchor = 'middle') {
        const element = svgElement('text', {
            x,
            y,
            class: className,
            'text-anchor': anchor,
        });
        element.textContent = text;
        svg.appendChild(element);
    }

    function drawMonthlyChart(data) {
        const svg = document.getElementById('ifAdminMonthlyChart');
        if (!svg || !data) return;

        const labels = Array.isArray(data.labels) ? data.labels : [];
        const found = Array.isArray(data.encontrados) ? data.encontrados : [];
        const lost = Array.isArray(data.perdidos) ? data.perdidos : [];
        const left = 46;
        const right = 624;
        const top = 18;
        const bottom = 203;
        const chartHeight = bottom - top;
        const chartWidth = right - left;
        const maximum = Math.max(1, ...found, ...lost);
        const groupWidth = labels.length ? chartWidth / labels.length : chartWidth;
        const barWidth = Math.min(22, groupWidth * 0.24);
        const barGap = 6;

        svg.replaceChildren();

        for (let tick = 0; tick <= 4; tick += 1) {
            const value = Math.round((maximum * tick) / 4);
            const y = bottom - (chartHeight * tick) / 4;
            svg.appendChild(svgElement('line', {
                x1: left,
                y1: y,
                x2: right,
                y2: y,
                class: 'chart-grid-line',
            }));
            addSvgText(svg, numberFormat.format(value), left - 9, y + 1, 'chart-axis-label', 'end');
        }

        labels.forEach((label, index) => {
            const center = left + groupWidth * (index + 0.5);
            const values = [
                { value: Number(found[index]) || 0, className: 'chart-bar-found', offset: -(barWidth / 2 + barGap / 2) },
                { value: Number(lost[index]) || 0, className: 'chart-bar-lost', offset: barWidth / 2 + barGap / 2 },
            ];

            values.forEach(({ value, className, offset }) => {
                const height = (value / maximum) * chartHeight;
                const x = center + offset - barWidth / 2;
                const y = bottom - height;
                const bar = svgElement('rect', {
                    x,
                    y,
                    width: barWidth,
                    height,
                    rx: 3,
                    class: className,
                });
                const title = svgElement('title');
                title.textContent = numberFormat.format(value);
                bar.appendChild(title);
                svg.appendChild(bar);
                if (value > 0) {
                    addSvgText(svg, numberFormat.format(value), x + barWidth / 2, y - 5, 'chart-value-label');
                }
            });

            addSvgText(svg, label, center, bottom + 25, 'chart-axis-label');
        });
    }

    function drawRequestChart(data) {
        const svg = document.getElementById('ifAdminRequestChart');
        const legend = document.getElementById('ifAdminRequestLegend');
        if (!svg || !legend || !data) return;

        const keys = Array.isArray(data.keys) ? data.keys : [];
        const labels = Array.isArray(data.labels) ? data.labels : [];
        const values = Array.isArray(data.values) ? data.values.map((value) => Number(value) || 0) : [];
        const colors = {
            em_analise: '#e5a12c',
            aprovada: '#16945c',
            recusada: '#dc5b5b',
        };
        const total = values.reduce((sum, value) => sum + value, 0);
        const radius = 56;
        const circumference = 2 * Math.PI * radius;
        const centerX = 90;
        const centerY = 82;

        svg.replaceChildren();
        legend.replaceChildren();
        svg.appendChild(svgElement('circle', {
            cx: centerX,
            cy: centerY,
            r: radius,
            class: 'if-admin-donut-track',
        }));

        let offset = 0;
        values.forEach((value, index) => {
            const segmentLength = total ? (value / total) * circumference : 0;
            if (segmentLength > 0) {
                svg.appendChild(svgElement('circle', {
                    cx: centerX,
                    cy: centerY,
                    r: radius,
                    class: 'if-admin-donut-segment',
                    stroke: colors[keys[index]] || '#8b95a5',
                    transform: `rotate(-90 ${centerX} ${centerY})`,
                    'stroke-dasharray': `${Math.max(segmentLength - 2, 0)} ${circumference}`,
                    'stroke-dashoffset': -offset,
                }));
            }
            offset += segmentLength;

            const row = document.createElement('li');
            const dot = document.createElement('i');
            dot.className = 'chart-legend-dot';
            dot.style.backgroundColor = colors[keys[index]] || '#8b95a5';
            dot.setAttribute('aria-hidden', 'true');
            const label = document.createElement('span');
            label.textContent = labels[index] || keys[index] || '';
            const count = document.createElement('strong');
            count.className = 'chart-legend-value';
            count.textContent = numberFormat.format(value);
            row.append(dot, label, count);
            legend.appendChild(row);
        });

        addSvgText(svg, numberFormat.format(total), centerX, centerY + 1, 'if-admin-donut-total');
        addSvgText(svg, 'Solicitações', centerX, centerY + 17, 'if-admin-donut-caption');
    }

    drawMonthlyChart(readChartData('ifAdminMonthlyChartData'));
    drawRequestChart(readChartData('ifAdminRequestChartData'));
})();
