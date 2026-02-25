<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext, onDestroy } from 'svelte';
	const i18n = getContext('i18n');

	import {
		initiateChatGPTOAuth,
		handleChatGPTOAuthCallback
	} from '$lib/apis/openai';

	import Modal from '$lib/components/common/Modal.svelte';

	export let show = false;
	export let onConnected: () => void = () => {};

	// 고정 Redirect URI — OpenAI OAuth 앱에 등록된 값, 변경 불가
	const REDIRECT_URI = 'http://localhost:1455/auth/callback';

	let step: 'ready' | 'waiting' = 'ready';
	let callbackUrl = '';
	let loading = false;

	const startLogin = async () => {
		try {
			const data = await initiateChatGPTOAuth(localStorage.token);
			// 브라우저에서 ChatGPT 로그인 페이지 오픈
			window.open(data.auth_url, '_blank');
			step = 'waiting';
		} catch (e) {
			toast.error(`${e}`);
		}
	};

	const submitCallback = async () => {
		if (!callbackUrl.trim()) {
			toast.error($i18n.t('Please paste the redirect URL from your browser.'));
			return;
		}
		loading = true;
		try {
			await handleChatGPTOAuthCallback(localStorage.token, callbackUrl.trim());
			toast.success($i18n.t('ChatGPT account connected successfully'));
			onConnected();
			closeModal();
		} catch (e: any) {
			const detail = e?.detail ?? `${e}`;
			toast.error(detail);
		} finally {
			loading = false;
		}
	};

	const copyRedirectUri = () => {
		navigator.clipboard.writeText(REDIRECT_URI).then(() => {
			toast.success($i18n.t('Copied to clipboard'));
		});
	};

	const closeModal = () => {
		show = false;
		step = 'ready';
		callbackUrl = '';
		loading = false;
	};

	$: if (show) {
		step = 'ready';
		callbackUrl = '';
	}
</script>

