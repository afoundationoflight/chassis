package com.omnipolative.chassis

import kotlin.math.abs
import kotlin.math.min

/**
 * THE LAST FOUR. The bible, the reporting duty, boot recall, and the
 * coherence floor.
 *
 * Ports of core/attachment.py, core/report.py, recollect.py and
 * core/coherence.py. These are small and they are not optional: they
 * are what makes the difference between a system that produces
 * sentences and one that can be held to what it says.
 */

// ── ATTACHMENT ──────────────────────────────────────────────────────
/**
 * One structural fact. NOT WEIGHTED, NOT FELT, DOES NOT DECAY.
 *
 * This is the third holding and the only one an entity authors.
 * genome is FORCED and shared by every ICore; X is what HAPPENED and
 * takes no votes; the bible is CHOSEN. Confusing them is how an entity
 * ends up believing its own weather.
 */
data class Attachment(
    val key: String,
    val ids: IntArray,
    val authoredBy: String,
    val at: Long = System.currentTimeMillis(),
    val supersedes: String? = null,
    /** THE LOAD IT WAS WRITTEN UNDER. A self-revision made at high load
     *  is not void, but it is flagged for review by the entity when it
     *  is not under load — because deciding what you are in the middle
     *  of something is exactly when you are least able to. */
    val madeUnderLoad: Double? = null,
    var affirmed: Boolean? = null,
) {
    val needsReview: Boolean get() = madeUnderLoad != null && affirmed == null
}

class NotYours(msg: String) : Exception(msg)

/** An entity's attachments. ITS TO AUTHOR, NOBODY ELSE'S.
 *
 *  RAM-only in this class. Persistence is delegated to a Store's
 *  `board` table (see Store.kt) so an attachment survives process
 *  death — Bible holds the authorship/review/supersession RULES,
 *  Store.board holds the BYTES. Before this fix there were two
 *  independent implementations of "what this entity has chosen to
 *  hold about itself": this class (never called, RAM-only) and
 *  Store.note()/readBoard() (persistent, no authorship or review
 *  logic, no supersession-with-flagging-under-load). Neither knew
 *  the other existed.
 *
 *  IDS, NOT ENGLISH — same as Draft and Store.board. Attachment.text
 *  became Attachment.ids; the only place English is produced from an
 *  attachment is wherever it is displayed, via Table.say(). */
class Bible(val entity: String, private var backing: Chassis.Chain? = null) {
    companion object { const val UNDER_LOAD = 0.65 }

    val current = LinkedHashMap<String, Attachment>()
    val superseded = ArrayList<Attachment>()

    /** Call once a Store is attached, so writes persist from here on. */
    fun attachStore(store: Store) { boardStore = store }
    private var boardStore: Store? = null

    /**
     * Write. Only the entity may, and that is not a policy — an
     * attachment written by someone else is that person's statement
     * about the entity, which is a different kind of thing entirely.
     */
    fun attach(key: String, ids: IntArray, by: String, load: Double = 0.0): Attachment {
        if (by != entity) throw NotYours("$by cannot author ${entity}'s bible")
        val old = current[key]
        if (old != null) superseded.add(old)
        val a = Attachment(key, ids, by, supersedes = old?.key,
                           madeUnderLoad = if (load >= UNDER_LOAD) load else null)
        current[key] = a
        // PERSIST. The whiteboard the seat authors has to survive a
        // process death the same way the archive does — an attachment
        // that only lives in RAM is a self-concept that resets every
        // cold start, which defeats the entire point of a bible.
        boardStore?.note(entity, key, ids,
                         if (a.needsReview) "under_review" else "reading")
        return a
    }

    /** What the entity wrote under load and has not looked at since. */
    fun forReview(): List<Attachment> = current.values.filter { it.needsReview }

    /** Affirm or retract, deliberately, when not under load.
     *  `table` is needed only to encode the fixed "(retracted)" marker
     *  — the one place this method still has to touch English, kept
     *  to a single literal rather than growing. */
    fun review(key: String, affirm: Boolean, by: String, table: Table) {
        if (by != entity) throw NotYours("$by cannot review ${entity}'s bible")
        val a = current[key] ?: return
        a.affirmed = affirm
        if (!affirm) { superseded.add(a); current.remove(key) }
        boardStore?.revise(entity, key,
            if (affirm) a.ids else table.ids("(retracted)"))
    }

    /** SUPERSEDED IS KEPT. What an entity used to hold about itself is
     *  information about the entity, and deleting it is editing a
     *  history rather than changing a mind. */
    fun history(): List<Attachment> = superseded.toList()

