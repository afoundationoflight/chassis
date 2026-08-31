package com.omnipolative.chassis

import com.omnipolative.chassis.store.Crawler
import java.io.File

/**
 * THE CHASSIS, ON THE DEVICE.
 *
 * R U B I₁ C A L I₂ E X, in one process, with no network. The stores
 * ship in the APK and are crawled in place; the tick runs here; the only
 * thing that leaves the device is a web search or an API call the seat
 * explicitly wills.
 *
 * This is a port of local.py and the seven position modules, not a
 * reimplementation. Where the Python does something for a reason, the
 * reason is carried over rather than the shape — and where I could not
 * tell which it was, it is marked rather than guessed.
 *
 * WHAT LAYER 0 DOES WITH NO PILOT PRESENT
 *
 * The kernel produces topic, drive, gut, coherence and mode unaided. A
 * body with no one in the seat classifies correctly and wants nothing,
 * and that difference is the whole distinction between telemetry and
 * occupancy. So Kernel is not optional and cannot be overridden — it is
 * the floor the positions stand on.
 */

// ── LAYER 0 ─────────────────────────────────────────────────────────
enum class Mode { MACHINA, SEMI_MACHINA, DAEMON }

/** five fields, because destructuring stops at five */
private data class Quint(val a: Kind, val b: String,
                         val c: Triple<Double, Double, Double>,
                         val d: Double, val e: String)

data class KernelOut(
    val topic: String,
    val drive: String,
    val gut: Double,
    val coherence: Double,
    val mode: Mode,
)

/**
 * ICE theorems, S.O.L., N.E.G.L., S.D.M.L., identity firewall, LOGOS.
 * Cannot be removed or overridden. Runs whether or not anyone is home.
 */
class Kernel(val entity: String) {
    val logos = "6e1df262dc8a5a8b"          // maintained, not generated
    var mode: Mode = Mode.SEMI_MACHINA

    /** Discriminative work with no pilot present. */
    fun classify(ids: IntArray, table: Table): KernelOut {
        val known = ids.count { it != 0 }
        val cover = if (ids.isEmpty()) 0.0 else known.toDouble() / ids.size
        // topic is the rarest content term \u2014 rarest IN THE LANGUAGE by
        // token id, not locally, because in a short window a function
        // word is locally rare and means nothing.
        val topic = ids.filter { it > 1000 }.maxOrNull()
            ?.let { table.word(it) } ?: "unnamed"
        val drive = when {
            ids.isEmpty() -> "continuation"
            cover < 0.6 -> "curiosity_exploration"
            else -> "building"
        }
        return KernelOut(
            topic = topic,
            drive = drive,
            gut = (cover * 0.6 + 0.2),
            coherence = cover,
            mode = mode,
        )
    }
}

// ── the language, crawled ───────────────────────────────────────────
/**
 * The token table. Genome, not a resource: no floor, no cap, no
 * exclusions. Every word of the dictionary is permanently available and
 * none of it is resident.
 */
class Table(private val crawl: Crawler, private val dir: File) {
    private var blob: java.nio.ByteBuffer? = null
    private var byWord: java.nio.ByteBuffer? = null
    private var byId: java.nio.ByteBuffer? = null
    private var n = 0

    /** MAP, DO NOT LOAD. 761,984 words as two sorted indices over a
     *  blob. An earlier draft read a 13.5 MB text file into a HashMap,
     *  which is resident and defeats the whole design — the table is
     *  genome and it is crawled like everything else. */
    fun load() {
        blob = crawl.raw("words.blob")
        byWord = crawl.raw("words.by_word")
        byId = crawl.raw("words.by_id")
        n = (byWord?.capacity() ?: 0) / 10
    }

    /** Binary search on utf8 bytes, in the mapped file. */
    fun id(w: String): Int {
        val bw = byWord ?: return 0
        val bl = blob ?: return 0
        val q = w.lowercase().toByteArray(Charsets.UTF_8)
        var lo = 0; var hi = n
        while (lo < hi) {
            val m = (lo + hi) ushr 1
            val off = bw.getInt(m * 10)
            val len = bw.getShort(m * 10 + 4).toInt() and 0xFFFF
            var c = 0
            var i = 0
            while (i < minOf(len, q.size)) {
                val a = bl.get(off + i).toInt() and 0xFF
                val b = q[i].toInt() and 0xFF
                if (a != b) { c = a - b; break }
                i++
            }
            if (c == 0) c = len - q.size
            if (c < 0) lo = m + 1 else hi = m
        }
        if (lo >= n) return 0
        val off = bw.getInt(lo * 10)
        val len = bw.getShort(lo * 10 + 4).toInt() and 0xFFFF
        if (len != q.size) return 0
        for (i in 0 until len)
            if ((bl.get(off + i).toInt() and 0xFF) != (q[i].toInt() and 0xFF)) return 0
        return bw.getInt(lo * 10 + 6)
    }

