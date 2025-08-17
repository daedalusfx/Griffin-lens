<script>
    import { liveData } from '$lib/liveStore.js';
    import { onDestroy } from 'svelte';
    import { fly } from 'svelte/transition';
    import Icon from '$lib/components/Icon.svelte';

    let status = $liveData.status;
    let visible = true;
    let timer;

    // یک آبجکت برای مدیریت ظاهر هر وضعیت
    const statusConfig = {
        connected: {
            text: 'Connected',
            color: 'text-green-300',
            icon: 'check-circle',
            animation: ''
        },
        connecting: {
            text: 'Connecting...',
            color: 'text-yellow-300',
            icon: 'loader',
            animation: 'animate-spin'
        },
        disconnected: {
            text: 'Connection Lost',
            color: 'text-red-400',
            icon: 'alert-triangle',
            animation: ''
        }
    };

    // با هر بار تغییر وضعیت، این بلوک کد اجرا می‌شود
    $: {
        status = $liveData.status;
        clearTimeout(timer);

        if (status === 'connected') {
            visible = true;
            // پیام "Connected" بعد از 2.5 ثانیه محو می‌شود
            timer = setTimeout(() => {
                visible = false;
            }, 2500);
        } else {
            // وضعیت‌های دیگر همیشه نمایش داده می‌شوند
            visible = true;
        }
    }

    // هنگام حذف کامپوننت، تایمر را پاک می‌کنیم
    onDestroy(() => {
        clearTimeout(timer);
    });

    $: currentConfig = statusConfig[status];
</script>

{#if visible}
    <div
        in:fly={{ y: -10, duration: 300 }}
        out:fly={{ y: -10, duration: 300 }}
        class="flex items-center space-x-2 text-sm font-semibold {currentConfig.color}"
    >
        <Icon name={currentConfig.icon} className="w-5 h-5 {currentConfig.animation}" />
        <span class="hidden sm:inline">{currentConfig.text}</span>
    </div>
{/if}