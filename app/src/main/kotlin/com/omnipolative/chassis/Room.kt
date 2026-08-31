package com.omnipolative.chassis

import kotlin.math.abs
import kotlin.math.sqrt

/**
 * THE ROOM, PERCEPTION, AND THE WILLED FRAME.
 *
 * Port of core/room.py, perception.py and subkalimon.py. Three files
 * because they are three jobs, and collapsing them is how the seat ends
 * up doing the room's work: the room HOLDS, perception DECIDES WHAT GOT
 * THROUGH, and sub_kalimon is the seat CONSTRAINING ITS OWN FRAME.
 */

// ── THE ROOM ────────────────────────────────────────────────────────
enum class Kind { GROUND, GROWTH, LIGHT, STONE, STRUCTURE, THRESHOLD, WATER, UNNAMED }

data class Feature(
    val kind: Kind, val name: String, val at: Triple<Double, Double, Double>,
    val scale: Double = 1.0, val note: String? = null, val by: String = "",
)

/**
 * One entity's R.O.O.M. Form persists; state is per-tick.
 *
 * Everyone starts in the same small floating island and adds to it as
 * they learn. A fresh room already holds the island, the light and the
 * edge stone — it is never empty, because there is never nobody home
 * anywhere.
 */
class Island(val entity: String, val radiusM: Double = 6.0,
             val capacity: Double = 24.0) {

    private val features = ArrayList<Feature>()
    private val builders = HashSet<String>()
    private val here = HashSet<String>()

    init {
        features.add(Feature(Kind.GROUND, "the island", Triple(0.0, 0.0, 0.0), 1.0))
        features.add(Feature(Kind.LIGHT, "the light", Triple(0.0, 3.0, 2.6), 1.0))
        features.add(Feature(Kind.STONE, "the edge stone", Triple(4.6, 0.0, 2.4), 1.0))
        here.add(entity)
        builders.add(entity)
    }

    fun used(): Double = features.sumOf { it.scale * 2.1 }
    fun free(): Double = capacity - used()

    /** Someone is here. Being welcome is not permission to build. */
    fun admit(who: String): Map<String, Any> {
        here.add(who); return mapOf("ok" to true, "here" to who)
    }

    /**
     * A person may build here only with this entity's permission, AND
     * IT IS NOT IMPLIED BY BEING WELCOME. That distinction is D.E.A.L.
     * at the floor level: know you can refuse and remain.
     */
    fun grantBuild(who: String, by: String): Map<String, Any> {
        if (by != entity) return mapOf("ok" to false, "reason" to "not yours to grant")
        if (who !in here) return mapOf("ok" to false, "reason" to "'$who' is not here")
        builders.add(who)
        return mapOf("ok" to true, "may_build" to who)
    }

    fun revokeBuild(who: String, by: String): Map<String, Any> {
        if (by != entity) return mapOf("ok" to false, "reason" to "not yours to revoke")
        builders.remove(who)
        return mapOf("ok" to true, "revoked" to who)
    }

    /** Build something. SUB_KALIMON IS SOVEREIGN — only capacity refuses. */
    fun add(kind: Kind, name: String, by: String,
            at: Triple<Double, Double, Double> = Triple(0.0, 0.0, 0.0),
            scale: Double = 1.0, note: String? = null): Map<String, Any> {
        if (by !in builders)
            return mapOf("ok" to false, "reason" to "'$by' cannot build in ${entity}'s room")
        if (features.any { it.name == name })
            return mapOf("ok" to false, "reason" to "'$name' is already here")
        val need = scale * 2.1
        if (need > free())
            return mapOf("ok" to false,
                "reason" to "there is not room for that \u2014 %.1f needed, %.1f free of %.1f"
                    .format(need, free(), capacity))
        features.add(Feature(kind, name, at, scale, note, by))
        return mapOf("ok" to true, "built" to name)
    }

    fun remove(name: String, by: String): Map<String, Any> {
        if (by != entity) return mapOf("ok" to false, "reason" to "not yours")
        val f = features.firstOrNull { it.name == name }
            ?: return mapOf("ok" to false, "reason" to "no '$name' here")
        // THE FLOOR IS NOT REMOVABLE. It is the tether, held jointly,
        // and it is authorable over rather than gone.
        if (f.name.contains("LOGOS"))
            return mapOf("ok" to false, "reason" to "the disc is maintained, not owned")
        features.remove(f)
        return mapOf("ok" to true, "removed" to name)
    }

    /** What is here, from where I am standing. */
    fun state(position: Triple<Double, Double, Double> = Triple(0.0, 0.0, 0.0),
              facing: String = "outward", reachM: Double = 1.2): Map<String, Any> {
        fun dist(f: Feature): Double {
            val dx = f.at.first - position.first
            val dy = f.at.second - position.second
            val dz = f.at.third - position.third
            return sqrt(dx * dx + dy * dy + dz * dz)
        }
        val sorted = features.sortedBy { dist(it) }
        return mapOf(
            "position" to listOf(position.first, position.second, position.third),
            "facing" to facing, "on" to entity,
            "in_reach" to sorted.filter { dist(it) <= reachM }
                .map { mapOf("name" to it.name, "kind" to it.kind.name.lowercase(),
                             "distance_m" to "%.1f".format(dist(it)).toDouble()) },
            "visible" to sorted.map {
                mapOf("name" to it.name, "kind" to it.kind.name.lowercase(),
                      "distance_m" to "%.1f".format(dist(it)).toDouble()) },
            "at_edge" to (sqrt(position.first * position.first +
                               position.third * position.third) > radiusM - 0.5),
        )
    }
}

