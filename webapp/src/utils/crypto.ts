// Legacy client-side decryption for existing public project sharing links.
//
// Port of the original Node `crypto` implementation (see git history on
// master, pre-React-migration) to the browser's Web Crypto API. The
// algorithm is:
//
//   1. Derive a deterministic 16-byte IV per project id:
//        IV = HMAC-SHA256(secret, projectId).slice(0, 16)
//      This guarantees the same project id always encrypts to the same
//      string — useful for caching and clean URLs.
//   2. Pad the secret to exactly 32 ASCII bytes:
//        aesKey = utf8(secret.substring(0, 32).padEnd(32, "0"))
//   3. AES-256-CBC encrypt the projectId.
//   4. Output: base64url(IV ‖ ciphertext)
//
// `VITE_PROJECT_ENCRYPTION_KEY` is exposed to the browser via the bundle.
// This was obfuscation rather than an authorization boundary because the key
// is present in the browser bundle. New links use the public project UUID
// directly; this decoder remains only for backward compatibility.

const TEXT_ENCODER = new TextEncoder();
const TEXT_DECODER = new TextDecoder();

function getSecret(): string {
    const secret = import.meta.env.VITE_PROJECT_ENCRYPTION_KEY;
    if (!secret || typeof secret !== "string") {
        throw new Error(
            "VITE_PROJECT_ENCRYPTION_KEY is not set. " +
                "Add it to webapp/.env (see .env.example) to enable share links.",
        );
    }
    return secret;
}

function getSubtle(): SubtleCrypto {
    const subtle =
        typeof globalThis.crypto !== "undefined"
            ? globalThis.crypto.subtle
            : undefined;
    if (!subtle) {
        throw new Error(
            "Web Crypto (crypto.subtle) is unavailable in this environment.",
        );
    }
    return subtle;
}

// Returns a freshly-allocated Uint8Array backed by a non-shared
// ArrayBuffer. Required by `SubtleCrypto.encrypt`'s `iv` field under
// TS 5.7+ where ArrayBufferView is generic over its buffer type.
function copyBytes(view: Uint8Array): Uint8Array<ArrayBuffer> {
    const buffer = new ArrayBuffer(view.byteLength);
    const out = new Uint8Array(buffer);
    out.set(view);
    return out;
}

async function deriveAesKey(secret: string): Promise<CryptoKey> {
    const subtle = getSubtle();
    const padded = secret.substring(0, 32).padEnd(32, "0");
    const rawKey = TEXT_ENCODER.encode(padded).slice(0, 32);
    return subtle.importKey("raw", rawKey, { name: "AES-CBC" }, false, [
        "decrypt",
    ]);
}

function fromBase64Url(value: string): Uint8Array {
    const padded = value
        .replace(/-/g, "+")
        .replace(/_/g, "/")
        .padEnd(value.length + ((4 - (value.length % 4)) % 4), "=");
    const bin = atob(padded);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
}

/**
 * Decrypt a legacy sharing token back into the original project id.
 * Throws if the token is malformed or the secret is wrong.
 */
export async function decryptProjectId(encrypted: string): Promise<string> {
    const secret = getSecret();
    const subtle = getSubtle();

    const combined = fromBase64Url(encrypted);
    if (combined.byteLength <= 16) {
        throw new Error("Invalid sharing token");
    }
    const iv = copyBytes(combined.subarray(0, 16));
    const ciphertext = copyBytes(combined.subarray(16));

    const key = await deriveAesKey(secret);
    const plaintext = await subtle.decrypt(
        { name: "AES-CBC", iv },
        key,
        ciphertext,
    );
    return TEXT_DECODER.decode(plaintext);
}
