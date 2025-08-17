<!-- src/routes/alerts/+page.svelte -->
<script>
    import { onMount } from 'svelte';
    import { liveData } from '$lib/liveStore.js';
    import SymbolSelector from '$lib/components/SymbolSelector.svelte';

    let activeRules = [];
    let triggeredAlerts = [];
    let notificationPermission = 'default';
    let selectedSymbol = '';

    // Form state
    let ruleBroker = '';
    let ruleMetricKey = 'quality_score';
    let ruleCondition = 'below';
    let ruleValue = 80;

    // Available metrics for alerts
    const ALERTABLE_METRICS = [
        { key: 'quality_score', name: 'Quality Score' },
        { key: 'score_integrity', name: 'Integrity Score' },
        { key: 'avg_spread', name: 'Average Spread' },
        { key: 'avg_latency_ms', name: 'Latency (ms)' }
    ];

    // Get brokers for the selected symbol
    $: brokersForSymbol = $liveData.data && $liveData.data[selectedSymbol]
        ? Object.keys($liveData.data[selectedSymbol]).sort()
        : [];

    // --- Notification Logic ---
    onMount(() => {
        if ("Notification" in window) {
            Notification.requestPermission().then(permission => {
                notificationPermission = permission;
            });
        }
    });

    function showNotification(title, body) {
        if (notificationPermission === 'granted') {
            new Notification(title, { body, icon: 'https://placehold.co/48x48/88C0D0/2E3440?text=G' });
        }
    }

    // --- Alerting Logic ---
    // This reactive block runs whenever live data or rules change
    $: if ($liveData.data && selectedSymbol && $liveData.data[selectedSymbol]) {
        const symbolData = $liveData.data[selectedSymbol];
        activeRules.forEach(rule => {
            if (rule.symbol !== selectedSymbol || !symbolData[rule.broker]) return;

            const currentValue = symbolData[rule.broker][rule.metric.key];
            let isTriggered = false;
            if (rule.condition === 'below' && currentValue < rule.value) isTriggered = true;
            if (rule.condition === 'above' && currentValue > rule.value) isTriggered = true;

            const now = Date.now();
            if (isTriggered && (now - (rule.lastTriggered || 0) > 30000)) { // 30s cooldown
                rule.lastTriggered = now;
                const alertLog = {
                    id: now,
                    time: new Date().toLocaleTimeString(),
                    message: `ALERT: ${rule.broker}'s ${rule.metric.name} went ${rule.condition} ${rule.value}. Current: ${currentValue.toFixed(2)}.`
                };
                triggeredAlerts = [alertLog, ...triggeredAlerts];
                showNotification(`Griffin Alert: ${rule.broker}`, alertLog.message.substring(alertLog.message.indexOf(':') + 2));
            }
        });
    }

    function addAlertRule() {
        if (!ruleBroker || !ruleValue) {
            alert('Please fill all fields.');
            return;
        }
        activeRules = [
            ...activeRules,
            {
                id: Date.now(),
                symbol: selectedSymbol,
                broker: ruleBroker,
                metric: ALERTABLE_METRICS.find(m => m.key === ruleMetricKey),
                condition: ruleCondition,
                value: parseFloat(ruleValue),
            }
        ];
    }

    function removeRule(id) {
        activeRules = activeRules.filter(r => r.id !== id);
    }

    // Set default broker when symbol changes
    $: if (brokersForSymbol.length > 0) {
        ruleBroker = brokersForSymbol[0];
    }
</script>

<svelte:head>
    <title>Griffin - Alerts & Notifications</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
    <header class="text-center mb-10">
        <h1 class="text-3xl sm:text-4xl font-bold text-cyan-400">Alerts & Notifications</h1>
        <p class="text-gray-400 mt-2">Define custom rules and receive desktop notifications for critical events.</p>
    </header>

    <SymbolSelector bind:selectedSymbol symbols={$liveData.data ? Object.keys($liveData.data).sort() : []} />

    {#if selectedSymbol}
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- Create Alert Form -->
            <div class="lg:col-span-1">
                <form on:submit|preventDefault={addAlertRule} class="bg-[#3B4252]/60 p-6 rounded-xl border border-[#4C566A] space-y-4">
                    <h2 class="text-xl font-bold text-white">Create New Alert Rule</h2>
                    <div>
                        <label class="block text-sm mb-1">Broker</label>
                        <select bind:value={ruleBroker} class="w-full p-2 rounded-md bg-[#3B4252] border border-[#4C566A]">
                            {#each brokersForSymbol as broker} <option value={broker}>{broker}</option> {/each}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">Metric</label>
                        <select bind:value={ruleMetricKey} class="w-full p-2 rounded-md bg-[#3B4252] border border-[#4C566A]">
                            {#each ALERTABLE_METRICS as metric} <option value={metric.key}>{metric.name}</option> {/each}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">Condition</label>
                        <select bind:value={ruleCondition} class="w-full p-2 rounded-md bg-[#3B4252] border border-[#4C566A]">
                            <option value="below">Drops Below</option>
                            <option value="above">Goes Above</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm mb-1">Value</label>
                        <input type="number" step="any" bind:value={ruleValue} class="w-full p-2 rounded-md bg-[#3B4252] border border-[#4C566A]" required>
                    </div>
                    <button type="submit" class="w-full font-bold py-2 px-4 rounded-md bg-[#81A1C1] text-[#2E3440] hover:bg-[#88C0D0]">Add Rule</button>
                </form>
            </div>

            <!-- Active Rules & Log -->
            <div class="lg:col-span-2 space-y-8">
                <div class="bg-[#3B4252]/60 p-6 rounded-xl border border-[#4C566A]">
                    <h2 class="text-xl font-bold text-white mb-4">Active Rules for {selectedSymbol}</h2>
                    <div class="space-y-3">
                        {#each activeRules.filter(r => r.symbol === selectedSymbol) as rule (rule.id)}
                            <div class="flex justify-between items-center bg-gray-700/50 p-3 rounded-md">
                                <span class="text-sm">
                                    <strong>{rule.broker}</strong>: If <strong>{rule.metric.name}</strong> goes <strong>{rule.condition} {rule.value}</strong>
                                </span>
                                <button on:click={() => removeRule(rule.id)} class="text-red-400 hover:text-red-300 font-bold">&times;</button>
                            </div>
                        {:else}
                            <p class="text-gray-500">No alert rules defined for this symbol yet.</p>
                        {/each}
                    </div>
                </div>
                <div class="bg-[#3B4252]/60 p-6 rounded-xl border border-[#4C566A]">
                    <h2 class="text-xl font-bold text-white mb-4">Triggered Alerts Log</h2>
                    <div class="space-y-3 max-h-96 overflow-y-auto">
                        {#each triggeredAlerts as alert (alert.id)}
                            <div class="font-mono text-sm bg-red-900/50 p-2 rounded">{alert.message}</div>
                        {:else}
                            <p class="text-gray-500">Waiting for alerts to be triggered...</p>
                        {/each}
                    </div>
                </div>
            </div>
        </div>
    {:else}
        <p class="text-center text-gray-500 mt-20">Please select a symbol to configure alerts.</p>
    {/if}
</div>