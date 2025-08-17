<script>
	import { liveData } from '$lib/liveStore.js';
	import { slide } from 'svelte/transition';
    import SymbolSelector from '$lib/components/SymbolSelector.svelte';
    import Modal from '$lib/components/Modal.svelte'; // مودال را وارد می‌کنیم
    import Icon from '$lib/components/Icon.svelte';

	let activeTabs = {};

	$: symbols = $liveData.data ? Object.keys($liveData.data).sort() : [];
	let selectedSymbol = '';

	$: selectedSymbolData = $liveData.data ? $liveData.data[selectedSymbol] || {} : {};
	$: sortedBrokers = Object.entries(selectedSymbolData).sort(([, a], [, b]) => (b.quality_score || 0) - (a.quality_score || 0));

	// متغیرهایی برای مدیریت مودال
	let isModalOpen = false;
	let modalData = null; // داده‌های بروکری که در مودال نمایش داده می‌شود

	function showDetails(brokerName, data) {
		modalData = { brokerName, ...data };
		isModalOpen = true;
	}

	function closeModal() {
		isModalOpen = false;
		modalData = null;
	}

	$: if (symbols.length > 0 && !selectedSymbol) {
		selectedSymbol = symbols[0];
	}

	const getScoreColor = (score = 0) => {
		if (score > 80) return 'text-green-400';
		if (score > 50) return 'text-yellow-400';
		return 'text-red-400';
	};
</script>

