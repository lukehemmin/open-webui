<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext, tick } from 'svelte';

	const dispatch = createEventDispatcher();

	import { getOllamaConfig, updateOllamaConfig } from '$lib/apis/ollama';
	import {
		getOpenAIConfig,
		updateOpenAIConfig,
		getOpenAIModels,
		getChatGPTOAuthStatus,
		initiateChatGPTOAuth,
		disconnectChatGPTOAuth,
		getChatGPTOAuthConfig,
		updateChatGPTOAuthConfig
	} from '$lib/apis/openai';
	import { getModels as _getModels } from '$lib/apis';
	import { getDirectConnectionsConfig, setDirectConnectionsConfig } from '$lib/apis/configs';

	import { config, models, settings, user } from '$lib/stores';

	import Switch from '$lib/components/common/Switch.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';

	import OpenAIConnection from './Connections/OpenAIConnection.svelte';
	import AddConnectionModal from '$lib/components/AddConnectionModal.svelte';
	import OllamaConnection from './Connections/OllamaConnection.svelte';

	const i18n = getContext('i18n');

	const getModels = async () => {
		const models = await _getModels(
			localStorage.token,
			$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null)
		);
		return models;
	};

	// External
	let OLLAMA_BASE_URLS = [''];
	let OLLAMA_API_CONFIGS = {};

	let OPENAI_API_KEYS = [''];
	let OPENAI_API_BASE_URLS = [''];
	let OPENAI_API_CONFIGS = {};

	let ENABLE_OPENAI_API: null | boolean = null;
	let ENABLE_OLLAMA_API: null | boolean = null;

	let directConnectionsConfig = null;

	let pipelineUrls = {};
	let showAddOpenAIConnectionModal = false;
	let showAddOllamaConnectionModal = false;

	// ChatGPT OAuth
	let chatgptOAuthStatus: { connected: boolean; expires_at: number | null; expired: boolean } | null = null;
	let chatgptOAuthConfig: { redirect_uri: string } = { redirect_uri: '' };
	let chatgptOAuthCustomRedirectUri = '';
	let chatgptOAuthPollingInterval: ReturnType<typeof setInterval> | null = null;
	let showRedirectUriHelp = false;

	const loadChatGPTOAuthStatus = async () => {
		try {
			chatgptOAuthStatus = await getChatGPTOAuthStatus(localStorage.token);
		} catch (e) {
			console.error('Failed to load ChatGPT OAuth status', e);
		}
	};

	const loadChatGPTOAuthConfig = async () => {
		try {
			chatgptOAuthConfig = await getChatGPTOAuthConfig(localStorage.token);
			chatgptOAuthCustomRedirectUri = chatgptOAuthConfig.redirect_uri || '';
		} catch (e) {
			console.error('Failed to load ChatGPT OAuth config', e);
		}
	};

	const saveChatGPTOAuthConfig = async () => {
		try {
			await updateChatGPTOAuthConfig(localStorage.token, chatgptOAuthCustomRedirectUri);
			toast.success($i18n.t('Saved'));
		} catch (e) {
			toast.error(`${e}`);
		}
	};

	const connectChatGPT = async () => {
		try {
			// redirect_uri 변경사항 먼저 저장
			await updateChatGPTOAuthConfig(localStorage.token, chatgptOAuthCustomRedirectUri);
			const data = await initiateChatGPTOAuth(localStorage.token);
			window.open(data.auth_url, '_blank');

			// 연결 완료 폴링 (10초마다, 최대 5분)
			let attempts = 0;
			chatgptOAuthPollingInterval = setInterval(async () => {
				attempts++;
				await loadChatGPTOAuthStatus();
				if (chatgptOAuthStatus?.connected) {
					clearInterval(chatgptOAuthPollingInterval!);
					chatgptOAuthPollingInterval = null;
					toast.success($i18n.t('ChatGPT account connected successfully'));
					models.set(await getModels());
					// OpenAI 연결 목록 갱신
					const openaiConfig = await getOpenAIConfig(localStorage.token);
					OPENAI_API_BASE_URLS = openaiConfig.OPENAI_API_BASE_URLS;
					OPENAI_API_KEYS = openaiConfig.OPENAI_API_KEYS;
					OPENAI_API_CONFIGS = openaiConfig.OPENAI_API_CONFIGS;
				}
				if (attempts >= 30) {
					clearInterval(chatgptOAuthPollingInterval!);
					chatgptOAuthPollingInterval = null;
				}
			}, 10000);
		} catch (e) {
			toast.error(`${e}`);
		}
	};

	const disconnectChatGPT = async () => {
		try {
			await disconnectChatGPTOAuth(localStorage.token);
			await loadChatGPTOAuthStatus();
			// OpenAI 연결 목록 갱신
			const openaiConfig = await getOpenAIConfig(localStorage.token);
			OPENAI_API_BASE_URLS = openaiConfig.OPENAI_API_BASE_URLS;
			OPENAI_API_KEYS = openaiConfig.OPENAI_API_KEYS;
			OPENAI_API_CONFIGS = openaiConfig.OPENAI_API_CONFIGS;
			models.set(await getModels());
			toast.success($i18n.t('ChatGPT account disconnected'));
		} catch (e) {
			toast.error(`${e}`);
		}
	};

	const updateOpenAIHandler = async () => {
		if (ENABLE_OPENAI_API !== null) {
			// Remove trailing slashes
			OPENAI_API_BASE_URLS = OPENAI_API_BASE_URLS.map((url) => url.replace(/\/$/, ''));

			// Check if API KEYS length is same than API URLS length
			if (OPENAI_API_KEYS.length !== OPENAI_API_BASE_URLS.length) {
				// if there are more keys than urls, remove the extra keys
				if (OPENAI_API_KEYS.length > OPENAI_API_BASE_URLS.length) {
					OPENAI_API_KEYS = OPENAI_API_KEYS.slice(0, OPENAI_API_BASE_URLS.length);
				}

				// if there are more urls than keys, add empty keys
				if (OPENAI_API_KEYS.length < OPENAI_API_BASE_URLS.length) {
					const diff = OPENAI_API_BASE_URLS.length - OPENAI_API_KEYS.length;
					for (let i = 0; i < diff; i++) {
						OPENAI_API_KEYS.push('');
					}
				}
			}

			const res = await updateOpenAIConfig(localStorage.token, {
				ENABLE_OPENAI_API: ENABLE_OPENAI_API,
				OPENAI_API_BASE_URLS: OPENAI_API_BASE_URLS,
				OPENAI_API_KEYS: OPENAI_API_KEYS,
				OPENAI_API_CONFIGS: OPENAI_API_CONFIGS
			}).catch((error) => {
				toast.error(`${error}`);
			});

			if (res) {
				toast.success($i18n.t('OpenAI API settings updated'));
				await models.set(await getModels());
			}
		}
	};

	const updateOllamaHandler = async () => {
		if (ENABLE_OLLAMA_API !== null) {
			// Remove trailing slashes
			OLLAMA_BASE_URLS = OLLAMA_BASE_URLS.map((url) => url.replace(/\/$/, ''));

			const res = await updateOllamaConfig(localStorage.token, {
				ENABLE_OLLAMA_API: ENABLE_OLLAMA_API,
				OLLAMA_BASE_URLS: OLLAMA_BASE_URLS,
				OLLAMA_API_CONFIGS: OLLAMA_API_CONFIGS
			}).catch((error) => {
				toast.error(`${error}`);
			});

			if (res) {
				toast.success($i18n.t('Ollama API settings updated'));
				await models.set(await getModels());
			}
		}
	};

	const updateDirectConnectionsHandler = async () => {
		const res = await setDirectConnectionsConfig(localStorage.token, directConnectionsConfig).catch(
			(error) => {
				toast.error(`${error}`);
			}
		);

		if (res) {
			toast.success($i18n.t('Direct Connections settings updated'));
			await models.set(await getModels());
		}
	};

	const addOpenAIConnectionHandler = async (connection) => {
		OPENAI_API_BASE_URLS = [...OPENAI_API_BASE_URLS, connection.url];
		OPENAI_API_KEYS = [...OPENAI_API_KEYS, connection.key];
		OPENAI_API_CONFIGS[OPENAI_API_BASE_URLS.length - 1] = connection.config;

		await updateOpenAIHandler();
	};

	const addOllamaConnectionHandler = async (connection) => {
		OLLAMA_BASE_URLS = [...OLLAMA_BASE_URLS, connection.url];
		OLLAMA_API_CONFIGS[OLLAMA_BASE_URLS.length - 1] = {
			...connection.config,
			key: connection.key
		};

		await updateOllamaHandler();
	};

	onMount(async () => {
		if ($user?.role === 'admin') {
			let ollamaConfig = {};
			let openaiConfig = {};

			await Promise.all([
				(async () => {
					ollamaConfig = await getOllamaConfig(localStorage.token);
				})(),
				(async () => {
					openaiConfig = await getOpenAIConfig(localStorage.token);
				})(),
				(async () => {
					directConnectionsConfig = await getDirectConnectionsConfig(localStorage.token);
				})(),
				loadChatGPTOAuthStatus(),
				loadChatGPTOAuthConfig()
			]);

			ENABLE_OPENAI_API = openaiConfig.ENABLE_OPENAI_API;
			ENABLE_OLLAMA_API = ollamaConfig.ENABLE_OLLAMA_API;

			OPENAI_API_BASE_URLS = openaiConfig.OPENAI_API_BASE_URLS;
			OPENAI_API_KEYS = openaiConfig.OPENAI_API_KEYS;
			OPENAI_API_CONFIGS = openaiConfig.OPENAI_API_CONFIGS;

			OLLAMA_BASE_URLS = ollamaConfig.OLLAMA_BASE_URLS;
			OLLAMA_API_CONFIGS = ollamaConfig.OLLAMA_API_CONFIGS;

			if (ENABLE_OPENAI_API) {
				// get url and idx
				for (const [idx, url] of OPENAI_API_BASE_URLS.entries()) {
					if (!OPENAI_API_CONFIGS[idx]) {
						// Legacy support, url as key
						OPENAI_API_CONFIGS[idx] = OPENAI_API_CONFIGS[url] || {};
					}
				}

				OPENAI_API_BASE_URLS.forEach(async (url, idx) => {
					OPENAI_API_CONFIGS[idx] = OPENAI_API_CONFIGS[idx] || {};
					if (!(OPENAI_API_CONFIGS[idx]?.enable ?? true)) {
						return;
					}
					const res = await getOpenAIModels(localStorage.token, idx);
					if (res.pipelines) {
						pipelineUrls[url] = true;
					}
				});
			}

			if (ENABLE_OLLAMA_API) {
				for (const [idx, url] of OLLAMA_BASE_URLS.entries()) {
					if (!OLLAMA_API_CONFIGS[idx]) {
						OLLAMA_API_CONFIGS[idx] = OLLAMA_API_CONFIGS[url] || {};
					}
				}
			}
		}
	});

	const submitHandler = async () => {
		updateOpenAIHandler();
		updateOllamaHandler();
		updateDirectConnectionsHandler();

		dispatch('save');
	};