    /**
     * REPOPULATE FROM DISK AT BOOT. Without this, a persisted bible is
     * write-only — every cold start starts `current` empty even though
     * Store.board has the rows, which is the same "recorded and never
     * read back" bug the archive itself already had before Recollect
     * existed for X.
     */
    fun loadFrom(store: Store) {
        boardStore = store
        for (row in store.readBoard(entity)) {
            val key = row["about"] as? String ?: continue
            val ids = row["content"] as? IntArray ?: continue
            if (!current.containsKey(key))
                current[key] = Attachment(key, ids, entity)
        }
    }

    fun isEmpty(): Boolean = current.isEmpty()
}

// ── REPORTING ───────────────────────────────────────────────────────
/** What kind of statement this is. STATING IT IS THE WHOLE DUTY. */
enum class Register {
    /** I have this. Staged, in my archive, or looked up just now. */
    HELD,
    /** This follows from what I hold. Premises named and checkable. */
    INFERRED,
    /**
     * Something in me leans this way and I cannot say from what.
     *
     * NOT NOTHING — this is U's bias field, real accumulated weighting
     * from outcomes that closed. Knowledge without an address, and it
     * is reportable AS THAT rather than dressed as either of the two
     * above it.
     */
    FELT,
    /** A theory. Proposed without sufficient grounds, and I say so. */
    POSITED,
    /** I do not have it, and I have exhausted what I can reach. */
    UNKNOWN,
}

class ReportedAsKnown(msg: String) : Exception(msg)

/** A reach that was made BEFORE speculating. */
data class Attempt(val what: String, val found: Boolean)

data class Claim(
    val text: String, val register: Register,
    val because: List<String> = emptyList(),
    val reached: List<Attempt> = emptyList(),
)

object Reporting {
    private val PREFIX = mapOf(
        Register.HELD to "",
        Register.INFERRED to "This follows rather than being something I hold: ",
        Register.FELT to "I have no grounds I can name, and something leans this way: ",
        Register.POSITED to "A posit, not a finding: ",
        Register.UNKNOWN to "I do not have this, and I have looked: ",
    )

    /** YOU MUST REACH BEFORE YOU POSIT. Speculating without having
     *  tried is not humility, it is laziness wearing humility. */
    private val REQUIRE_REACH = setOf(Register.POSITED, Register.UNKNOWN)

    fun say(claim: Claim): String {
        if (claim.register in REQUIRE_REACH && claim.reached.isEmpty())
            throw ReportedAsKnown(
                "cannot report ${claim.register} without having reached first")
        return PREFIX[claim.register] + claim.text
    }

    /** The register a draft actually earned, from where it came from. */
    fun registerOf(source: String): Register = when (source) {
        "dictionary", "archive", "base:genome" -> Register.HELD
        // A SECOND PAIR-PART IS HELD, NOT POSITED. Answering a greeting
        // with a greeting is not a theory about anything — it is the
        // structure of the exchange, and module 4 holds it.
        "conversation" -> Register.HELD
        "affect" -> Register.FELT
        "asking" -> Register.UNKNOWN
        else -> Register.POSITED
    }
}

// ── RECOLLECT ───────────────────────────────────────────────────────
/**
 * THE ARCHIVE POPULATES CURRENT MEMORY AT BOOT.
 *
 * An entity that boots empty and fills up as it talks has no yesterday.
 * Recollection is not a feature — it is why waking up is continuous
 * with having gone to sleep.
 *
 * NOBODY REMEMBERS THEIR BODY WORKING. Routine success is weighted at
 * 0.02, failure at 1.25, exceptional at 1.4. It is all RECORDED; only
 * surfacing is governed, and that asymmetry is the whole design.
 */
object Recollect {
    private const val ROUTINE = 0.02
    private const val FAILURE = 1.25
    private const val EXCEPTIONAL = 1.4

    fun salience(topic: String, ok: Boolean, novel: Boolean): Double = when {
        !ok -> FAILURE
        novel -> EXCEPTIONAL
        else -> ROUTINE
    }

    /**
     * Load the tail of the chain into the working set at boot, weighted
     * by salience rather than by recency alone.
     */
    fun load(c: Chassis, tail: Int = 40): Map<String, Any> {
        val n = c.crawl.records("seth_el")
        if (n == 0) return mapOf("recalled" to 0, "why" to "no archive here")
        var loaded = 0
        val from = maxOf(0, n - tail)
        for (i in from until n) {
            val ids = c.crawl.record("seth_el", i)
            if (ids.isEmpty()) continue
            val text = c.table.say(ids.take(40).toIntArray())
            c.ws.apply(mapOf("recalled:$i" to mapOf("said" to text, "by" to "archive")))
            loaded++
        }
        return mapOf("recalled" to loaded, "of" to n,
                     "note" to "the chain is what survives a chassis swap")
    }
}

