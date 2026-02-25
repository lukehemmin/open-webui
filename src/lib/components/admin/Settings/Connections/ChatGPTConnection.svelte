<script lang="ts">
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Cog6 from '$lib/components/icons/Cog6.svelte';

	export let chatgptOAuthStatus: {
		connected: boolean;
		expires_at: number | null;
		expired: boolean;
	} | null = null;

	export let onLogin: () => void = () => {};
	export let onDisconnect: () => void = () => {};
	export let onConfigure: () => void = () => {};
</script>

<div class="flex w-full gap-2 items-center">
	<Tooltip
		className="w-full relative"
		content="https://api.openai.com/v1"
		placement="top-start"
	>
		{#if !(chatgptOAuthStatus?.connected && !chatgptOAuthStatus?.expired)}
			<div class="absolute top-0 bottom-0 left-0 right-0 opacity-40 bg-white dark:bg-gray-900 z-10 rounded-lg pointer-events-none"></div>
		{/if}

		<div class="flex w-full items-center gap-2 px-2 py-1.5 rounded-lg bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-700">
			<!-- ChatGPT 로고 아이콘 -->
			<div class="shrink-0 flex items-center justify-center w-5 h-5">
				<svg viewBox="0 0 41 41" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-700 dark:text-gray-300" fill="currentColor">
					<path d="M37.532 16.87a9.963 9.963 0 0 0-.856-8.184 10.078 10.078 0 0 0-10.855-4.835 9.964 9.964 0 0 0-7.505-3.348 10.079 10.079 0 0 0-9.612 6.977 9.967 9.967 0 0 0-6.664 4.834 10.08 10.08 0 0 0 1.24 11.817 9.965 9.965 0 0 0 .856 8.185 10.079 10.079 0 0 0 10.855 4.835 9.965 9.965 0 0 0 7.504 3.347 10.078 10.078 0 0 0 9.617-6.981 9.967 9.967 0 0 0 6.663-4.834 10.079 10.079 0 0 0-1.243-11.813zM22.498 37.886a7.474 7.474 0 0 1-4.799-1.735c.061-.033.168-.091.237-.134l7.964-4.6a1.294 1.294 0 0 0 .655-1.134V19.054l3.366 1.944a.12.12 0 0 1 .066.092v9.299a7.505 7.505 0 0 1-7.49 7.496zM6.392 31.006a7.471 7.471 0 0 1-.894-5.023c.06.036.162.099.237.141l7.964 4.6a1.297 1.297 0 0 0 1.308 0l9.724-5.614v3.888a.12.12 0 0 1-.048.103l-8.051 4.649a7.504 7.504 0 0 1-10.24-2.744zM4.297 13.62A7.469 7.469 0 0 1 8.2 10.333c0 .068-.004.19-.004.274v9.201a1.294 1.294 0 0 0 .654 1.132l9.723 5.614-3.366 1.944a.12.12 0 0 1-.114.012L7.044 23.86a7.504 7.504 0 0 1-2.747-10.24zm27.658 6.437l-9.724-5.615 3.367-1.943a.121.121 0 0 1 .114-.012l8.048 4.648a7.498 7.498 0 0 1-1.158 13.528v-9.476a1.293 1.293 0 0 0-.647-1.13zm3.35-5.043c-.059-.037-.162-.099-.236-.141l-7.965-4.6a1.298 1.298 0 0 0-1.308 0l-9.723 5.614v-3.888a.12.12 0 0 1 .048-.103l8.05-4.645a7.497 7.497 0 0 1 11.135 7.763zm-21.063 6.929l-3.367-1.944a.12.12 0 0 1-.065-.092v-9.299a7.497 7.497 0 0 1 12.293-5.756 6.94 6.94 0 0 0-.236.134l-7.965 4.6a1.294 1.294 0 0 0-.654 1.132l-.006 11.225zm1.829-3.943l4.33-2.501 4.332 2.5v4.999l-4.331 2.5-4.331-2.5V18z"/>
				</svg>
			</div>

			<!-- URL 표시 -->
			<div class="flex-1 min-w-0">
				<div class="text-sm truncate text-gray-700 dark:text-gray-300">https://api.openai.com/v1</div>
			</div>

			<!-- 상태 표시 (API Key 자리에) -->
			<div class="shrink-0">
				{#if chatgptOAuthStatus?.connected && !chatgptOAuthStatus?.expired}
					<div class="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 px-2">
						<div class="w-1.5 h-1.5 rounded-full bg-green-500"></div>
						<span>{$i18n.t('Connected')}</span>
					</div>
				{:else if chatgptOAuthStatus?.connected && chatgptOAuthStatus?.expired}
					<div class="flex items-center gap-1 text-xs text-yellow-600 dark:text-yellow-400 px-2">
						<div class="w-1.5 h-1.5 rounded-full bg-yellow-500"></div>
						<span>{$i18n.t('Expired')}</span>
					</div>
				{:else}
					<div class="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500 px-2">
						<div class="w-1.5 h-1.5 rounded-full bg-gray-300 dark:bg-gray-600"></div>
						<span>{$i18n.t('Not Connected')}</span>
					</div>
				{/if}
			</div>
		</div>
	</Tooltip>

	<div class="flex gap-1 shrink-0">
		{#if chatgptOAuthStatus?.connected && !chatgptOAuthStatus?.expired}
			<Tooltip content={$i18n.t('Disconnect')}>
				<button
					class="self-center p-1 bg-transparent hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 rounded-lg transition text-red-500 hover:text-red-600"
					on:click={onDisconnect}
					type="button"
				>
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
						<path fill-rule="evenodd" d="M3 4.25A2.25 2.25 0 0 1 5.25 2h5.5A2.25 2.25 0 0 1 13 4.25v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 0-.75-.75h-5.5a.75.75 0 0 0-.75.75v11.5c0 .414.336.75.75.75h5.5a.75.75 0 0 0 .75-.75v-2a.75.75 0 0 1 1.5 0v2A2.25 2.25 0 0 1 10.75 18h-5.5A2.25 2.25 0 0 1 3 15.75V4.25Z" clip-rule="evenodd" />
						<path fill-rule="evenodd" d="M6 10a.75.75 0 0 1 .75-.75h9.546l-1.048-.943a.75.75 0 1 1 1.004-1.114l2.5 2.25a.75.75 0 0 1 0 1.114l-2.5 2.25a.75.75 0 1 1-1.004-1.114l1.048-.943H6.75A.75.75 0 0 1 6 10Z" clip-rule="evenodd" />
					</svg>
				</button>
			</Tooltip>
		{:else}
			<Tooltip content={$i18n.t('Login')}>
				<button
					class="self-center p-1 bg-transparent hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 rounded-lg transition text-blue-500 hover:text-blue-600"
					on:click={onLogin}
					type="button"
				>
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
						<path fill-rule="evenodd" d="M3 4.25A2.25 2.25 0 0 1 5.25 2h5.5A2.25 2.25 0 0 1 13 4.25v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 0-.75-.75h-5.5a.75.75 0 0 0-.75.75v11.5c0 .414.336.75.75.75h5.5a.75.75 0 0 0 .75-.75v-2a.75.75 0 0 1 1.5 0v2A2.25 2.25 0 0 1 10.75 18h-5.5A2.25 2.25 0 0 1 3 15.75V4.25Z" clip-rule="evenodd" />
						<path fill-rule="evenodd" d="M16.53 8.22a.75.75 0 0 1 0 1.06l-1.72 1.72h6.44a.75.75 0 0 1 0 1.5H14.81l1.72 1.72a.75.75 0 1 1-1.06 1.06l-3-3a.75.75 0 0 1 0-1.06l3-3a.75.75 0 0 1 1.06 0Z" clip-rule="evenodd" transform="rotate(180 10 10)" />
					</svg>
				</button>
			</Tooltip>
		{/if}

		<Tooltip content={$i18n.t('Configure')}>
			<button
				class="self-center p-1 bg-transparent hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 rounded-lg transition"
				on:click={onConfigure}
				type="button"
			>
				<Cog6 />
			</button>
		</Tooltip>
	</div>
</div>
