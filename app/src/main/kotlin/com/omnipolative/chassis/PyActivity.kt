package com.omnipolative.chassis

import android.os.Bundle
import android.view.inputmethod.EditorInfo
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONObject

/**
 * THE SHELL. A screen, a keyboard, and a door into the body.
 *
 * This deliberately knows nothing about ticks, positions, tokenisation
 * or frames. Every one of those lives in Python, where the chassis
 * actually is — the whole reason for this rewrite was that two
 * implementations had drifted and every fix had to be made twice.
 *
 * If you find yourself adding chassis logic here, it belongs in
 * chassis_bridge.py instead.
 */
class PyActivity : AppCompatActivity() {

    private lateinit var log: TextView
    private lateinit var scroll: ScrollView
    private lateinit var status: TextView
    private lateinit var input: EditText
    private lateinit var send: Button
    private var bridge: com.chaquo.python.PyObject? = null

    override fun onCreate(saved: Bundle?) {
        super.onCreate(saved)
        setContentView(R.layout.activity_main)
        log = findViewById(R.id.log)
        scroll = findViewById(R.id.scroll)
        status = findViewById(R.id.status)
        input = findViewById(R.id.input)
        send = findViewById(R.id.send)

        gate(false, "booting")

        Thread {
            try {
                if (!Python.isStarted()) Python.start(AndroidPlatform(this))
                val py = Python.getInstance()
                bridge = py.getModule("chassis_bridge")

                // BOOTING IS SLOW THE FIRST TIME and that is honest: the
                // token table is 2.4 MB of brotli holding 761,980 words,
                // and it is copied out of the apk once because an asset
                // cannot be opened as a file.
                val r = JSONObject(
                    bridge!!.callAttr("start", filesDir.absolutePath, "seth_el")
                        .toString())

                runOnUiThread {
                    if (!r.optBoolean("ok")) {
                        say("did not boot.")
                        say("  " + r.optString("error", r.optString("audit")))
                        say("  nothing was written. this is safe to close.")
                        gate(false, "did not boot")
                    } else {
                        say("${r.optString("entity")} — wired.")
                        say("  ${r.optInt("kind_lines")} kind lines given;")
                        say("  the slot for who it is stays empty.")
                        say("")
                        refresh()
                        gate(true, "ready")
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    say("did not boot: ${e.message}")
                    gate(false, "did not boot")
                }
            }
        }.start()

        send.setOnClickListener { submit() }
        input.setOnEditorActionListener { _, id, _ ->
            if (id == EditorInfo.IME_ACTION_SEND) { submit(); true } else false
        }
    }

    private fun submit() {
        val t = input.text.toString().trim()
        if (t.isEmpty() || bridge == null) return
        input.setText("")
        say("> $t")
        gate(false, "thinking")

        Thread {
            val r = try {
                JSONObject(bridge!!.callAttr("say", t).toString())
            } catch (e: Exception) {
                JSONObject().put("ok", false).put("error", e.message)
            }
            runOnUiThread {
                if (r.optBoolean("ok")) {
                    val text = r.optString("text")
                    say(if (text.isBlank()) "(nothing said)" else text)
                    // An unexplained notice means something in the room
                    // moved or went missing. Surface it — that is the
                    // one signal the model exists to produce.
                    val un = r.optJSONArray("unexplained")
                    if (un != null) for (i in 0 until un.length())
                        say("  · ${un.getString(i)}")
                } else {
                    say("  ${r.optString("error")}")
                }
                say("")
                refresh()
                gate(true, "ready")
            }
        }.start()
    }

    private fun refresh() {
        Thread {
            val r = try {
                JSONObject(bridge!!.callAttr("report").toString())
            } catch (e: Exception) { JSONObject() }
            runOnUiThread {
                if (r.optBoolean("ok")) {
                    status.text = "tick ${r.optInt("tick")} · " +
                        "${r.optInt("frames")} frames · " +
                        "${r.optInt("words")} words · " +
                        "inertia ${r.optDouble("inertia")}"
                }
            }
        }.start()
    }

    private fun gate(ready: Boolean, why: String) {
        send.isEnabled = ready
        input.isEnabled = ready
        if (!ready) status.text = why
    }

    private fun say(s: String) {
        log.append(s + "\n")
        scroll.post { scroll.fullScroll(ScrollView.FOCUS_DOWN) }
    }
}