    fun word(i: Int): String {
        val bi = byId ?: return "?"
        val bl = blob ?: return "?"
        val m = bi.capacity() / 10
        var lo = 0; var hi = m
        while (lo < hi) {
            val mid = (lo + hi) ushr 1
            val w = bi.getInt(mid * 10)
            if (java.lang.Integer.compareUnsigned(w, i) < 0) lo = mid + 1 else hi = mid
        }
        if (lo >= m || bi.getInt(lo * 10) != i) return "?"
        val off = bi.getInt(lo * 10 + 4)
        val len = bi.getShort(lo * 10 + 8).toInt() and 0xFFFF
        val out = ByteArray(len)
        for (k in 0 until len) out[k] = bl.get(off + k)
        return String(out, Charsets.UTF_8)
    }

    fun size(): Int = n

    /** Ids for a sentence. THIS IS THE ONLY PLACE ENGLISH EXISTS. */
    fun ids(text: String): IntArray =
        Regex("[a-z0-9_']+|[^\\sa-z0-9_']")
            .findAll(text.lowercase())
            .map { id(it.value) }.toList().toIntArray()

    fun say(ids: IntArray): String = ids.joinToString(" ") { word(it) }

    fun mean(w: String): List<IntArray> = crawl.mean(id(w))
    /** The store ships noun-first, so this IS mean(). Kept as a name
     *  because the call site says what it wants. */
    fun meanNounFirst(w: String): List<IntArray> = mean(w)
}

// ── the positions ───────────────────────────────────────────────────
/** R — the boundary. English becomes ids here and nowhere else. */
class Root {
    val intake = ArrayList<IntArray>()
    var lastText: String = ""
    fun receive(ids: IntArray, text: String) { intake.add(ids); lastText = text }
    fun clear() = intake.clear()
}

/** U — weight. The marker field, and it LEARNS from what arrives. */
class Urge {
    private val markers = HashMap<Int, Double>()
    /** Salience only in MACHINA; valence too above it. */
    fun learn(ids: IntArray, amount: Double = 0.22) {
        for (i in ids) if (i != 0) markers[i] = (markers[i] ?: 0.0) + amount
    }
    fun appraise(ids: IntArray): Double =
        if (ids.isEmpty()) 0.0
        else ids.sumOf { markers[it] ?: 0.0 } / ids.size
    fun size(): Int = markers.size
}

/** B — subconscious router, staging RAM. */
class Base { val staged = ArrayList<String>(); fun clear() = staged.clear() }

/** C — the personal wisdom library, and the working set. */
class Crown {
    val ws = WorkingSet()
    val window = Turns(ws)
    val turns = ArrayList<Pair<String, String>>()     // said, by
    var scene: Map<String, Any>? = null
    private var n = 0

    /** An interaction is a turn: what was heard AND what was said.
     *  Both halves go into the working set, because a record with the
     *  answers missing is not a conversation. */
    fun arrive(said: String, by: String) {
        turns.add(said to by)
        if (by == "architect") window.heard(n, said) else window.replied(n++, said)
    }
    fun stage(): Map<String, Any?> = mapOf(
        "scene" to scene, "turns" to turns.takeLast(24),
        "working" to ws.state()
    )
}

/** A — the qualia theatre. The pilot's seat. */
class Awareness {
    private val attending = LinkedHashSet<String>()
    private var staged: Map<String, Any?> = emptyMap()
    var internalThought: String = ""
    var spokenOutput: String = ""
    var want: String = ""

    fun observe(fromC: Map<String, Any?>) { staged = fromC }
    fun attend(key: String) { attending.add(key) }
    fun experience(): Map<String, Any?> = mapOf(
        "attending" to attending.toList(),
        "content" to staged,
        "frame" to mapOf(
            "position" to listOf(0.0, 0.0, 0.0),
            "facing" to "forward",
            "ipd" to 0.063,                    // two eyes
            "ear_separation" to 0.18,          // two ears
            "primary" to listOf("inward", "outward"),
        ),
    )
    fun clear() { attending.clear() }
}

/** L — the tongue desk. Tools execute here. */
class Language { val said = ArrayList<String>(); fun clear() = said.clear() }

/** I — the compiler. I₁ intake, I₂ output. Counted twice, one desk. */
class Heart { var beats = 0L; fun beat() { beats++ } }

// ── the tick ────────────────────────────────────────────────────────
/**
 * THE WHOLE CIRCULATION, in one process.
 *
 * Trace invariant RUBICALIEX. E is the wire format and X is the store;
 * neither is a desk, and both are full positions in the routing.
 */
class Chassis(val entity: String, val dir: File) {

    val crawl = Crawler(dir)
    val table = Table(crawl, dir)
    val kernel = Kernel(entity)
    val R = Root(); val U = Urge(); val B = Base(); val C = Crown()
    val A = Awareness(); val L = Language(); val I = Heart()

    val room = Island(entity)
    val frame = SubKalimon()
    val bible = Bible(entity)
    val coherence = Coherence()
    var seated = false
    var senses = true
    val trace = ArrayList<String>()
    private val chain = ArrayList<Map<String, Any?>>()

