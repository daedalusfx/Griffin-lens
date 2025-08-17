<script>
    import Icon from '$lib/components/Icon.svelte';
</script>

<svelte:head>
    <title>Griffin - Home</title>
</svelte:head>

<div class="max-w-4xl mx-auto text-center">
    <div class="mt-12 sm:mt-20">
        <Icon name="logo" class="w-24 h-24 text-cyan-400 mx-auto mb-6" />
        <h1 class="text-5xl font-bold text-white mb-4">Griffin Analysis Engine</h1>
        <p class="text-xl text-gray-400 max-w-2xl mx-auto">
            Your real-time, data-driven solution for monitoring and evaluating broker feed quality with unparalleled precision.
        </p>
    </div>

    <div class="grid md:grid-cols-2 gap-8 mt-24 text-left">
        <!-- Link to Dashboard View -->
        <a href="/dashboard" class="block p-8 bg-[#3B4252] rounded-xl border border-[#4C566A] hover:border-cyan-400 transition-all hover:scale-105 hover:shadow-2xl group">
            <Icon name="dashboard" class="w-10 h-10 text-cyan-400 mb-4" />
            <h2 class="text-2xl font-bold text-white mb-2">Dashboard View</h2>
            <p class="text-gray-300 group-hover:text-white transition-colors">A detailed, card-based view for each broker. Perfect for deep-diving into individual performance, complete with score history and key performance indicators.</p>
        </a>

        <!-- Link to Matrix View -->
        <a href="/matrix" class="block p-8 bg-[#3B4252] rounded-xl border border-[#4C566A] hover:border-cyan-400 transition-all hover:scale-105 hover:shadow-2xl group">
            <Icon name="matrix" class="w-10 h-10 text-cyan-400 mb-4" />
            <h2 class="text-2xl font-bold text-white mb-2">Matrix View</h2>
            <p class="text-gray-300 group-hover:text-white transition-colors">A high-density, color-coded table for at-a-glance comparison of all broker metrics. Instantly identify weaknesses and outliers across the board.</p>
        </a>

        <!-- Link to Time Analysis View -->
        <a href="/time" class="block p-8 bg-[#3B4252] rounded-xl border border-[#4C566A] hover:border-cyan-400 transition-all hover:scale-105 hover:shadow-2xl group md:col-span-2">
            <Icon name="time" class="w-10 h-10 text-cyan-400 mb-4" />
            <h2 class="text-2xl font-bold text-white mb-2">Time-Series Analysis</h2>
            <p class="text-gray-300 group-hover:text-white transition-colors">Compare live scores against historical performance averages. This view provides context by showing broker quality over various timeframes, from minutes to hours.</p>
        </a>
    </div>
</div>
