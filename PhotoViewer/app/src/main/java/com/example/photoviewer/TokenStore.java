package com.example.photoviewer;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Stores the login token encrypted with an AES key held in Android Keystore. */
final class TokenStore {
    private static final String KEYSTORE = "AndroidKeyStore";
    private static final String KEY_ALIAS = "photo_viewer_token_key";
    private static final String TRANSFORMATION = "AES/GCM/NoPadding";
    private static final String ENCRYPTED_TOKEN = "token_encrypted";
    private static final String LEGACY_TOKEN = "token";
    private static final int TAG_BITS = 128;
    private final SharedPreferences preferences;

    TokenStore(Context context) {
        preferences = context.getSharedPreferences("photo_viewer", Context.MODE_PRIVATE);
    }

    String load() {
        String legacy = preferences.getString(LEGACY_TOKEN, null);
        if (legacy != null) {
            save(legacy);
            return legacy;
        }
        String stored = preferences.getString(ENCRYPTED_TOKEN, null);
        if (stored == null) return null;
        try {
            ByteBuffer data = ByteBuffer.wrap(Base64.decode(stored, Base64.NO_WRAP));
            byte[] iv = new byte[data.get()];
            data.get(iv);
            byte[] encrypted = new byte[data.remaining()];
            data.get(encrypted);
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(TAG_BITS, iv));
            return new String(cipher.doFinal(encrypted), StandardCharsets.UTF_8);
        } catch (Exception e) {
            preferences.edit().remove(ENCRYPTED_TOKEN).apply();
            return null;
        }
    }

    /** Saves the token and removes any plaintext copy; on failure the token is kept in memory only. */
    void save(String token) {
        SharedPreferences.Editor editor = preferences.edit().remove(LEGACY_TOKEN);
        try {
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.ENCRYPT_MODE, key());
            byte[] iv = cipher.getIV();
            byte[] encrypted = cipher.doFinal(token.getBytes(StandardCharsets.UTF_8));
            ByteBuffer data = ByteBuffer.allocate(1 + iv.length + encrypted.length);
            data.put((byte) iv.length).put(iv).put(encrypted);
            editor.putString(ENCRYPTED_TOKEN, Base64.encodeToString(data.array(), Base64.NO_WRAP));
        } catch (Exception e) {
            editor.remove(ENCRYPTED_TOKEN);
        }
        editor.apply();
    }

    void clear() {
        preferences.edit().remove(ENCRYPTED_TOKEN).remove(LEGACY_TOKEN).apply();
    }

    private SecretKey key() throws Exception {
        KeyStore keyStore = KeyStore.getInstance(KEYSTORE);
        keyStore.load(null);
        if (keyStore.containsAlias(KEY_ALIAS)) return (SecretKey) keyStore.getKey(KEY_ALIAS, null);
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, KEYSTORE);
        generator.init(new KeyGenParameterSpec.Builder(
                KEY_ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .build());
        return generator.generateKey();
    }
}
