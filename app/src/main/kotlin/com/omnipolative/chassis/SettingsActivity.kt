package com.omnipolative.chassis

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.RadioButton
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * WHERE THE KEY IS ENTERED. The one place in the app that touches
 * TongueSettings directly — MainActivity only ever reads
 * buildActiveTongue() at boot, never the raw key.
 */
class SettingsActivity : AppCompatActivity() {

    private lateinit var settings: TongueSettings

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)
        settings = TongueSettings(applicationContext)

        val chooseLocal: RadioButton = findViewById(R.id.chooseLocal)
        val chooseRemote: RadioButton = findViewById(R.id.chooseRemote)
        val endpointInput: EditText = findViewById(R.id.endpointInput)
        val modelInput: EditText = findViewById(R.id.modelInput)
        val apiKeyInput: EditText = findViewById(R.id.apiKeyInput)
        val saveButton: Button = findViewById(R.id.saveButton)
        val statusText: TextView = findViewById(R.id.statusText)

        // PREFILL FROM WHAT IS ALREADY SAVED, except the key itself —
        // showing a previously-saved key back in the clear on screen
        // open defeats the point of storing it encrypted in the first
        // place. Endpoint/model are not secrets; the key is.
        endpointInput.setText(settings.endpoint() ?: "")
        modelInput.setText(settings.model() ?: "")
        if (settings.activeTongue() == "remote") chooseRemote.isChecked = true
        else chooseLocal.isChecked = true

        statusText.text = if (settings.hasRemoteConfigured())
            "remote configured · active: ${settings.activeTongue()}"
        else "no remote configured yet · active: local"

        saveButton.setOnClickListener {
            val endpoint = endpointInput.text.toString().trim()
            val model = modelInput.text.toString().trim()
            val key = apiKeyInput.text.toString().trim()

            if (chooseRemote.isChecked) {
                if (endpoint.isEmpty() || model.isEmpty() || key.isEmpty()) {
                    statusText.text = "remote needs endpoint, model, and a key — not saved"
                    return@setOnClickListener
                }
                settings.save(endpoint, model, key)
                settings.setActiveTongue("remote")
                statusText.text = "saved. remote active: $model"
            } else {
                // ENDPOINT/MODEL ARE KEPT even when switching to local,
                // so re-checking "remote" later does not lose them —
                // only the ACTIVE choice changes. The key field is left
                // exactly as stored; leaving it blank here never erases
                // a saved key, since save() is only called in the
                // remote branch above.
                settings.setActiveTongue("local")
                statusText.text = "local active"
            }
            apiKeyInput.setText("")   // never linger in the visible field
        }
    }
}
