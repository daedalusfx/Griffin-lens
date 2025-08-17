<script>
    /**
     * A small visual indicator for active/frozen status.
     * @props {boolean} isFrozen - The frozen state.
     */
    export let isFrozen;

    // Add the animation class when not frozen
    const animationClass = 'animate-[pulse_2s_infinite]';
</script>

<div class="flex items-center space-x-2 mt-1">
    <span
        class="h-2.5 w-2.5 rounded-full"
        class:bg-red-500={isFrozen}
        class:bg-green-500={!isFrozen}
        class:animate-pulse={!isFrozen}
    ></span>
    <span class="text-sm {isFrozen ? 'text-red-400' : 'text-green-400'}">
        {isFrozen ? 'Frozen' : 'Active'}
    </span>
</div>