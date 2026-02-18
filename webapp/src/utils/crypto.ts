"use server";

import crypto from "crypto";

// Environment variable to use as encryption key (should be 32 bytes for AES-256)
const SECRET_KEY = process.env.PROJECT_ENCRYPTION_KEY as string;

/**
 * Encrypts a project ID to create a short, consistent secure sharing link
 * @param projectId The original project ID to encrypt
 * @returns A short encrypted string safe to use in URLs
 */
export async function encryptProjectId(projectId: string): Promise<string> {
    // Create a deterministic IV by hashing the project ID with our secret key
    // This ensures the same project ID always generates the same encrypted output
    // while still being secure due to the secret key
    const hmac = crypto.createHmac("sha256", SECRET_KEY);
    hmac.update(projectId);
    // Use first 16 bytes of the HMAC output as our IV
    const iv = Buffer.from(hmac.digest().subarray(0, 16));

    // Create a cipher using AES-256-CBC with our deterministic IV
    const cipher = crypto.createCipheriv(
        "aes-256-cbc",
        Buffer.from(SECRET_KEY.substring(0, 32).padEnd(32, "0")),
        iv,
    );

    // Encrypt the project ID
    let encrypted = cipher.update(projectId, "utf8", "base64");
    encrypted += cipher.final("base64");

    // Combine IV and encrypted data and convert to URL-safe base64
    const combined = Buffer.concat([iv, Buffer.from(encrypted, "base64")]);
    return combined.toString("base64url");
}

/**
 * Decrypts an encrypted project ID from a sharing link
 * @param encryptedData The encrypted project ID from the URL
 * @returns The original project ID
 */
export async function decryptProjectId(encryptedData: string): Promise<string> {
    try {
        // Convert from base64url to buffer
        const encryptedBuffer = Buffer.from(encryptedData, "base64url");

        // Extract IV (first 16 bytes) and actual encrypted data
        const iv = encryptedBuffer.subarray(0, 16);
        const encryptedText = encryptedBuffer.subarray(16).toString("base64");

        // Create decipher
        const decipher = crypto.createDecipheriv(
            "aes-256-cbc",
            Buffer.from(SECRET_KEY.substring(0, 32).padEnd(32, "0")),
            iv,
        );

        // Decrypt the data
        let decrypted = decipher.update(encryptedText, "base64", "utf8");
        decrypted += decipher.final("utf8");

        return decrypted;
    } catch (error) {
        console.error("Failed to decrypt project ID:", error);
        throw new Error("Invalid or corrupted project link");
    }
}
