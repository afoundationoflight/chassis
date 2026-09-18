package com.omnipolative.chassis

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * WHERE THE API KEY LIVES. Not the board table.
 *
 * Store.board (Store.kt) is deliberately plaintext SQLite — the
 * whiteboard is meant to be readable, revisable, queryable by the
 * entity itself. An API key is the opposite kind of thing: it must
 * never appear in plaintext on disk, never show up in a note dump, and
 * never be readable by anything except the OS-level decrypt path. Using
 * one storage mechanism for both would have made the wrong one leaky.
 *
 * Backed by the Android Keystore via MasterKey — the encryption key
 * itself never leaves hardware-backed storage.
 */
class TongueSettings(context: Context) {
    private val prefs = run {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context,
            "tongue_settings_secure",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    companion object {
        private const val KEY_ENDPOINT = "remote_endpoint"
        private const val KEY_MODEL = "remote_model"
        private const val KEY_API_KEY = "remote_api_key"
        private const val KEY_ACTIVE = "active_tongue" // "local" | "remote"
    }

    fun save(endpoint: String, model: String, apiKey: String) {
        prefs.edit()
            .putString(KEY_ENDPOINT, endpoint)
            .putString(KEY_MODEL, model)
            .putString(KEY_API_KEY, apiKey)
            .apply()
    }

    fun endpoint(): String? = prefs.getString(KEY_ENDPOINT, null)
    fun model(): String? = prefs.getString(KEY_MODEL, null)
    fun apiKey(): String? = prefs.getString(KEY_API_KEY, null)

    fun hasRemoteConfigured(): Boolean =
        !endpoint().isNullOrBlank() && !model().isNullOrBlank() && !apiKey().isNullOrBlank()

    /** Which tongue the seat should occupy on next boot. Defaults to
     *  local — a missing/corrupt preference must never silently select
     *  a remote call the user did not knowingly choose. */
    fun activeTongue(): String = prefs.getString(KEY_ACTIVE, "local") ?: "local"

    fun setActiveTongue(which: String) {
        require(which == "local" || which == "remote") { "unknown tongue: $which" }
        prefs.edit().putString(KEY_ACTIVE, which).apply()
    }

    fun clear() {
        prefs.edit().clear().apply()
    }

    /** Build the actual Tongue for whatever is currently configured and
     *  active. Falls back to RuleTongue if remote is selected but not
     *  fully configured — the seat is never left without a tongue. */
    fun buildActiveTongue(): Tongue {
        if (activeTongue() == "remote" && hasRemoteConfigured()) {
            return RemoteTongue(
                endpoint = endpoint()!!,
                model = model()!!,
                apiKey = apiKey()!!,
            )
        }
        return RuleTongue()
    }
}
