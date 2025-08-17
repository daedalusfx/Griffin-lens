<script>
    import { onMount, onDestroy } from 'svelte';
    import { Chart as ChartJS, Title, Tooltip, LineElement, CategoryScale, LinearScale, PointElement, LineController } from 'chart.js';

    ChartJS.register(Title, Tooltip, LineElement, CategoryScale, LinearScale, PointElement, LineController);

    export let historyData = [];

    let chart;
    let canvasElement;

    // Update chart when data changes
    $: if (chart && historyData) {
        chart.data.labels = historyData.map((_, i) => i + 1);
        chart.data.datasets[0].data = historyData;
        chart.update('none'); // 'none' for no animation
    }

    onMount(() => {
        const ctx = canvasElement.getContext('2d');
        chart = new ChartJS(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    borderColor: '#88C0D0',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 0, // Hide points
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 0 },
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                scales: {
                    x: { display: false },
                    y: { display: false, min: 0, max: 100 }
                }
            }
        });
    });

    onDestroy(() => {
        if (chart) chart.destroy();
    });
</script>

<div class="w-full h-full">
    <canvas bind:this={canvasElement}></canvas>
</div>
