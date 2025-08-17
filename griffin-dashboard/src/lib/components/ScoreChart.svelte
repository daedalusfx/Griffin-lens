<script>
    import { onMount, onDestroy } from 'svelte';
    // Import LineController along with the other components
    import { Chart as ChartJS, Title, Tooltip, LineElement, CategoryScale, LinearScale, PointElement, LineController } from 'chart.js';

    // Register the new LineController
    ChartJS.register(Title, Tooltip, LineElement, CategoryScale, LinearScale, PointElement, LineController);

    export let historyData = [];
    export let brokerName = '';

    let chart; // This will hold the chart instance
    let canvasElement; // This will bind to the <canvas> element

    // This reactive statement updates the chart whenever the data changes
    $: if (chart && historyData) {
        chart.data.labels = historyData.map((_, i) => i + 1);
        chart.data.datasets[0].data = historyData;
        chart.data.datasets[0].label = `امتیاز ${brokerName}`;
        chart.update();
    }

    // onMount runs once after the component is added to the DOM
    onMount(() => {
        const ctx = canvasElement.getContext('2d');
        chart = new ChartJS(ctx, {
            type: 'line', // Now Chart.js knows what 'line' means
            data: {
                labels: [], // Initially empty
                datasets: [{
                    data: [], // Initially empty
                    borderColor: '#88C0D0',
                    tension: 0.4,
                    fill: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: true }
                },
                scales: {
                    x: { display: false },
                    y: { display: false, min: 0, max: 100 } // Set score limits
                }
            }
        });
    });

    // onDestroy cleans up the chart instance when the component is removed
    onDestroy(() => {
        if (chart) {
            chart.destroy();
        }
    });
</script>

<div class="w-full h-16">
    <canvas bind:this={canvasElement}></canvas>
</div>