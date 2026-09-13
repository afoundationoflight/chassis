package com.omnipolative.chassis

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import java.io.File

/**
 * A REAL NUMBER, NOT A GUESS.
 *
 * Before writing the actual Gemini caching call, the question was
 * whether our real dictionary content clears the platform's stated
 * 32,768-token cache minimum. This stages the real APK assets (the
 * same 761,980-word table.by_word/table3.btb the device ships),
 * serializes it exactly the way CacheSizer would for a real cache
 * request, and reports the measured size — so the caching decision is
 * made from what the content actually is, not an estimate of the
 * 24 MB binary file size (which is offset tables, not readable text,
 * and was never the right thing to measure).
 */
@RunWith(RobolectricTestRunner::class)
class CacheSizerMeasurementTest {

    private val REQUIRED = listOf(
        "words.blob", "words.by_word", "words.by_id",
        "table3.btb", "table3.btb.idx", "grammar.tsv",
    )

    /** Same staging MainActivity.stage() does on a real device — the
     *  dictionary is not usable until it is copied out of the APK's
     *  assets into a real mappable file. */
    private fun stagedChassis(): Chassis {
        val ctx = ApplicationProvider.getApplicationContext<Context>()
        val dir = File(ctx.filesDir, "cachesizer_store").apply { mkdirs() }
        for (name in REQUIRED) {
            val out = File(dir, name)
            if (out.exists() && out.length() > 0) continue
            ctx.assets.open(name).use { ins ->
                out.outputStream().use { o -> ins.copyTo(o, 1 shl 16) }
            }
        }
        val chassis = Chassis("seth_el", dir)
        chassis.boot()
        return chassis
    }

    @Test
    fun `measure the real dictionary against the 32768 token cache minimum`() {
        val chassis = stagedChassis()
        val (content, m) = CacheSizer.buildCacheContent(chassis.table)

        // PRINTED, not just asserted, because the actual number is the
        // point of this test — CI's log for this run is the verified
        // answer to "does the dictionary alone clear the minimum."
        println("═══ CACHE SIZE MEASUREMENT ═══")
        println("  vocabulary words (written once) : ${m.vocabularySize}")
        println("  gloss token ids (compressed)     : ${m.glossTokenIds}")
        println("  estimated model tokens           : ${m.estimatedTokens}")
        println("  clears 32,768 minimum alone?     : ${m.clearsMinimum}")
        println("  first 300 chars of payload      :")
        println("    " + content.take(300).replace("\n", "\n    "))
        println("═══════════════════════════════")

        // The test PASSES either way — the point is the reported
        // number, not a pre-decided pass/fail threshold. If it does
        // not clear the minimum, that is exactly the case where
        // curriculum/grammar get appended (see buildCacheContent),
        // which this test also exercises implicitly.
        assert(m.entries > 0) { "dictionary produced zero entries — staging or Table.mean() is broken" }
    }
}