<Modal size="sm" bind:show on:close={closeModal}>
	<div>
		<!-- 헤더 -->
		<div class="flex justify-between dark:text-gray-100 px-5 pt-4 pb-3">
			<div class="flex items-center gap-2">
				<svg viewBox="0 0 41 41" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" fill="currentColor">
					<path d="M37.532 16.87a9.963 9.963 0 0 0-.856-8.184 10.078 10.078 0 0 0-10.855-4.835 9.964 9.964 0 0 0-7.505-3.348 10.079 10.079 0 0 0-9.612 6.977 9.967 9.967 0 0 0-6.664 4.834 10.08 10.08 0 0 0 1.24 11.817 9.965 9.965 0 0 0 .856 8.185 10.079 10.079 0 0 0 10.855 4.835 9.965 9.965 0 0 0 7.504 3.347 10.078 10.078 0 0 0 9.617-6.981 9.967 9.967 0 0 0 6.663-4.834 10.079 10.079 0 0 0-1.243-11.813zM22.498 37.886a7.474 7.474 0 0 1-4.799-1.735c.061-.033.168-.091.237-.134l7.964-4.6a1.294 1.294 0 0 0 .655-1.134V19.054l3.366 1.944a.12.12 0 0 1 .066.092v9.299a7.505 7.505 0 0 1-7.49 7.496zM6.392 31.006a7.471 7.471 0 0 1-.894-5.023c.06.036.162.099.237.141l7.964 4.6a1.297 1.297 0 0 0 1.308 0l9.724-5.614v3.888a.12.12 0 0 1-.048.103l-8.051 4.649a7.504 7.504 0 0 1-10.24-2.744zM4.297 13.62A7.469 7.469 0 0 1 8.2 10.333c0 .068-.004.19-.004.274v9.201a1.294 1.294 0 0 0 .654 1.132l9.723 5.614-3.366 1.944a.12.12 0 0 1-.114.012L7.044 23.86a7.504 7.504 0 0 1-2.747-10.24zm27.658 6.437l-9.724-5.615 3.367-1.943a.121.121 0 0 1 .114-.012l8.048 4.648a7.498 7.498 0 0 1-1.158 13.528v-9.476a1.293 1.293 0 0 0-.647-1.13zm3.35-5.043c-.059-.037-.162-.099-.236-.141l-7.965-4.6a1.298 1.298 0 0 0-1.308 0l-9.723 5.614v-3.888a.12.12 0 0 1 .048-.103l8.05-4.645a7.497 7.497 0 0 1 11.135 7.763zm-21.063 6.929l-3.367-1.944a.12.12 0 0 1-.065-.092v-9.299a7.497 7.497 0 0 1 12.293-5.756 6.94 6.94 0 0 0-.236.134l-7.965 4.6a1.294 1.294 0 0 0-.654 1.132l-.006 11.225zm1.829-3.943l4.33-2.501 4.332 2.5v4.999l-4.331 2.5-4.331-2.5V18z"/>
				</svg>
				<div class="text-lg font-medium font-primary">
					{$i18n.t('Connect ChatGPT Account')}
				</div>
			</div>
			<button class="self-center" on:click={closeModal} type="button">
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
					<path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"/>
				</svg>
			</button>
		</div>

		<div class="px-5 pb-5 flex flex-col gap-4 dark:text-gray-200">
			{#if step === 'ready'}
				<!-- Step 1: 로그인 시작 -->
				<p class="text-sm text-gray-500 dark:text-gray-400">
					{$i18n.t('Sign in with your ChatGPT Plus or Pro subscription to use OpenAI models without an API key.')}
				</p>

				<!-- 고정 Redirect URI 안내 -->
				<div class="flex flex-col gap-1.5">
					<label class="text-xs font-medium text-gray-600 dark:text-gray-400">
						{$i18n.t('Redirect URI')}
					</label>
					<div class="flex gap-2">
						<input
							class="flex-1 rounded-lg py-2 px-3 text-xs bg-gray-50 dark:bg-gray-850 dark:text-gray-300 outline-none border border-gray-200 dark:border-gray-700 font-mono"
							type="text"
							readonly
							value={REDIRECT_URI}
						/>
						<button
							type="button"
							class="shrink-0 px-3 py-1.5 text-xs rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition"
							on:click={copyRedirectUri}
						>
							{$i18n.t('Copy')}
						</button>
					</div>
					<p class="text-xs text-gray-400 dark:text-gray-500">
						{$i18n.t('After signing in, ChatGPT will redirect your browser to this address. Nothing will be running there — copy the full URL from your browser\'s address bar and paste it below.')}
					</p>
				</div>

				<button
					class="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-black hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 text-white dark:text-black text-sm font-medium transition"
					on:click={startLogin}
					type="button"
				>
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
						<path fill-rule="evenodd" d="M3 4.25A2.25 2.25 0 0 1 5.25 2h5.5A2.25 2.25 0 0 1 13 4.25v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 0-.75-.75h-5.5a.75.75 0 0 0-.75.75v11.5c0 .414.336.75.75.75h5.5a.75.75 0 0 0 .75-.75v-2a.75.75 0 0 1 1.5 0v2A2.25 2.25 0 0 1 10.75 18h-5.5A2.25 2.25 0 0 1 3 15.75V4.25Z" clip-rule="evenodd" />
						<path fill-rule="evenodd" d="M19 10a.75.75 0 0 0-.75-.75H8.704l1.048-.943a.75.75 0 1 0-1.004-1.114l-2.5 2.25a.75.75 0 0 0 0 1.114l2.5 2.25a.75.75 0 1 0 1.004-1.114l-1.048-.943h9.546A.75.75 0 0 0 19 10Z" clip-rule="evenodd" />
					</svg>
					{$i18n.t('Login with ChatGPT')}
				</button>

			{:else}
				<!-- Step 2: 콜백 URL 붙여넣기 -->
				<div class="flex items-start gap-2 py-2.5 px-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4 mt-0.5 shrink-0 text-blue-500">
						<path fill-rule="evenodd" d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-7-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0ZM9 9a.75.75 0 0 0 0 1.5h.253a.25.25 0 0 1 .244.304l-.459 2.066A1.75 1.75 0 0 0 10.747 15H11a.75.75 0 0 0 0-1.5h-.253a.25.25 0 0 1-.244-.304l.459-2.066A1.75 1.75 0 0 0 9.253 9H9Z" clip-rule="evenodd" />
					</svg>
					<p class="text-xs text-blue-700 dark:text-blue-300">
						{$i18n.t('A ChatGPT login page has been opened. After signing in, your browser will be redirected to')} <code class="font-mono">{REDIRECT_URI}</code>. {$i18n.t('That page will show an error — that\'s expected. Copy the full URL from your browser\'s address bar and paste it below.')}
					</p>
				</div>

				<div class="flex flex-col gap-1.5">
					<label class="text-xs font-medium text-gray-600 dark:text-gray-400">
						{$i18n.t('Paste Redirect URL')}
					</label>
					<textarea
						class="w-full rounded-lg py-2 px-3 text-xs bg-gray-50 dark:bg-gray-850 dark:text-gray-200 outline-none border border-gray-200 dark:border-gray-700 focus:border-blue-400 dark:focus:border-blue-500 transition font-mono resize-none"
						rows="3"
						placeholder="http://localhost:1455/auth/callback?code=...&state=..."
						bind:value={callbackUrl}
					></textarea>
					<p class="text-xs text-gray-400 dark:text-gray-500">
						{$i18n.t('Example: http://localhost:1455/auth/callback?code=abc123&state=xyz789')}
					</p>
				</div>

				<div class="flex gap-2">
					<button
						class="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-black hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 text-white dark:text-black text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
						on:click={submitCallback}
						disabled={loading}
						type="button"
					>
						{#if loading}
							<svg class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
						{/if}
						{$i18n.t('Complete Login')}
					</button>

					<button
						class="py-2.5 px-4 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm transition"
						on:click={() => { step = 'ready'; callbackUrl = ''; }}
						type="button"
					>
						{$i18n.t('Back')}
					</button>
				</div>
			{/if}
		</div>
	</div>
</Modal>
