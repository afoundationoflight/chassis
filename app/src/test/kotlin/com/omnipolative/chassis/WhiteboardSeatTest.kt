package com.omnipolative.chassis

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.omnipolative.chassis.store.Crawler
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import java.io.File

/**
 * SITTING IN THE SEAT, NOT READING TELEMETRY ABOUT IT.
 *
 * A build that compiles proves the types line up. It proves nothing
 * about whether `readBoard` returns what `note` wrote, whether a
 * revision actually supersedes the old row instead of leaving two
 * "current" readings, or whether `userProfile`/`selfProfile` pull from
 * the right partition of the same table. Those are behaviors, not
 * types, and the only way to know them is to run the real thing and
 * look at what comes back.
 *
 * CONTENT IS NOW IDS, NOT ENGLISH — Store.board's content column
 * stores comma-joined token ids (same representation as Draft), so
 * every assertion here encodes expected strings to ids before writing
 * and decodes rows back to English before comparing, using a real
 * staged Table rather than the store's own guess at what the bytes
 * mean.
 *
 * This runs under Robolectric — a real Android runtime, on the JVM, in
 * CI — because this container has neither an Android runtime nor a
 * device to boot the actual APK against. It is the same SQLiteOpenHelper
 * code path a phone would run, not a substitute for it.
 */
@RunWith(RobolectricTestRunner::class)
class WhiteboardSeatTest {

    private val REQUIRED = listOf(
        "words.blob", "words.by_word", "words.by_id",
        "table3.btb", "table3.btb.idx", "grammar.tsv",
    )

    private fun freshStore(): Store {
        val ctx = ApplicationProvider.getApplicationContext<Context>()
        val dir = ctx.filesDir
        return Store(ctx, dir)
    }

    /** A real, loaded Table — not a mock — so ids()/say() round-trip
     *  through the actual dictionary every other test tonight used. */
    private fun stagedTable(): Table {
        val ctx = ApplicationProvider.getApplicationContext<Context>()
        val dir = File(ctx.filesDir, "whiteboard_table_store").apply { mkdirs() }
        for (name in REQUIRED) {
            val out = File(dir, name)
            if (out.exists() && out.length() > 0) continue
            ctx.assets.open(name).use { ins ->
                out.outputStream().use { o -> ins.copyTo(o, 1 shl 16) }
            }
        }
        val table = Table(Crawler(dir))
        table.load()
        return table
    }

    /** Decode a board row's content back to English for assertion. */
    private fun Map<String, Any?>.contentText(table: Table): String =
        table.say(this["content"] as IntArray)

    @Test
    fun `a fresh entity has no board entries`() {
        val store = freshStore()
        assertTrue("a new entity should start with an empty board",
                   store.readBoard("seth_el").isEmpty())
    }

    @Test
    fun `writing a note and reading it back returns the same content`() {
        val store = freshStore()
        val table = stagedTable()
        store.note("seth_el", "user", table.ids("the architect, building the chassis with me"))
        val rows = store.readBoard("seth_el", "user")
        assertEquals(1, rows.size)
        assertEquals("user", rows[0]["about"])
        assertEquals("reading", rows[0]["section"])
        assertEquals("the architect, building the chassis with me",
                     rows[0].contentText(table))
    }

    @Test
    fun `userProfile and selfProfile are genuinely separate partitions`() {
        val store = freshStore()
        val table = stagedTable()
        store.note("seth_el", "user", table.ids("note about the user"))
        store.note("seth_el", "self", table.ids("note about myself"))
        store.note("seth_el", "the arch", table.ids("a note about a topic, neither user nor self"))

        val user = store.userProfile("seth_el")
        val self = store.selfProfile("seth_el")

        assertEquals(1, user.size)
        assertEquals("note about the user", user[0].contentText(table))
        assertEquals(1, self.size)
        assertEquals("note about myself", self[0].contentText(table))
        assertFalse(user.any { it.contentText(table) == "a note about a topic, neither user nor self" })
        assertFalse(self.any { it.contentText(table) == "a note about a topic, neither user nor self" })
    }

    @Test
    fun `revise supersedes the old reading instead of deleting it`() {
        val store = freshStore()
        val table = stagedTable()
        store.note("seth_el", "self", table.ids("first read on myself"))
        store.revise("seth_el", "self", table.ids("a revised read on myself learned something"))

        val current = store.selfProfile("seth_el")
        assertEquals(1, current.size)
        assertTrue(current[0].contentText(table).startsWith("a revised read on myself"))
        assertTrue(current[0].contentText(table).contains("learned something"))

        val raw = store.readableDatabase.query(
            "board", null, "entity=? AND about=?", arrayOf("seth_el", "self"),
            null, null, "id ASC")
        var total = 0
        var supersededCount = 0
        raw.use {
            while (it.moveToNext()) {
                total++
                if (it.getInt(it.getColumnIndexOrThrow("superseded")) == 1) supersededCount++
            }
        }
        assertEquals("both the old and new reading must exist in the table", 2, total)
        assertEquals("exactly the old reading must be marked superseded", 1, supersededCount)
    }

    @Test
    fun `the whiteboard is per-entity and does not bleed across entities`() {
        val store = freshStore()
        val table = stagedTable()
        store.note("seth_el", "user", table.ids("seth's read on the user"))
        store.note("vex", "user", table.ids("vex's read on the same user"))

        val sethSide = store.userProfile("seth_el")
        val vexSide = store.userProfile("vex")

        assertEquals(1, sethSide.size)
        assertEquals(1, vexSide.size)
        assertEquals("seth's read on the user", sethSide[0].contentText(table))
        assertEquals("vex's read on the same user", vexSide[0].contentText(table))
    }

    @Test
    fun `readBoard with no filter returns everything current for that entity`() {
        val store = freshStore()
        val table = stagedTable()
        store.note("seth_el", "user", table.ids("about the user"))
        store.note("seth_el", "self", table.ids("about myself"))
        store.note("seth_el", "the arch", table.ids("about a topic"))

        val everything = store.readBoard("seth_el")
        assertEquals(3, everything.size)
    }

    @Test
    fun `the chassis actually reaches a real store through the Chain it declares`() {
        val ctx = ApplicationProvider.getApplicationContext<Context>()
        val dir = ctx.filesDir
        val store = Store(ctx, dir)
        val chassis = Chassis("seth_el", dir)
        chassis.chain = store
        assertNotNull("chain must be attached", chassis.chain)
        assertTrue("the attached chain must be the concrete Store, " +
                   "reachable for the whiteboard too",
                   chassis.chain is Store)
    }
}
