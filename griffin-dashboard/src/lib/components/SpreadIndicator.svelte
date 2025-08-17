<!-- src/lib/components/SpreadIndicator.svelte -->
<script>
    /**
     * Displays live spread dynamically colored against the average spread.
     * @props {number} current - The current live spread.
     * @props {number} avg - The average spread.
     * @props {number} fixed - The number of decimal places to show.
     * @props {string} className - Additional CSS classes for styling the text.
     */
    export let current = 0;
    export let avg = 0;
    export let fixed = 2;
    export let className = 'text-base';

    let colorClass = 'text-green-400';

    // Reactive block to determine the color of the live spread
    $: {
        const average = avg || 0;
        const live = current || 0;
        
        // If live spread is 50% higher than average, it's a spike (red)
        if (live > average * 1.5 && average > 0) {
            colorClass = 'text-red-400';
        // If live spread is 20% higher than average, it's widening (yellow)
        } else if (live > average * 1.2 && average > 0) {
            colorClass = 'text-yellow-400';
        // Otherwise, it's stable (green)
        } else {
            colorClass = 'text-green-400';
        }
    }
</script>

<div class="flex flex-col items-center justify-center">
    <!-- Live Spread (Large and Colored) -->
    <p class="font-semibold transition-colors {className} {colorClass}">
        {current.toFixed(fixed)}
    </p>
    <!-- Average Spread (Small and Gray) -->
    <p class="text-xs text-gray-400 -mt-1" title="Average Spread">
        Avg: {avg.toFixed(fixed)}
    </p>
</div>
