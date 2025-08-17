<script>
  /**
   * A circular SVG ring to display a score from 0-100.
   * @props {number} score - The score to display (0-100).
   */
  export let score = 0;

  const circumference = 2 * Math.PI * 40; // 2 * pi * radius

  // Reactive calculations for the ring color and stroke offset
  $: ringColor = score > 80 ? 'stroke-green-400' : score > 50 ? 'stroke-yellow-400' : 'stroke-red-500';
  $: scoreOffset = circumference - (score / 100) * circumference;
</script>

<div class="relative w-24 h-24 flex-shrink-0">
  <svg class="w-full h-full" viewBox="0 0 100 100">
    <circle
      class="text-gray-600"
      stroke-width="8"
      stroke="currentColor"
      fill="transparent"
      r="40"
      cx="50"
      cy="50"
    />
    <circle
      class="transition-all duration-700 ease-out {ringColor}"
      style="transform: rotate(-90deg); transform-origin: 50% 50%;"
      stroke-width="8"
      stroke-dasharray={circumference}
      stroke-dashoffset={scoreOffset}
      stroke-linecap="round"
      fill="transparent"
      r="40"
      cx="50"
      cy="50"
    />
  </svg>
  <div class="absolute inset-0 flex items-center justify-center">
    <span class="text-2xl font-bold text-white">{Math.round(score)}</span>
  </div>
</div>