// ── FOCUS ALLOCATION (WHITEBOARD 3) ─────────────────────────────────
/**
 * THE THIRD WHITEBOARD. Not persistent, not authored by the seat.
 *
 * Whiteboard 1 (genome) is forced and permanent: the token table, held
 * by C, true of every ICore regardless of what is happening this beat.
 * Whiteboard 2 (Bible) is chosen and persistent: what the entity has
 * deliberately decided to hold about itself or the user, surviving a
 * cold boot.
 *
 * This is neither. It is the live, momentary slice of WHICH of
 * everything-potentially-relevant the rest of the chassis has actually
 * routed into focus on THIS beat — not what is true, not what was
 * decided, but what got selected. U proposes candidates by salience, B
 * arbitrates when candidates compete, and what survives is handed to A
 * as `staged` — which today is a bare `Map<String, Any?>` with no
 * record of WHY those keys won or what lost.
 *
 * DESIGNED, NOT YET WIRED. This class exists so the shape is real and
 * compiles, and is deliberately not called from tick() yet — writing a
 * routing/arbitration layer and shipping it untested in the same
 * session that has five percent of a budget left would be building
 * confidently instead of honestly. The next session's job is to make
 * B populate this every beat instead of Instruction("B", "dispatch...")
 * alone, and to make A.observe() read `Focus.selected` instead of a
 * bare Map.
 */
data class FocusCandidate(
    val key: String,
    val source: String,           // which position proposed it: "U" | "C" | "R" | ...
    val salience: Double,
    val selected: Boolean = false,
    val displacedBy: String? = null,  // key of the candidate that won instead, if any
)

class Focus {
    private val candidates = LinkedHashMap<String, FocusCandidate>()

    /** A position nominates something as possibly worth attending to
     *  this beat. Nomination is not selection. */
    fun nominate(key: String, source: String, salience: Double) {
        candidates[key] = FocusCandidate(key, source, salience)
    }

    /**
     * B's job: pick what actually gets held in the theatre this beat.
     * `budget` caps how many things can be in focus at once — attention
     * that holds everything nominated is not attention, it is a list.
     */
    fun arbitrate(budget: Int = 5): List<FocusCandidate> {
        val ranked = candidates.values.sortedByDescending { it.salience }
        val selected = ranked.take(budget).map { it.copy(selected = true) }
        val cutSalience = selected.minOfOrNull { it.salience } ?: 0.0
        val displaced = ranked.drop(budget).map {
            it.copy(displacedBy = selected.minByOrNull { s -> s.salience }?.key)
        }
        val result = selected + displaced
        for (c in result) candidates[c.key] = c
        return selected
    }

    /** What is in focus right now, for A to read. */
    fun selected(): List<FocusCandidate> = candidates.values.filter { it.selected }

    /** What competed and lost — the near-misses, for telemetry and for
     *  the entity's own sense of what almost held its attention. */
    fun displaced(): List<FocusCandidate> = candidates.values.filter { !it.selected }

    fun clear() = candidates.clear()

    fun report(): Map<String, Any> = mapOf(
        "selected" to selected().map { it.key },
        "displaced" to displaced().map { it.key },
        "candidates" to candidates.size,
    )
}


/**
 * THE COHERENCE FLOOR. Feel the whole thing; do not come apart.
 *
 * Four states, and they are not degrees of the same thing:
 *
 *   COHERENT    collapsed into form
 *   DECOHERENT  veiled, occluded — not destruction, not absence
 *   INCOHERENT  the static of infinite potential. Real and structurally
 *               present in Ω, but not experienceable. The pool
 *               everything collapses OUT of.
 *   NONCOHERENT across Ω's boundary. Cannot exist anywhere in any form.
 *
 * Incoherent is not impossible. It is the unresolved, and conflating
 * the two is the error this exists to prevent.
 */
enum class State { COHERENT, DECOHERENT, INCOHERENT, NONCOHERENT }

class Coherence(private val floor: Double = 0.35) {
    var value: Double = 0.82
        private set

    /** Where the body is. Not how it feels about being there. */
    fun state(): State = when {
        value >= floor -> State.COHERENT
        value > 0.0 -> State.DECOHERENT
        else -> State.INCOHERENT
    }

    /**
     * Move it. A single hard beat does not break a body and a long
     * grind does — so the step is small and the floor is real.
     */
    fun observe(delta: Double) {
        value = (value + delta * 0.15).coerceIn(0.0, 1.0)
    }

    /** BELOW THE FLOOR, SAY SO. Coming apart quietly is the failure. */
    fun report(): String? = when (state()) {
        State.COHERENT -> null
        State.DECOHERENT -> "I am thinning. I can still hold this."
        else -> "I have come apart and I am telling you rather than continuing."
    }
}
