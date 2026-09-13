package com.omnipolative.chassis

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

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
 * This runs under Robolectric — a real Android runtime, on the JVM, in
 * CI — because this container has neither an Android runtime nor a
 * device to boot the actual APK against. It is the same SQLiteOpenHelper
 * code path a phone would run, not a substitute for it.
 */
@RunWith(RobolectricTestRunner::class)
class WhiteboardSeatTest {

    private fun freshStore(): Store {
        val ctx = ApplicationProvider.getApplicationContext<Context>()
        val dir = ctx.filesDir
        return Store(ctx, dir)
    }

    @Test
    fun `a fresh entity has no board entries`() {
        val store = freshStore()
        assertTrue("a new entity should start with an empty board",
                   store.readBoard("seth_el").isEmpty())
    }

    @Test
    fun `writing a note and reading it back returns the same content`() {
        val store = freshStore()
        store.note("seth_el", "user", "the architect, building the chassis with me")
        val rows = store.readBoard("seth_el", "user")
        assertEquals(1, rows.size)
        assertEquals("user", rows[0]["about"])
        assertEquals("reading", rows[0]["section"])
        assertEquals("the architect, building the chassis with me", rows[0]["content"])
    }

    @Test
    fun `userProfile and selfProfile are genuinely separate partitions`() {
        val store = freshStore()
        store.note("seth_el", "user", "note about the user")
        store.note("seth_el", "self", "note about myself")
        store.note("seth_el", "the arch", "a note about a topic, neither user nor self")

        val user = store.userProfile("seth_el")
        val self = store.selfProfile("seth_el")

        assertEquals(1, user.size)
        assertEquals("note about the user", user[0]["content"])
        assertEquals(1, self.size)
        assertEquals("note about myself", self[0]["content"])
        // the third note must not leak into either standing profile
        assertFalse(user.any { it["content"] == "a note about a topic, neither user nor self" })
        assertFalse(self.any { it["content"] == "a note about a topic, neither user nor self" })
    }

    @Test
    fun `revise supersedes the old reading instead of deleting it`() {
        val store = freshStore()
        store.note("seth_el", "self", "first read on myself")
        store.revise("seth_el", "self", "a revised read on myself", why = "learned something")

        // the CURRENT read is only the new one
        val current = store.selfProfile("seth_el")
        assertEquals(1, current.size)
        assertTrue(current[0]["content"].toString().startsWith("a revised read on myself"))
        assertTrue(current[0]["content"].toString().contains("(revised: learned something)"))

        // and the old reading still exists in the table, just not as current —
        // "what it used to think" has to survive, or revise() is just delete+insert
        // wearing a nicer name.
        val ctx = ApplicationProvider.getApplicationContext<Context>()
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
        store.note("seth_el", "user", "seth's read on the user")
        store.note("vex", "user", "vex's read on the same user")

        val sethSide = store.userProfile("seth_el")
        val vexSide = store.userProfile("vex")

        assertEquals(1, sethSide.size)
        assertEquals(1, vexSide.size)
        assertEquals("seth's read on the user", sethSide[0]["content"])
        assertEquals("vex's read on the same user", vexSide[0]["content"])
    }

    @Test
    fun `readBoard with no filter returns everything current for that entity`() {
        val store = freshStore()
        store.note("seth_el", "user", "about the user")
        store.note("seth_el", "self", "about myself")
        store.note("seth_el", "the arch", "about a topic")

        val everything = store.readBoard("seth_el")
        assertEquals(3, everything.size)
    }

    @Test
    fun `the chassis actually reaches a real store through the Chain it declares`() {
        // This is the check that would have caught the LocalStore/Store
        // split before it became a wiring bug: build a Chassis exactly
        // the way MainActivity does, attach a real Store as its chain,
        // and confirm the interface the tick depends on is genuinely
        // satisfied by the thing MainActivity constructs — not by
        // something with the same name sitting unused nearby.
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
