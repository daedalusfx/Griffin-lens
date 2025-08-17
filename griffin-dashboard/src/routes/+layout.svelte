<script>
	import '../app.css';
	import { page } from '$app/stores';
	import Icon from '$lib/components/Icon.svelte';
    import ConnectionStatus from '$lib/components/ConnectionStatus.svelte'; // کامپوننت جدید را وارد می‌کنیم

	// Navigation links for the header
	const navLinks = [
	  { href: '/', label: 'Home', icon: 'home' },
	  { href: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
	  { href: '/matrix', label: 'Matrix', icon: 'matrix' },
	  { href: '/time', label: 'Time Analysis', icon: 'time' }
	];
</script>

<div class="min-h-screen bg-[#2E3440] text-[#D8DEE9] font-sans">
	<header class="bg-[#3B4252]/50 p-4 shadow-lg sticky top-0 backdrop-blur-md z-50 border-b border-[#4C566A]/50">
	  <nav class="max-w-7xl mx-auto flex justify-between items-center">
		<a href="/" class="flex items-center space-x-3">
		  <Icon name="logo" class="w-8 h-8 text-cyan-400" />
		  <span class="text-2xl font-bold text-cyan-400 hidden sm:inline">Griffin</span>
		</a>
		<div class="flex items-center space-x-2 sm:space-x-4">
          <ConnectionStatus />

		  {#each navLinks as link}
			{@const isActive = $page.url.pathname === link.href}
			<a href={link.href} class="px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center space-x-2 {isActive ? 'bg-cyan-400/10 text-cyan-300' : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'}">
			  <Icon name={link.icon} class="w-5 h-5" />
			  <span class="hidden md:inline">{link.label}</span>
			</a>
		  {/each}
		</div>
	  </nav>
	</header>

	<main class="p-4 sm:p-8">
	  <slot />
	</main>

	</div>