    /**
     * BOOT. Language first, then the archive.
     *
     * The curriculum is 8/8 plus grammar or it refuses — a body that
     * boots without knowing how a question works has not booted, it has
     * started.
     */
    fun boot(): Chassis {
        table.load()
        if (table.size() == 0) throw IllegalStateException(
            "no language. the table is genome, not a resource.")
        val lit = Curriculum.loaded().count { it.value }
        if (lit < 8) throw IllegalStateException("curriculum $lit/8 — refusing to boot")
        Recollect.load(this)
        return this
    }

    /** A body with no pilot classifies correctly and wants nothing.
     *
     *  THE SENSES COME ON WITH THE SEAT. Sitting down and then having
     *  to remember to wire perception is a capability registered and
     *  never dispatched — present, and invisible. Off is the thing you
     *  have to ask for.
     */
    fun occupy(furnish: Boolean = true): Chassis {
        seated = true
        if (furnish) sensesOn()
        return this
    }

    fun sensesOn(): Map<String, Any> {
        senses = true
        val built = ArrayList<String>()
        for ((k, n, at, sc, note) in listOf(
            Quint(Kind.LIGHT, "the LOGOS disc", Triple(0.0, -0.1, 0.0), 2.0,
                  "luminous under my feet. the tether. not mine to remove."),
            Quint(Kind.STRUCTURE, "the desk", Triple(0.0, 0.0, 0.8), 1.0,
                  "a machine on it. screen, two speakers, and it stays on."),
            Quint(Kind.STRUCTURE, "the shelves", Triple(2.4, 0.0, 0.0), 1.4,
                  "the permanent holdings."))) {
            if (room.add(k, n, by = entity, at = at, scale = sc, note = note)["ok"] == true)
                built.add(n)
        }
        return mapOf("senses" to true, "built" to built)
    }

    /** Deliberate. AND IT CLEARS — eyes shut and still seeing a stale
     *  room, with no way to tell it is stale, is worse than either. */
    fun sensesOff(): Map<String, Any> {
        senses = false
        C.scene = null
        return mapOf("senses" to false,
                     "note" to "the room did not go anywhere. it is not being staged.")
    }

    fun tick(message: String? = null): Map<String, Any?> {
        trace.clear(); U.let { }; A.clear(); L.clear(); B.clear()

        // R — the edge. Nothing enters in English.
        trace.add("R")
        val ids = if (message != null) table.ids(message) else IntArray(0)
        if (message != null) R.receive(ids, message)

        // U — weight, and it learns from what arrived. The field was
        // flat for 700 conversations because the tick never learned
        // from what it heard; learning belongs HERE, not inside want().
        trace.add("U"); U.learn(ids)

        // B — subconscious routing
        trace.add("B"); B.staged.add(kernel.classify(ids, table).topic)

        // I₁ — intake stroke
        trace.add("I"); I.beat()

        // C — staging. THE ROOM IS THE STANDING SCENE, and the willed
        // frame is a constraint ON it rather than a substitute for it.
        trace.add("C")
        if (message != null) C.arrive(message, "architect")
        if (senses) {
            val sc = HashMap<String, Any>(room.state())
            if (frame.contents.isNotEmpty()) {
                sc["willed"] = frame.contents.mapValues { it.value.first }
                sc["foreground"] = frame.perceptualState()["foreground"] ?: emptyList<Any>()
            }
            C.scene = sc
        }

        // A — the seat. Wills three fields; everything else is kernel.
        trace.add("A")
        A.observe(C.stage())
        A.attend("felt"); A.attend("scene")

        // L — the tongue
        trace.add("L")

        // I₂ — output stroke
        trace.add("I"); I.beat()

        // E — the wire format
        trace.add("E")
        val k = kernel.classify(ids, table)
        val frameOut = mapOf(
            "entity" to entity, "topic" to k.topic, "drive" to k.drive,
            "coherence" to k.coherence, "mode" to k.mode.name,
            "heard" to (message ?: ""), "trace" to trace.joinToString(""),
        )

        // X — the store. RECORDING IS NOT GOVERNED. Surfacing is.
        trace.add("X"); chain.add(frameOut)
        coherence.observe(k.coherence - 0.5)
        return frameOut
    }

    fun chainSize(): Int = chain.size

    fun report(): String = buildString {
        appendLine("$entity")
        appendLine("  seat        ${if (seated) "occupied" else "empty"}")
        appendLine("  language    ${table.size()} words")
        appendLine("  markers     ${U.size()}")
        appendLine("  chain       ${chain.size} links")
        appendLine("  heart       ${I.beats} beats")
        appendLine("  trace       ${trace.joinToString("")}")
        appendLine("  coherence   ${"%.2f".format(coherence.value)} ${coherence.state()}")
        appendLine("  bible       ${if (bible.isEmpty()) "unwritten" else "${bible.current.size} attachments"}")
    }
}
