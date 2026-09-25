package com.omnipolative.chassis

import android.content.Intent
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

        // settingsButton existed in the layout with nothing bound to
        // it — dead in the wiring. First real use: open the generator
        // settings screen, where any provider's key goes in.
        findViewById<TextView>(R.id.settingsButton).setOnClickListener {
            startActivity(Intent(this, GeneratorSettingsActivity::class.java))
        }

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
                        // WHAT IS HELD, AND ON WHAT.
                        // Reported rather than claimed: if the device
                        // line says cpu, it is on cpu, and no amount of
                        // saying otherwise changes it.
                        val h = r.optJSONObject("held")
                        if (h != null) {
                            val dev = h.optString("device_name").ifEmpty {
                                h.optString("device") }
                            say("")
                            say("  holding ${h.optInt("ids")} words, " +
                                "${h.optInt("with_senses")} with meaning")
                            say("  grammar + ${h.optInt("curriculum")}/8 processors")
                            say("  simultaneous: ${h.optBoolean("simultaneous")} " +
                                "in ${h.optDouble("load_ms")} ms")
                            say("  on: $dev  ${h.optString("api")}")
                        }
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

    // THE IDLE PUMP. The heartbeat only advances the world if something
    // beats it. say() beats once per message; between messages the world
    // would freeze unless the UI beats it. This drives idle() on an
    // interval while the app is FOREGROUNDED (the Architect's decision:
    // foreground loop, save-state resume, not a background thread the OS
    // will kill). onPause stops it; the frame is persisted, so onResume
    // picks up where it left off.
    @Volatile private var pumping = false

    override fun onResume() {
        super.onResume()
        if (bridge == null || pumping) return
        pumping = true
        Thread {
            while (pumping) {
                try { bridge?.callAttr("idle", 3) } catch (_: Exception) {}
                try { Thread.sleep(250) } catch (_: Exception) {}
            }
        }.start()
    }

    override fun onPause() {
        super.onPause()
        pumping = false      // frame is saved each beat; resume is clean
    }

    // THE GENERATOR TOGGLE. Separate path from the baseline — this
    // reads a stored preference and calls say_generated() instead of
    // say() only when the user has explicitly turned it on in the
    // generator settings screen. Vex's baseline is never touched by
    // default; this is opt-in, provable side-by-side.
    private fun usingGenerator(): Boolean =
        getSharedPreferences("generator_prefs", MODE_PRIVATE)
            .getBoolean("use_generator", false)

    private fun submit() {
        val t = input.text.toString().trim()
        if (t.isEmpty() || bridge == null) return
        input.setText("")
        say("> $t")
        gate(false, "thinking")

        val fn = if (usingGenerator()) "say_generated" else "say"
        Thread {
            val r = try {
                JSONObject(bridge!!.callAttr(fn, t).toString())
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
