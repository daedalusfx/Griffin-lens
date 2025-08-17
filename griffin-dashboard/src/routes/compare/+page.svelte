<!-- src/routes/compare/+page.svelte -->
<script>
    import { liveData } from '$lib/liveStore.js';
    import SymbolSelector from '$lib/components/SymbolSelector.svelte';
    import ComparisonChart from '$lib/components/ComparisonChart.svelte';

    const MAX_COMPARE_COUNT = 3;

    // --- تعریف ثابت metrics به اینجا منتقل شد ---
    const metrics = [
        { label: 'Quality Score', key: 'quality_score', isScore: true, fixed: 0 },
        { label: 'Integrity Score', key: 'score_integrity', isScore: true, fixed: 0 },
        { label: 'Avg Spread', key: 'avg_spread', isScore: false, fixed: 2 },
        { label: 'TPS', key: 'tps', isScore: false, fixed: 0 },
        { label: 'Latency (ms)', key: 'avg_latency_ms', isScore: false, fixed: 1 },
    ];

    let selectedBrokers = [];
    let selectedSymbol = '';

    // Get all brokers for the selected symbol
    $: brokersForSymbol = $liveData.data && $liveData.data[selectedSymbol]
        ? Object.keys($liveData.data[selectedSymbol]).sort()
        : [];

    // Filter the full data for only the selected brokers
    $: comparisonData = selectedBrokers.map(name => ({
        name,
        ...($liveData.data[selectedSymbol]?.[name] || {})
    }));

    // Prepare data specifically for the chart component
    $: chartData = comparisonData.map(b => ({
        name: b.name,
        history: b.score_history || []
    }));

    // Helper function for coloring scores in the table
    const getScoreColor = (score = 0) => {
        if (score > 80) return 'text-green-400';
        if (score > 50) return 'text-yellow-400';
        return 'text-red-400';
    };

    function handleBrokerSelection(brokerName) {
        const isSelected = selectedBrokers.includes(brokerName);
        if (isSelected) {
            selectedBrokers = selectedBrokers.filter(b => b !== brokerName);
        } else {
            if (selectedBrokers.length < MAX_COMPARE_COUNT) {
                selectedBrokers = [...selectedBrokers, brokerName];
            } else {
                alert(`You can only compare up to ${MAX_COMPARE_COUNT} brokers.`);
            }
        }
    }

    // Reset selection when symbol changes
    $: if (selectedSymbol) {
        selectedBrokers = [];
    }
</script>

<svelte:head>
    <title>Griffin - Comparison Tool</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
    <header class="text-center mb-10">
        <h1 class="text-3xl sm:text-4xl font-bold text-cyan-400">Broker Comparison Tool</h1>
        <p class="text-gray-400 mt-2">Select up to 3 brokers to compare their performance side-by-side.</p>
    </header>

    <SymbolSelector bind:selectedSymbol symbols={$liveData.data ? Object.keys($liveData.data).sort() : []} />

    <!-- Broker Selector -->
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-10">
        {#each brokersForSymbol as brokerName (brokerName)}
            <button
                on:click={() => handleBrokerSelection(brokerName)}
                class="p-4 rounded-lg text-center font-bold border transition-all {selectedBrokers.includes(brokerName)
                    ? 'bg-cyan-500/20 border-cyan-400'
                    : 'bg-[#3B4252] border-[#4C566A]'}"
            >
                {brokerName}
            </button>
        {/each}
    </div>

    <!-- Comparison Section -->
    {#if selectedBrokers.length > 0}
        <div class="space-y-8">
            <div class="bg-[#3B4252]/60 p-6 rounded-xl border border-[#4C566A]">
                <h2 class="text-xl font-bold text-white mb-4">Quality Score History</h2>
                <ComparisonChart {chartData} />
            </div>

            <div class="bg-[#3B4252]/60 rounded-xl border border-[#4C566A] overflow-hidden">
                <table class="w-full text-center">
                    <thead class="bg-[#3B4252]">
                        <tr>
                            <th class="p-4 text-left">Metric</th>
                            {#each comparisonData as broker}
                                <th class="p-4">{broker.name}</th>
                            {/each}
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-[#434C5E]">
                        <!-- حالا می‌توانیم مستقیماً روی metrics که در اسکریپت تعریف شده، حلقه بزنیم -->
                        {#each metrics as metric}
                            <tr>
                                <td class="p-4 text-left font-semibold text-gray-300">{metric.label}</td>
                                {#each comparisonData as broker}
                                    {@const value = broker[metric.key] || 0}
                                    <td class="p-4 font-mono text-lg {metric.isScore ? getScoreColor(value) : 'text-white'}">
                                        {value.toFixed(metric.fixed)}
                                    </td>
                                {/each}
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    {:else}
        <div class="text-center py-20">
            <p class="text-gray-500">Please select at least one broker to start the comparison.</p>
        </div>
    {/if}
</div>