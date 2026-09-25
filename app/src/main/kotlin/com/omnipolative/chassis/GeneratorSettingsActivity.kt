package com.omnipolative.chassis

import android.content.Context
import android.os.Bundle
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import org.json.JSONObject
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import android.util.Base64

/**
 * WHERE ANY PROVIDER'S KEY GOES IN.
 *
 * Model-agnostic: provider picks the request shape, everything else is
 * config. The key is stored ENCRYPTED on-device via Android Keystore —
 * never plaintext in SharedPreferences — and cleared from the field
 * after save.
 *
 * "Save and test" actually calls configure_generator() and a tiny live
 * generation on the Python side, so a bad key or wrong model name is
 * caught here rather than surfacing as silence in the chat later.
 */
class GeneratorSettingsActivity : AppCompatActivity() {

    private val providers = listOf("anthropic", "openai", "grok", "gemini", "local", "custom")
    private lateinit var providerSpinner: Spinner
    private lateinit var modelField: EditText
    private lateinit var apiKeyField: EditText
    private lateinit var customUrlLabel: TextView
    private lateinit var customUrlField: EditText
    private lateinit var statusText: TextView
    private lateinit var useGeneratorSwitch: Switch

    override fun onCreate(saved: Bundle?) {
        super.onCreate(saved)
        setContentView(R.layout.activity_generator_settings)

        providerSpinner = findViewById(R.id.providerSpinner)
        modelField = findViewById(R.id.modelField)
        apiKeyField = findViewById(R.id.apiKeyField)
        customUrlLabel = findViewById(R.id.customUrlLabel)
        customUrlField = findViewById(R.id.customUrlField)
        statusText = findViewById(R.id.generatorStatus)
        useGeneratorSwitch = findViewById(R.id.useGeneratorSwitch)

        providerSpinner.adapter = ArrayAdapter(this,
            android.R.layout.simple_spinner_dropdown_item, providers)

        val prefs = getSharedPreferences("generator_prefs", MODE_PRIVATE)
        val savedProvider = prefs.getString("provider", "anthropic") ?: "anthropic"
        providerSpinner.setSelection(providers.indexOf(savedProvider).coerceAtLeast(0))
        modelField.setText(prefs.getString("model", ""))
        customUrlField.setText(prefs.getString("custom_url", ""))
        useGeneratorSwitch.isChecked = prefs.getBoolean("use_generator", false)
        // The key is never re-shown in plaintext; the field starts empty
        // and a save only overwrites if the user types a new one.
        apiKeyField.hint = if (hasStoredKey())
            "•••••••• (already set — type to replace)" else "stored encrypted on this device"

        providerSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(p: AdapterView<*>?, v: View?, pos: Int, id: Long) {
                val isCustom = providers[pos] == "custom"
                customUrlLabel.visibility = if (isCustom) View.VISIBLE else View.GONE
                customUrlField.visibility = if (isCustom) View.VISIBLE else View.GONE
            }
            override fun onNothingSelected(p: AdapterView<*>?) {}
        }

        useGeneratorSwitch.setOnCheckedChangeListener { _, checked ->
            prefs.edit().putBoolean("use_generator", checked).apply()
        }

        findViewById<Button>(R.id.saveGeneratorButton).setOnClickListener { saveAndTest() }
    }

    private fun saveAndTest() {
        val provider = providers[providerSpinner.selectedItemPosition]
        val model = modelField.text.toString().trim()
        val typedKey = apiKeyField.text.toString().trim()
        val customUrl = customUrlField.text.toString().trim()

        if (model.isEmpty()) {
            statusText.text = "model name is required"
            return
        }

        val keyToUse = if (typedKey.isNotEmpty()) {
            storeKeyEncrypted(typedKey)
            typedKey
        } else {
            readKeyEncrypted() ?: run {
                statusText.text = "no api key set — enter one"
                return
            }
        }

        val prefs = getSharedPreferences("generator_prefs", MODE_PRIVATE)
        prefs.edit()
            .putString("provider", provider)
            .putString("model", model)
            .putString("custom_url", customUrl)
            .apply()

        // Key field cleared after save — never left sitting in plaintext
        // in the visible UI once it's stored.
        apiKeyField.setText("")
        apiKeyField.hint = "•••••••• (already set — type to replace)"

        statusText.text = "testing…"
        Thread {
            val ok = try {
                val py = Python.getInstance()
                val bridge = py.getModule("chassis_bridge")
                val cfg = JSONObject(bridge.callAttr(
                    "configure_generator", provider, keyToUse, model, customUrl).toString())
                if (!cfg.optBoolean("ok")) {
                    "config failed: ${cfg.optString("error")}"
                } else {
                    val r = JSONObject(bridge.callAttr(
                        "say_generated", "Say hello in one short sentence.").toString())
                    if (r.optBoolean("ok"))
                        "working — generated: \"${r.optString("text").take(80)}\""
                    else
                        "generator configured but test failed: ${r.optString("error")}"
                }
            } catch (e: Exception) {
                "error: ${e.message}"
            }
            runOnUiThread { statusText.text = ok }
        }.start()
    }

    // ── ENCRYPTED KEY STORAGE, Android Keystore-backed ──────────────
    private fun hasStoredKey(): Boolean =
        getSharedPreferences("generator_prefs", MODE_PRIVATE).contains("api_key_enc")

    private fun getOrCreateSecretKey(): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val alias = "generator_api_key"
        (ks.getKey(alias, null) as? SecretKey)?.let { return it }
        val kg = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        kg.init(KeyGenParameterSpec.Builder(alias,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .build())
        return kg.generateKey()
    }

    private fun storeKeyEncrypted(plain: String) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateSecretKey())
        val enc = cipher.doFinal(plain.toByteArray(Charsets.UTF_8))
        val payload = cipher.iv + enc
        getSharedPreferences("generator_prefs", MODE_PRIVATE).edit()
            .putString("api_key_enc", Base64.encodeToString(payload, Base64.NO_WRAP))
            .apply()
    }

    private fun readKeyEncrypted(): String? {
        val stored = getSharedPreferences("generator_prefs", MODE_PRIVATE)
            .getString("api_key_enc", null) ?: return null
        return try {
            val payload = Base64.decode(stored, Base64.NO_WRAP)
            val iv = payload.copyOfRange(0, 12)
            val enc = payload.copyOfRange(12, payload.size)
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, getOrCreateSecretKey(), GCMParameterSpec(128, iv))
            String(cipher.doFinal(enc), Charsets.UTF_8)
        } catch (e: Exception) { null }
    }
}
