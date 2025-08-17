<script>
    import { liveData } from '$lib/liveStore.js';
    import SymbolSelector from '$lib/components/SymbolSelector.svelte';

    $: symbols = $liveData.data ? Object.keys($liveData.data).sort() : [];
    let selectedSymbol = '';

    $: selectedSymbolData = $liveData.data ? ($liveData.data[selectedSymbol] || {}) : {};
    $: sortedBrokers = Object.entries(selectedSymbolData).sort(([, a], [, b]) => (b.quality_score || 0) - (a.quality_score || 0));

    $: if (symbols.length > 0 && !selectedSymbol) {
        selectedSymbol = symbols[0];
    }

    const getScoreColorClass = (score = 0) => {
        if (score > 80) return 'bg-green-500/10 text-green-300';
        if (score > 50) return 'bg-yellow-500/10 text-yellow-300';
        return 'bg-red-500/10 text-red-300';
    };

    // Add the two missing headers
    const headers = [
        { key: 'score_authenticity', label: 'Authenticity' },
        { key: 'score_integrity', label: 'Integrity' },
        { key: 'score_execution', label: 'Execution' },
        { key: 'score_feed_stability', label: 'Feed Stability' },
        { key: 'score_spread_stability', label: 'Spread Stability' },
        { key: 'score_quote_freeze', label: 'Quote Freeze' }
    ];
</script>

<svelte:head>
    <title>Griffin - Matrix View</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
    <header class="text-center mb-6">
        <h1 class="text-4xl font-bold text-white">Heatmap Matrix</h1>
        <p class="text-gray-400 mt-2">High-density view for quick performance comparison.</p>
    </header>

    {#if symbols.length > 0}
        <SymbolSelector bind:selectedSymbol {symbols} />

        <div class="overflow-x-auto bg-[#3B4252]/60 rounded-xl border border-[#4C566A]">
            <table class="w-full min-w-[900px]">
                <thead class="border-b border-[#4C566A]">
                    <tr class="text-sm text-gray-300">
                        <th class="p-4 text-left font-semibold">Broker</th>
                        <th class="p-4 text-center font-semibold">Final Score</th>
                        {#each headers as header}
                            <th class="p-4 text-center font-semibold">{header.label}</th>
                        {/each}
                    </tr>
                </thead>
                <tbody>
                    {#each sortedBrokers as [brokerName, data] (brokerName)}
                        <tr class="border-b border-[#434C5E] last:border-none hover:bg-gray-700/30 transition-colors">
                            <td class="p-4 font-bold text-left text-white">{brokerName} {data.is_leader ? '👑' : ''}</td>
                            <td class="p-4 text-xl font-bold text-center text-cyan-300">{Math.round(data.quality_score || 0)}</td>
                            {#each headers as header}
                                <td class="p-4 text-center font-semibold text-lg {getScoreColorClass(data[header.key])}">
                                    {Math.round(data[header.key] || 0)}
                                </td>
                            {/each}
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {:else if $liveData.status === 'connecting'}
        <p class="text-center text-gray-500 mt-20">Connecting to server...</p>
    {:else}
        <p class="text-center text-gray-500 mt-20">No data available from the server.</p>
    {/if}
</div>