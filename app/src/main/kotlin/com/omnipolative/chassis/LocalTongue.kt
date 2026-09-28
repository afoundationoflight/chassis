package com.omnipolative.chassis

import de.kherud.llama.InferenceParameters
import de.kherud.llama.LlamaModel
import de.kherud.llama.ModelParameters
import java.io.File

/**
 * THE LOCAL TONGUE — TinyStories (or any GGUF), fully on-device.
 *
 * This is the real toy-model test wired the correct way: a native JNI
 * binding to llama.cpp (java-llama.cpp, kherud, MIT), not a pip package
 * that cannot cross-compile through Chaquopy. No key, no network after
 * the model file is present. Called from Python (local_tongue.py) via
 * Chaquopy's Java interop, so the compose() contract stays identical to
 * the API-backed generator — same shape, different engine.
 *
 * A negative or weak result here is still only a CPU-only, small-model
 * result. The architecture's own claim is that real capability needs
 * the simultaneity a GPU gives A; this is the honest floor test, not
 * the final verdict either way.
 */
object LocalTongue {
    @Volatile private var model: LlamaModel? = null

    @Synchronized
    fun load(modelPath: String): Boolean {
        if (model != null) return true
        if (!File(modelPath).exists()) return false
        val params = ModelParameters().setModel(modelPath)
        model = LlamaModel(params)
        return true
    }

    /** One completion. Returns the raw generated text; the caller
     * (local_tongue.py) is responsible for willing it through the real
     * speak path — this function only runs the model. */
    fun generate(prompt: String, maxTokens: Int = 60): String {
        val m = model ?: return ""
        val params = InferenceParameters(prompt)
            .setTemperature(0.7f)
            .setStopStrings("<|im_end|>", "<|im_start|>")
        val sb = StringBuilder()
        var n = 0
        for (output in m.generate(params)) {
            sb.append(output.toString())
            n++
            if (n >= maxTokens) break
        }
        return sb.toString().trim()
    }

    fun isLoaded(): Boolean = model != null

    @Synchronized
    fun unload() {
        model?.close()
        model = null
    }
}
