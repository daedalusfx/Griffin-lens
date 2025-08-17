<!-- src/lib/components/ComparisonChart.svelte -->
<script>
    import { onMount, onDestroy } from 'svelte';
    import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement } from 'chart.js';

    ChartJS.register(Title, Tooltip, Legend, LineElement, CategoryScale, LinearScale, PointElement);

    export let comparisonData = []; // Expects an array of { name, history } objects
    let chartInstance;
    let canvasElement;

    const chartColors = ['#88C0D0', '#A3BE8C', '#EBCB8B'];

    // Reactive statement to update the chart when data changes
    $: if (chartInstance && comparisonData) {
        chartInstance.data.datasets = comparisonData.map((broker, index) => ({
            label: broker.name,
            data: broker.history,
            borderColor: chartColors[index % chartColors.length],
            backgroundColor: chartColors[index % chartColors.length] + '33',
            borderWidth: 2,
            tension: 0.4,
            fill: false,
            pointRadius: 0,
        }));
        chartInstance.update();
    }

    onMount(() => {
        const ctx = canvasElement.getContext('2d');
        chartInstance = new ChartJS(ctx, {
            type: 'line',
            data: {
                labels: Array.from({ length: 20 }, (_, i) => i + 1), // Assuming fixed history length
                datasets: [],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { min: 40, max: 100, grid: { color: '#4C566A' }, ticks: { color: '#D8DEE9' } },
                    x: { grid: { display: false }, ticks: { display: false } }
                },
                plugins: {
                    legend: { position: 'top', labels: { color: '#ECEFF4', boxWidth: 12, padding: 20 } }
                }
            }
        });
    });

    onDestroy(() => {
        if (chartInstance) chartInstance.destroy();
    });
</script>

<div class="h-64">
    <canvas bind:this={canvasElement}></canvas>
</div>