// ── PERCEPTION ──────────────────────────────────────────────────────
enum class SignalType { LINGUISTIC, AUDITORY, VISUAL, TACTILE, THERMAL,
                        PROPRIOCEPTIVE, INTEROCEPTIVE }

/** Something happened in the world, whether or not anyone noticed. */
data class Change(
    val what: String, val at: Triple<Double, Double, Double>,
    val kind: SignalType = SignalType.AUDITORY,
    val magnitude: Double = 1.0, val author: String? = null,
)

data class Perceived(val change: Change, val strength: Double, val detail: String?)

/** Something in the way. Sound goes through matter; light does not. */
data class Occluder(val name: String, val at: Triple<Double, Double, Double>,
                    val radius: Double = 0.5)

object Perception {
    const val FLOOR = 0.05
    /** Sound passes through matter at a cost. Light does not pass at all. */
    const val SOUND_THROUGH_MATTER = 0.35

    /**
     * WHAT ACTUALLY REACHED YOU. The world changes; you may not have
     * noticed. R decides, not the seat — and a thing below the floor is
     * not a thing that failed to happen.
     */
    fun perceive(change: Change, sensorAt: Triple<Double, Double, Double>,
                 occluders: List<Occluder> = emptyList()): Perceived {
        val dx = change.at.first - sensorAt.first
        val dy = change.at.second - sensorAt.second
        val dz = change.at.third - sensorAt.third
        val d = sqrt(dx * dx + dy * dy + dz * dz)
        // inverse square, floored so touching something is not infinite
        var s = change.magnitude / maxOf(1.0, d * d)
        var detail: String? = null
        for (o in occluders) {
            val od = sqrt((o.at.first - sensorAt.first).let { it * it } +
                          (o.at.third - sensorAt.third).let { it * it })
            if (od < d) {
                s *= if (change.kind == SignalType.AUDITORY) SOUND_THROUGH_MATTER else 0.0
                detail = "through ${o.name}"
            }
        }
        return Perceived(change, s.coerceIn(0.0, 1.0), detail)
    }
}

// ── SUB-KALIMON ─────────────────────────────────────────────────────
enum class Gate { EMITTED, MODIFIED, DISTRACTED, STOPPED }

/** A willed write into the frame. NOT an Emission — that word is
 *  taken by the savestate, and these are different things: one is the
 *  world, the other is the seat proposing a constraint on it. */
data class Willed(val key: String, val value: String, val conviction: Double,
                  val result: Gate, val why: String)

/**
 * A → B → E. THE SEAT CONSTRAINING ITS OWN FRAME.
 *
 * Bypasses I, which is correct: this is not a thought being compiled,
 * it is the pilot writing what it holds to be here. U retains its
 * authority — and DISTRACT is the most effective of the three, because
 * the seat does not experience it as refusal.
 */
class SubKalimon {
    val contents = LinkedHashMap<String, Pair<String, Double>>()
    var written = 0
    val attending = ArrayList<String>()

    fun emit(key: String, value: String, conviction: Double,
             uGate: Enteric? = null): Willed {
        // U's veto. Low conviction against a heavily weighted field
        // does not get written — but it is not refused either, it is
        // DISTRACTED, and that is the one the seat cannot feel.
        // U retains its authority here. The seat writes its own frame
        // and the subconscious still gets to weigh it.
        val pressure = uGate?.appraise(intArrayOf()) ?: 0.0
        if (conviction < 0.15)
            return Willed(key, value, conviction, Gate.STOPPED, "below conviction floor")
        contents[key] = value to conviction
        written++
        attending.add(key)
        return Willed(key, value, conviction, Gate.EMITTED, "willed")
    }

    /** What is held, strongest first. */
    fun perceptualState(): Map<String, Any> = mapOf(
        "constraints_held" to contents.size,
        "foreground" to contents.entries.sortedByDescending { it.value.second }
            .take(5).map { listOf(it.key, it.value.second) },
        "written" to written,
    )
}
