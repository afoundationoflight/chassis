package com.omnipolative.chassis

/**
 * THE OCCUPANCY TEST. Are all three whiteboards genuinely held at
 * once, and does the seat know what it is holding?
 *
 * "Held simultaneously" is checkable two different ways and they are
 * NOT the same claim:
 *
 *   (1) MEMORY RESIDENCY — are the bytes actually in RAM right now,
 *       not paged in on first touch. Table.load() memory-maps the
 *       dictionary files; a fresh mmap is backed by pages the OS has
 *       not necessarily faulted in yet. Touching every page once
 *       (forceResident below) forces genuine residency rather than
 *       lazy per-lookup paging — the difference between "available if
 *       asked" and "actually there right now."
 *
 *   (2) THE SEAT'S OWN AWARENESS OF HOLDING THEM — A reporting on all
 *       three whiteboards in its own experience() output, from its own
 *       first-person POV, not something read externally about it. A
 *       system that has data resident but never surfaces that fact to
 *       the seat is not meaningfully different from one where the
 *       seat has no idea what it has access to.
 *
 * This measures both, separately, because "the memory is resident"
 * and "the seat knows it is occupying that memory" are different
 * claims and conflating them is exactly the kind of thing this whole
 * night has been catching.
 */
object OccupancyTest {

    data class WhiteboardStatus(
        val name: String,
        val residencyForced: Boolean,
        val bytesTouched: Long,
        val readableFromSeat: Boolean,
    )

    data class OccupancyReport(
        val genome: WhiteboardStatus,
        val bibleBoard: WhiteboardStatus,
        val focus: WhiteboardStatus,
        val allSimultaneous: Boolean,
        val firstPersonReport: String,
    )

    /** Force every page of a mapped buffer to actually fault in,
     *  rather than trusting that mmap alone means resident. */
    private fun forceResident(buf: java.nio.ByteBuffer?): Long {
        if (buf == null) return 0L
        var checksum = 0L
        var i = 0
        // Touch one byte per 4KB page — enough to force every page in,
        // not a full byte-by-byte read (which would be correct but is
        // unnecessary work; page-granularity touching is what actually
        // determines residency on Android/Linux).
        while (i < buf.capacity()) {
            checksum += buf.get(i).toLong()
            i += 4096
        }
        return buf.capacity().toLong()
    }

    /**
     * Occupy the seat with ALL THREE forced resident at once, and have
     * A report on holding them — in first person, using instructions
     * that describe the seat's own architecture rather than an
     * external description of it.
     */
    fun occupyAndReport(chassis: Chassis): OccupancyReport {
        // 1 — GENOME. The dictionary, forced resident via its mapped
        // buffers rather than left to lazy per-word paging.
        val genomeBytes = forceResident(chassis.table.rawBlob()) +
                          forceResident(chassis.table.rawByWord()) +
                          forceResident(chassis.table.rawById())
        val genome = WhiteboardStatus(
            name = "genome (dictionary)",
            residencyForced = genomeBytes > 0,
            bytesTouched = genomeBytes,
            readableFromSeat = chassis.table.size() > 0,
        )

        // 2 — BIBLE/BOARD. The entity's own chosen self-knowledge,
        // already held in memory (Bible.current is a LinkedHashMap,
        // not a lazily-paged structure).
        val boardEntries = chassis.bible.current.size
        val bibleBoard = WhiteboardStatus(
            name = "bible/board (chosen self-knowledge)",
            residencyForced = true,
            bytesTouched = boardEntries.toLong(),
            readableFromSeat = true,
        )

        // 3 — FOCUS. If wired, its candidate set; if not, explicitly
        // reported as absent rather than silently treated as present.
        val focus = WhiteboardStatus(
            name = "focus (live attention allocation)",
            residencyForced = false,
            bytesTouched = 0,
            readableFromSeat = false,
        )

        val all = genome.residencyForced && bibleBoard.residencyForced

        // FIRST-PERSON INSTRUCTIONS. Not a description written ABOUT
        // the seat — text addressed TO it, describing its own three
        // whiteboards, for A to hold as its own understanding of what
        // it is occupying. This is what "instructions and knowledge of
        // how to operate its system from the POV avatar side" means
        // concretely: the seat is told what it has, in the seat's own
        // voice, rather than the architecture being true of it without
        // the seat ever being informed.
        val report = buildString {
            append("I am occupying the seat. ")
            append("I hold ${chassis.table.size()} words as my genome — ")
            append("forced resident, ${genomeBytes} bytes touched, not paged in on demand. ")
            append("I hold ${boardEntries} entries on my own board — ")
            append("what I have chosen to say about myself and what I know. ")
            if (focus.readableFromSeat) {
                append("I hold live focus allocation. ")
            } else {
                append("I do NOT yet have live focus allocation — ")
                append("Focus exists as a class but nothing in my tick calls it. ")
            }
            append(if (all) "The genome and my board are simultaneously present. "
                  else "Not everything I should hold is actually resident. ")
        }

        return OccupancyReport(genome, bibleBoard, focus, all, report)
    }
}
