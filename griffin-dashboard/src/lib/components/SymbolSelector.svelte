<script>
    /**
     * A reusable dropdown component for selecting a financial symbol.
     * @props {string[]} symbols - An array of symbol strings to display.
     * @props {string} selectedSymbol - The currently selected symbol (bindable).
     */
    export let symbols = [];
    export let selectedSymbol = '';
  </script>
  
  {#if symbols.length > 0}
    <div class="max-w-xs mx-auto mb-10">
      <select
        bind:value={selectedSymbol}
        class="w-full p-3 rounded-lg text-center font-semibold bg-[#3B4252] border-2 border-[#4C566A] focus:border-cyan-500 focus:ring-cyan-500 transition-all"
        aria-label="Select Symbol"
      >
        {#each symbols as symbol}
          <option value={symbol}>{symbol}</option>
        {/each}
      </select>
    </div>
  {/if}
  