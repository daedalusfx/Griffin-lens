<script>
    import { createEventDispatcher } from 'svelte';
    import StatusIndicator from '$lib/components/StatusIndicator.svelte';
    import ScoreRing from '$lib/components/ScoreRing.svelte';
    import Tooltip from '$lib/components/Tooltip.svelte';

    /**
     * @props {string} brokerName - The name of the broker.
     * @props {object} data - The analysis data object for the broker.
     */
    export let brokerName;
    export let data;

    const dispatch = createEventDispatcher();

    // Helper to determine text color based on score
    $: scoreColor = (score = 0) => {
        if (score > 80) return 'text-green-400';
        if (score > 50) return 'text-yellow-400';
        return 'text-red-500';
    };

    function showDetails() {
        dispatch('details', { brokerName, data });
    }
</script>

<div
    on:click={showDetails}
    class="bg-[#3B4252]/60 backdrop-blur-sm p-5 rounded-xl border border-[#4C566A] flex flex-col justify-between transition-all hover:border-cyan-500 hover:scale-[1.03] hover:shadow-2xl cursor-pointer"
    role="button"
    tabindex="0"
    on:keydown={(e) => e.key === 'Enter' && showDetails()}
>
    <div class="flex justify-between items-start mb-4">
        <div class="flex-grow">
            <h3 class="text-xl font-bold text-white truncate pr-2">{brokerName} {data.is_leader ? '👑' : ''}</h3>
            <StatusIndicator isFrozen={data.is_frozen} />
        </div>
        <ScoreRing score={data.quality_score || 0} />
    </div>

    <div class="grid grid-cols-2 gap-x-4 gap-y-5 text-center my-4">
        <Tooltip text="100 minus glitch penalties. Click card for log.">
            <div class="metric-card">
                <p class="text-sm">Integrity</p>
                <p class="text-3xl {scoreColor(data.score_integrity || 0)} mt-1">
                    {Math.round(data.score_integrity || 0)}
                </p>
            </div>
        </Tooltip>
        <Tooltip text="Feed similarity to the true market data.">
            <div>
                <p class="text-sm">Authenticity</p>
                <p class="text-3xl {scoreColor(data.score_authenticity || 0)} mt-1">
                    {Math.round(data.score_authenticity || 0)}
                </p>
            </div>
        </Tooltip>
        <Tooltip text="Based on slippage asymmetry. Higher is better.">
            <div>
                <p class="text-sm">Execution</p>
                <p class="text-3xl {scoreColor(data.score_execution || 0)} mt-1">
                    {Math.round(data.score_execution || 0)}
                </p>
            </div>
        </Tooltip>
        <Tooltip text="Score based on the time of the last tick.">
            <div>
                <p class="text-sm">Feed Stability</p>
                <p class="text-3xl {scoreColor(data.score_feed_stability || 0)} mt-1">
                    {Math.round(data.score_feed_stability || 0)}
                </p>
            </div>
        </Tooltip>
    </div>

    <div class="text-center bg-gray-900/30 p-3 rounded-lg mt-4">
        <div class="grid grid-cols-3 gap-2">
            <div>
                <p class="text-gray-400 text-xs">Spread</p>
                <p class="text-white text-base font-semibold">{(data.avg_spread || 0).toFixed(1)}</p>
            </div>
            <div>
                <p class="text-gray-400 text-xs">TPS</p>
                <p class="text-white text-base font-semibold">{data.tps || 0}</p>
            </div>
            <div>
                <p class="text-gray-400 text-xs">Latency (ms)</p>
                <p class="text-white text-base font-semibold">{(data.avg_latency_ms || 0).toFixed(1)}</p>
            </div>
        </div>
    </div>
</div>