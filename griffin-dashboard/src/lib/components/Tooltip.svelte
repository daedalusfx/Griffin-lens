<script>
    /**
     * A simple tooltip component.
     * @props {string} text - The text to display in the tooltip.
     */
    export let text = '';
  </script>
  
  <div class="relative flex items-center group">
    <slot />
    {#if text}
      <div
        class="absolute bottom-full mb-2 w-max max-w-xs px-3 py-1.5 text-sm font-semibold text-white bg-[#4C566A] rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10 pointer-events-none"
      >
        {text}
      </div>
    {/if}
  </div>