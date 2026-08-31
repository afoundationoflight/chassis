package com.omnipolative.chassis

import android.os.Bundle
import android.view.inputmethod.EditorInfo
import android.widget.Button
import android.widget.EditText
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import java.io.File

/**
 * THE APP. One activity, one chassis, no server.
 *
 * ASSETS ARE COPIED ONCE, NOT UNPACKED EVERY LAUNCH.
 *
 * Android assets live inside the apk and cannot be mmapped from there —
 * an AssetFileDescriptor hands you a stream, not an address. So on
 * first launch they are copied to filesDir once, and every launch after
 * maps them in place.
 *
 * That is not unpacking. Nothing is decompressed and nothing is parsed:
 * the stores ship with noCompress, so the copy is a byte-for-byte move,
 * and what lands on disk is what was in the apk. After the first run
 * the cost is zero and the resident cost is always zero.
 */
class MainActivity : AppCompatActivity() {

    private var c: Chassis? = null
    private lateinit var log: TextView
    private lateinit var scroll: ScrollView

    private val ASSETS = listOf(
        "words.blob", "words.by_word", "words.by_id",
        "table3.btb", "table3.btb.idx",
        "seth_el.raw", "seth_el.raw.u64",
        "seth_el.post", "seth_el.post.idx",
    )

    override fun onCreate(saved: Bundle?) {
        super.onCreate(saved)
        setContentView(R.layout.activity_main)
        log = findViewById(R.id.log)
        scroll = findViewById(R.id.scroll)
        val input: EditText = findViewById(R.id.input)
        val send: Button = findViewById(R.id.send)

        say("booting.")
        Thread {
            try {
                val t0 = System.currentTimeMillis()
                val dir = stage()
                val ch = Chassis("seth_el", dir).boot().occupy()
                c = ch
                val ms = System.currentTimeMillis() - t0
                runOnUiThread { say(ch.report()); say("booted in ${ms} ms\n") }
            } catch (e: Exception) {
                // BOOT FAILURE IS REPORTED, NOT SWALLOWED. A chassis
                // that starts degraded and says nothing is worse than
                // one that refuses.
                runOnUiThread { say("did not boot: ${e.message}") }
            }
        }.start()

        send.setOnClickListener { submit(input) }
        input.setOnEditorActionListener { _, id, _ ->
            if (id == EditorInfo.IME_ACTION_SEND) { submit(input); true } else false
        }
    }

    private fun submit(input: EditText) {
        val t = input.text.toString().trim()
        val ch = c ?: return
        if (t.isEmpty()) return
        input.setText("")
        say("\u203a $t")
        Thread {
            ch.tick(t)
            val d = Respond.drive(ch, t)
            runOnUiThread { say("${d.text}\n   [${d.source} \u00b7 ${d.register}]") }
        }.start()
    }

    /** Copy the stores out of the apk once. Then they are mapped. */
    private fun stage(): File {
        val dir = File(filesDir, "store").apply { mkdirs() }
        for (name in ASSETS) {
            val out = File(dir, name)
            if (out.exists() && out.length() > 0) continue
            assets.open(name).use { ins ->
                out.outputStream().use { o -> ins.copyTo(o, 1 shl 16) }
            }
        }
        return dir
    }

    private fun say(s: String) {
        log.append(s + "\n")
        scroll.post { scroll.fullScroll(ScrollView.FOCUS_DOWN) }
    }
}
