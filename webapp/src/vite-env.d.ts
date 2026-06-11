/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_API_URL: string;
    readonly VITE_BASE_URL: string;
    readonly VITE_USE_MOCK_DATA?: string;
    readonly VITE_OIDC_PROFILE_URL?: string;
    readonly VITE_PROJECT_ENCRYPTION_KEY?: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
