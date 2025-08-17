<script>
    import { liveData } from '$lib/liveStore.js';
    import BrokerCard from '$lib/components/BrokerCard.svelte';
    import SymbolSelector from '$lib/components/SymbolSelector.svelte';
    import Modal from '$lib/components/Modal.svelte'; // Import the Modal

    // Reactive variables from the store
    $: symbols = $liveData.data ? Object.keys($liveData.data).sort() : [];
    let selectedSymbol = '';

    $: selectedSymbolData = $liveData.data ? ($liveData.data[selectedSymbol] || {}) : {};
    $: sortedBrokers = Object.entries(selectedSymbolData).sort(([, a], [, b]) => (b.quality_score || 0) - (a.quality_score || 0));

    // State for the modal
    let isModalOpen = false;
    let modalData = null;

    // Function to open the modal with the clicked broker's data
    function showDetails(event) {
        modalData = event.detail.data;
        modalData.brokerName = event.detail.brokerName; // Add broker name to data
        isModalOpen = true;
    }

    function closeModal() {
        isModalOpen = false;
        modalData = null;
    }

    // Effect to set the default symbol
    $: if (symbols.length > 0 && !selectedSymbol) {
        selectedSymbol = symbols[0];
    }

    // Helper for score colors in the modal
	const getScoreColor = (score = 0) => {
		if (score > 80) return 'text-green-400';
		if (score > 50) return 'text-yellow-400';
		return 'text-red-400';
	};
</script>

<svelte:head>
    <title>Griffin - Dashboard View</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
    <header class="text-center mb-6">
        <h1 class="text-4xl font-bold text-white">Broker Dashboard</h1>
        <p class="text-gray-400 mt-2">Detailed card view for deep analysis. Click any card for full details.</p>
    </header>

    {#if symbols.length > 0}
        <SymbolSelector bind:selectedSymbol {symbols} />

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {#each sortedBrokers as [brokerName, data] (brokerName)}
                <BrokerCard {brokerName} {data} on:details={showDetails} />
            {/each}
        </div>
    {:else if $liveData.status === 'connecting'}
        <p class="text-center text-gray-500 mt-20">Connecting to server and fetching initial data...</p>
    {:else}
        <p class="text-center text-gray-500 mt-20">No data available from the server. Please ensure the analysis engine is running.</p>
    {/if}
</div>

<Modal show={isModalOpen} title="Full Broker Analysis: {modalData?.brokerName}" on:close={closeModal}>
    {#if modalData}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div class="space-y-3 bg-gray-900/30 p-4 rounded-lg">
                <h3 class="font-bold text-lg text-white mb-2">Core Scores</h3>
                {#each Object.entries(modalData) as [key, value]}
                    {#if key.startsWith('score_')}
                        <div class="flex justify-between items-center">
                            <span class="text-gray-300 capitalize">{key.replace('score_', '').replace('_', ' ')}:</span>
                            <span class="font-bold text-lg {getScoreColor(value)}">{Math.round(value)}</span>
                        </div>
                    {/if}
                {/each}
            </div>
            <div class="space-y-3 bg-gray-900/30 p-4 rounded-lg">
                <h3 class="font-bold text-lg text-white mb-2">Raw Metrics</h3>
                <div class="flex justify-between"><span class="text-gray-300">Avg Spread:</span> <span class="font-mono text-white">{(modalData.avg_spread || 0).toFixed(2)}</span></div>
                <div class="flex justify-between"><span class="text-gray-300">Ticks per Second (TPS):</span> <span class="font-mono text-white">{modalData.tps || 0}</span></div>
                <div class="flex justify-between"><span class="text-gray-300">Avg Latency (ms):</span> <span class="font-mono text-white">{(modalData.avg_latency_ms || 0).toFixed(1)}</span></div>
            </div>
            <div class="md:col-span-2 bg-gray-900/30 p-4 rounded-lg">
                <h3 class="font-bold text-lg text-white mb-2">Verified Glitches Log</h3>
                {#if modalData.verified_glitches_log && modalData.verified_glitches_log.length > 0}
                    <ul class="space-y-2 max-h-48 overflow-y-auto">
                        {#each modalData.verified_glitches_log as glitch}
                            <li class="font-mono text-xs bg-gray-800 p-2 rounded">
                                <span class="text-cyan-400">{glitch.time_str}</span> -
                                <span class="text-gray-300">Price: <span class="text-white">{glitch.bid}</span></span> -
                                <span class="text-red-400">Severity: <span class="text-red-300 font-bold">{Math.round(glitch.severity)}</span></span>
                            </li>
                        {/each}
                    </ul>
                {:else}
                    <p class="text-gray-500">No verified glitches recorded recently.</p>
                {/if}
            </div>
        </div>
    {/if}
</Modal>