<svelte:head>
	<title>Griffin - Time Analysis</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
    <header class="text-center mb-6">
        <h1 class="text-4xl font-bold text-white">Time-Series Analysis</h1>
        <p class="text-gray-400 mt-2">Live scores vs. historical performance. Click on any card for full details.</p>
    </header>

	{#if symbols.length > 0}
		<SymbolSelector bind:selectedSymbol {symbols} />

		<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-5">
			{#each sortedBrokers as [brokerName, data] (brokerName)}
				{@const qualityScore = Math.round(data.quality_score || 0)}
				{@const currentTab = activeTabs[brokerName] || 'live'}

				<!-- کارت‌ها اکنون div هستند تا از خطای nesting جلوگیری شود -->
				<div on:click={() => showDetails(brokerName, data)} class="bg-[#3B4252]/60 p-4 rounded-xl border border-[#4C566A] text-left transition-all hover:border-cyan-500 hover:scale-105 cursor-pointer">
					<!-- Header -->
					<div class="flex justify-between items-center">
						<h3 class="text-xl font-bold text-white">{brokerName} {data.is_leader ? '👑' : ''}</h3>
						<div class="text-4xl font-bold {getScoreColor(qualityScore)}">{qualityScore}</div>
					</div>

					<!-- Tabs -->
					<div class="flex border-b border-gray-600 my-3 text-sm">
						<button on:click|stopPropagation={() => (activeTabs[brokerName] = 'live')} class="px-3 py-1 transition-colors relative"
							class:text-cyan-400={currentTab === 'live'} class:text-gray-400={currentTab !== 'live'}>
							Live View
                            {#if currentTab === 'live'} <div class="absolute bottom-[-1px] left-0 right-0 h-0.5 bg-cyan-400"></div> {/if}
						</button>
						<button on:click|stopPropagation={() => (activeTabs[brokerName] = 'trend')} class="px-3 py-1 transition-colors relative"
							class:text-cyan-400={currentTab === 'trend'} class:text-gray-400={currentTab !== 'trend'}>
							Time Analysis
                            {#if currentTab === 'trend'} <div class="absolute bottom-[-1px] left-0 right-0 h-0.5 bg-cyan-400"></div> {/if}
						</button>
					</div>

					<!-- Tab Content -->
					{#if currentTab === 'live'}
						<div transition:slide|local class="min-h-[120px]">
							<div class="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
								<div class="flex justify-between"><span class="text-gray-400">Integrity:</span> <span class="font-semibold {getScoreColor(data.score_integrity)}">{Math.round(data.score_integrity || 0)}</span></div>
								<div class="flex justify-between"><span class="text-gray-400">Authenticity:</span> <span class="font-semibold {getScoreColor(data.score_authenticity)}">{Math.round(data.score_authenticity || 0)}</span></div>
								<div class="flex justify-between"><span class="text-gray-400">Execution:</span> <span class="font-semibold {getScoreColor(data.score_execution)}">{Math.round(data.score_execution || 0)}</span></div>
								<div class="flex justify-between"><span class="text-gray-400">Stability:</span> <span class="font-semibold {getScoreColor(data.score_feed_stability)}">{Math.round(data.score_feed_stability || 0)}</span></div>
                                <div class="flex justify-between col-span-2 border-t border-gray-600 pt-2 mt-1"><span class="text-gray-400">Avg Spread:</span> <span class="font-semibold text-white">{(data.avg_spread || 0).toFixed(1)}</span></div>
                                <div class="flex justify-between"><span class="text-gray-400">TPS:</span> <span class="font-semibold text-white">{data.tps || 0}</span></div>
                                <div class="flex justify-between"><span class="text-gray-400">Latency (ms):</span> <span class="font-semibold text-white">{(data.avg_latency_ms || 0).toFixed(1)}</span></div>
							</div>
						</div>
					{/if}

					{#if currentTab === 'trend'}
						<div transition:slide|local class="min-h-[120px]">
                            <div class="space-y-3 pt-2 text-sm">
                                {#if data.timeframe_averages && Object.keys(data.timeframe_averages).length > 0}
                                    {#each Object.entries(data.timeframe_averages) as [tf, score]}
                                        <div class="flex justify-between items-baseline">
                                            <span class="text-gray-400">Avg {tf}</span>
                                            <span class="text-lg font-bold {getScoreColor(score)}">{Math.round(score)}</span>
                                        </div>
                                    {/each}
                                {:else}
                                    <p class="text-gray-500 text-center pt-8">No historical data yet.</p>
                                {/if}
                            </div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
    {:else if $liveData.status === 'connecting'}
        <p class="text-center text-gray-500 mt-20">Connecting to server...</p>
    {:else}
        <p class="text-center text-gray-500 mt-20">No data available from the server.</p>
    {/if}
</div>

<!-- کامپوننت مودال را به صفحه اضافه می‌کنیم -->
<Modal show={isModalOpen} title="Full Broker Analysis: {modalData?.brokerName}" on:close={closeModal}>
    {#if modalData}
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <!-- بخش امتیازات -->
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
            <!-- بخش معیارهای خام -->
            <div class="space-y-3 bg-gray-900/30 p-4 rounded-lg">
                <h3 class="font-bold text-lg text-white mb-2">Raw Metrics</h3>
                <div class="flex justify-between"><span class="text-gray-300">Avg Spread:</span> <span class="font-mono text-white">{(modalData.avg_spread || 0).toFixed(2)}</span></div>
                <div class="flex justify-between"><span class="text-gray-300">Max Spread:</span> <span class="font-mono text-white">{(modalData.max_spread || 0).toFixed(2)}</span></div>
                <div class="flex justify-between"><span class="text-gray-300">Spread Std Dev:</span> <span class="font-mono text-white">{(modalData.spread_std_dev || 0).toFixed(2)}</span></div>
                <div class="flex justify-between"><span class="text-gray-300">Ticks per Second (TPS):</span> <span class="font-mono text-white">{modalData.tps || 0}</span></div>
                <div class="flex justify-between"><span class="text-gray-300">Avg Latency (ms):</span> <span class="font-mono text-white">{(modalData.avg_latency_ms || 0).toFixed(1)}</span></div>
                <div class="flex justify-between"><span class="text-gray-300">Slippage Asymmetry:</span> <span class="font-mono text-white">{(modalData.asymmetric_slippage_ratio || 0).toFixed(2)}</span></div>
            </div>
            <!-- بخش لاگ گلیچ‌ها -->
            <div class="md:col-span-2 bg-gray-900/30 p-4 rounded-lg">
                <h3 class="font-bold text-lg text-white mb-2">Verified Glitches Log (Last 5)</h3>
                {#if modalData.verified_glitches_log && modalData.verified_glitches_log.length > 0}
                    <ul class="space-y-2">
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