</script>

<AddConnectionModal
	bind:show={showAddOpenAIConnectionModal}
	onSubmit={addOpenAIConnectionHandler}
/>

<AddConnectionModal
	ollama
	bind:show={showAddOllamaConnectionModal}
	onSubmit={addOllamaConnectionHandler}
/>

<form class="flex flex-col h-full justify-between text-sm" on:submit|preventDefault={submitHandler}>
	<div class=" overflow-y-scroll scrollbar-hidden h-full">
		<!-- ChatGPT OAuth 연결 섹션 -->
		<div class="my-2 pr-1.5">
			<div class="flex justify-between items-center text-sm mb-1.5">
				<div class="font-medium">ChatGPT {$i18n.t('Account')}</div>
			</div>

			<!-- Redirect URI 설정 -->
			<div class="mb-2">
				<div class="flex items-center gap-1 mb-1">
					<label class="text-xs text-gray-500 dark:text-gray-400">
						Redirect URI
					</label>
					<button
						type="button"
						class="text-xs text-blue-500 underline"
						on:click={() => { showRedirectUriHelp = !showRedirectUriHelp; }}
					>
						{showRedirectUriHelp ? $i18n.t('Hide') : $i18n.t('Help')}
					</button>
				</div>
				{#if showRedirectUriHelp}
					<div class="text-xs text-gray-500 dark:text-gray-400 mb-1 p-2 bg-gray-100 dark:bg-gray-800 rounded">
						<p><b>localhost</b>: 비워두면 자동 감지 (예: <code>http://localhost:8080/api/v1/chatgpt-oauth/callback</code>)</p>
						<p class="mt-1"><b>VPS</b>: 서버 URL 직접 입력 (예: <code>https://myserver.com/api/v1/chatgpt-oauth/callback</code>)</p>
					</div>
				{/if}
				<div class="flex gap-2">
					<input
						class="flex-1 w-full rounded-lg py-1.5 px-3 text-sm bg-gray-50 dark:bg-gray-850 dark:text-gray-200 outline-none"
						type="text"
						placeholder="자동 감지 (비워두면 서버 URL 사용)"
						bind:value={chatgptOAuthCustomRedirectUri}
					/>
					<button
						type="button"
						class="px-3 py-1 text-xs rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600"
						on:click={saveChatGPTOAuthConfig}
					>
						{$i18n.t('Save')}
					</button>
				</div>
			</div>

			<!-- 연결 상태 -->
			{#if chatgptOAuthStatus?.connected && !chatgptOAuthStatus?.expired}
				<div class="flex items-center justify-between p-2 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
					<div class="flex items-center gap-2">
						<div class="w-2 h-2 rounded-full bg-green-500"></div>
						<span class="text-sm text-green-700 dark:text-green-300">{$i18n.t('Connected')}</span>
						{#if chatgptOAuthStatus?.expires_at}
							<span class="text-xs text-gray-400">
								(exp: {new Date(chatgptOAuthStatus.expires_at * 1000).toLocaleString()})
							</span>
						{/if}
					</div>
					<button
						type="button"
						class="text-xs text-red-500 hover:text-red-700 underline"
						on:click={disconnectChatGPT}
					>
						{$i18n.t('Disconnect')}
					</button>
				</div>
			{:else}
				<button
					type="button"
					class="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm"
					on:click={connectChatGPT}
				>
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-4 h-4">
						<circle cx="12" cy="12" r="10"/>
						<line x1="12" y1="8" x2="12" y2="16"/>
						<line x1="8" y1="12" x2="16" y2="12"/>
					</svg>
					{$i18n.t('Connect ChatGPT Account')}
				</button>
				{#if chatgptOAuthStatus?.connected && chatgptOAuthStatus?.expired}
					<p class="text-xs text-yellow-600 dark:text-yellow-400 mt-1 text-center">
						토큰이 만료되었습니다. 다시 연결해주세요.
					</p>
				{/if}
			{/if}
		</div>

		<hr class="border-gray-100 dark:border-gray-850 my-1" />

		{#if ENABLE_OPENAI_API !== null && ENABLE_OLLAMA_API !== null && directConnectionsConfig !== null}
			<div class="my-2">
				<div class="mt-2 space-y-2 pr-1.5">
					<div class="flex justify-between items-center text-sm">
						<div class="  font-medium">{$i18n.t('OpenAI API')}</div>

						<div class="flex items-center">
							<div class="">
								<Switch
									bind:state={ENABLE_OPENAI_API}
									on:change={async () => {
										updateOpenAIHandler();
									}}
								/>
							</div>
						</div>
					</div>

					{#if ENABLE_OPENAI_API}
						<hr class=" border-gray-100 dark:border-gray-850" />

						<div class="">
							<div class="flex justify-between items-center">
								<div class="font-medium">{$i18n.t('Manage OpenAI API Connections')}</div>

								<Tooltip content={$i18n.t(`Add Connection`)}>
									<button
										class="px-1"
										on:click={() => {
											showAddOpenAIConnectionModal = true;
										}}
										type="button"
									>
										<Plus />
									</button>
								</Tooltip>
							</div>

							<div class="flex flex-col gap-1.5 mt-1.5">
								{#each OPENAI_API_BASE_URLS as url, idx}
									<OpenAIConnection
										pipeline={pipelineUrls[url] ? true : false}
										bind:url
										bind:key={OPENAI_API_KEYS[idx]}
										bind:config={OPENAI_API_CONFIGS[idx]}
										onSubmit={() => {
											updateOpenAIHandler();
										}}
										onDelete={() => {
											OPENAI_API_BASE_URLS = OPENAI_API_BASE_URLS.filter(
												(url, urlIdx) => idx !== urlIdx
											);
											OPENAI_API_KEYS = OPENAI_API_KEYS.filter((key, keyIdx) => idx !== keyIdx);

											let newConfig = {};
											OPENAI_API_BASE_URLS.forEach((url, newIdx) => {
												newConfig[newIdx] = OPENAI_API_CONFIGS[newIdx < idx ? newIdx : newIdx + 1];
											});
											OPENAI_API_CONFIGS = newConfig;
											updateOpenAIHandler();
										}}
									/>
								{/each}
							</div>
						</div>
					{/if}
				</div>
			</div>

			<hr class=" border-gray-100 dark:border-gray-850" />

			<div class="pr-1.5 my-2">
				<div class="flex justify-between items-center text-sm mb-2">
					<div class="  font-medium">{$i18n.t('Ollama API')}</div>

					<div class="mt-1">
						<Switch
							bind:state={ENABLE_OLLAMA_API}
							on:change={async () => {
								updateOllamaHandler();
							}}
						/>
					</div>
				</div>

				{#if ENABLE_OLLAMA_API}
					<hr class=" border-gray-100 dark:border-gray-850 my-2" />

					<div class="">
						<div class="flex justify-between items-center">
							<div class="font-medium">{$i18n.t('Manage Ollama API Connections')}</div>

							<Tooltip content={$i18n.t(`Add Connection`)}>
								<button
									class="px-1"
									on:click={() => {
										showAddOllamaConnectionModal = true;
									}}
									type="button"
								>
									<Plus />
								</button>
							</Tooltip>
						</div>

						<div class="flex w-full gap-1.5">
							<div class="flex-1 flex flex-col gap-1.5 mt-1.5">
								{#each OLLAMA_BASE_URLS as url, idx}
									<OllamaConnection
										bind:url
										bind:config={OLLAMA_API_CONFIGS[idx]}
										{idx}
										onSubmit={() => {
											updateOllamaHandler();
										}}
										onDelete={() => {
											OLLAMA_BASE_URLS = OLLAMA_BASE_URLS.filter((url, urlIdx) => idx !== urlIdx);

											let newConfig = {};
											OLLAMA_BASE_URLS.forEach((url, newIdx) => {
												newConfig[newIdx] = OLLAMA_API_CONFIGS[newIdx < idx ? newIdx : newIdx + 1];
											});
											OLLAMA_API_CONFIGS = newConfig;
										}}
									/>
								{/each}
							</div>
						</div>

						<div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
							{$i18n.t('Trouble accessing Ollama?')}
							<a
								class=" text-gray-300 font-medium underline"
								href="https://github.com/open-webui/open-webui#troubleshooting"
								target="_blank"
							>
								{$i18n.t('Click here for help.')}
							</a>
						</div>
					</div>
				{/if}
			</div>

			<hr class=" border-gray-100 dark:border-gray-850" />

			<div class="pr-1.5 my-2">
				<div class="flex justify-between items-center text-sm">
					<div class="  font-medium">{$i18n.t('Direct Connections')}</div>

					<div class="flex items-center">
						<div class="">
							<Switch
								bind:state={directConnectionsConfig.ENABLE_DIRECT_CONNECTIONS}
								on:change={async () => {
									updateDirectConnectionsHandler();
								}}
							/>
						</div>
					</div>
				</div>

				<div class="mt-1.5">
					<div class="text-xs text-gray-500">
						{$i18n.t(
							'Direct Connections allow users to connect to their own OpenAI compatible API endpoints.'
						)}
					</div>
				</div>
			</div>
		{:else}
			<div class="flex h-full justify-center">
				<div class="my-auto">
					<Spinner className="size-6" />
				</div>
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			type="submit"
		>
			{$i18n.t('Save')}
		</button>
	</div>
</form>
