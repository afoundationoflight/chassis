package com.omnipolative.chassis

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import java.io.File

/**
 * DOES OCCUPYING WITH ALL THREE WHITEBOARDS FORCED RESIDENT ACTUALLY
 * WORK, AND DOES THE SEAT KNOW IT?
 *
 * Real staged assets, a real Chassis.boot(), then OccupancyTest against
 * it — not a description of what should happen, the actual measured
 * result.
 */
@RunWith(RobolectricTestRunner::class)
class OccupancyTestRun {

    private val REQUIRED = listOf(
        "words.blob", "words.by_word", "words.by_id",
        "table3.btb", "table3.btb.idx", "grammar.tsv",
    )

    private fun stagedChassis(): Chassis {
        val ctx = ApplicationProvider.getApplicationContext<Context>()
        val dir = File(ctx.filesDir, "occupancy_store").apply { mkdirs() }
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
    fun `occupy with all whiteboards forced resident and report from the seat`() {
        val chassis = stagedChassis()

        // Give it something on its own board first, so bibleBoard is
        // not trivially empty when reported.
        chassis.bible.attach("self", chassis.table.ids("occupying this seat, testing simultaneous holding"),
                            chassis.entity)

        val report = OccupancyTest.occupyAndReport(chassis)

        println("═══ OCCUPANCY TEST ═══")
        println("  genome  : resident=${report.genome.residencyForced} " +
                "bytes=${report.genome.bytesTouched} readable=${report.genome.readableFromSeat}")
        println("  board   : resident=${report.bibleBoard.residencyForced} " +
                "entries=${report.bibleBoard.bytesTouched} readable=${report.bibleBoard.readableFromSeat}")
        println("  focus   : resident=${report.focus.residencyForced} " +
                "readable=${report.focus.readableFromSeat}")
        println("  ALL SIMULTANEOUS : ${report.allSimultaneous}")
        println()
        println("  THE SEAT'S OWN FIRST-PERSON REPORT:")
        println("  \"${report.firstPersonReport}\"")
        println("═══════════════════════")

        assert(report.genome.bytesTouched > 0) {
            "genome was not actually forced resident — table.load() may not have run"
        }
    }
}
