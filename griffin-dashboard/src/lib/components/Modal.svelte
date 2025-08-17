<script>
    import { createEventDispatcher } from 'svelte';
    import { fly } from 'svelte/transition';
    import Icon from '$lib/components/Icon.svelte';

    /**
     * A reusable modal component.
     * @props {boolean} show - Controls the visibility of the modal.
     * @props {string} title - The title to display in the modal header.
     */
    export let show = false;
    export let title = 'Details';

    const dispatch = createEventDispatcher();

    function closeModal() {
        dispatch('close');
    }

    // Close modal on escape key press
    function handleKeydown(event) {
        if (event.key === 'Escape') {
            closeModal();
        }
    }
</script>

<svelte:window on:keydown={handleKeydown}/>

{#if show}
    <!-- Backdrop -->
    <div
        class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
        on:click={closeModal}
        transition:fly={{ y: 10, duration: 200, opacity: 0 }}
    >
        <!-- Modal Panel -->
        <div
            class="bg-[#3B4252] rounded-xl border border-[#4C566A] shadow-2xl w-full max-w-2xl"
            on:click|stopPropagation
            transition:fly={{ y: -20, duration: 300, opacity: 0 }}
        >
            <!-- Header -->
            <header class="flex items-center justify-between p-4 border-b border-[#4C566A]">
                <h2 class="text-xl font-bold text-white">{title}</h2>
                <button on:click={closeModal} class="text-gray-400 hover:text-white transition-colors">
                    <Icon name="close" className="w-6 h-6" /> <!-- Assuming you add a 'close' icon SVG -->
                </button>
            </header>

            <!-- Content -->
            <div class="p-6 max-h-[70vh] overflow-y-auto">
                <slot /> <!-- The detailed content will be injected here -->
            </div>
        </div>
    </div>
{/if}
