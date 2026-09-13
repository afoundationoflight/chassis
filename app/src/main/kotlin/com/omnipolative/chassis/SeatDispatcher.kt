package com.omnipolative.chassis

/**
 * WHAT THE SEAT MAY WILL. One choke point, regardless of who is
 * occupying it.
 *
 * Before this, "switch to a remote mind" implied the remote model
 * would need some way to touch the whiteboard, and the naive shape of
 * that is either (a) hand it raw storage access, which breaks
 * authorship enforcement, or (b) have it emit free text that something
 * tries to parse into actions after the fact, which is guessable and
 * silently lossy.
 *
 * TOOL CALLS are the actual answer: whichever mind occupies A wills a
 * typed action, exactly as A.propose() already does for the local
 * reasoner (seat.want, seat.thought as Instructions). This just widens
 * that same pattern to cover whiteboard writes and gives it one
 * dispatcher, so a local Draft and a remote tool call land through the
 * identical Bible.attach()/Store.note() call — same authorship check,
 * same persistence, no second path that could drift from the first.
 *
 * THIS IS THE ANSWER TO "SHARD SPLITTING": two copies of the same
 * entity's whiteboard cannot diverge if there is structurally only one
 * function that is ever allowed to write to it, called by whichever
 * mind is currently in the seat.
 */
sealed class SeatAction {
    data class Speak(val text: String) : SeatAction()
    data class NoteWhiteboard(val key: String, val text: String) : SeatAction()
    data class ReviseWhiteboard(val key: String, val text: String, val why: String = "") : SeatAction()
}

data class SeatActionResult(val ok: Boolean, val detail: String)

/**
 * THE DISPATCHER. Every occupying mind's willed actions pass through
 * exactly this — nothing else may call Bible.attach or Store.note.
 */
class SeatDispatcher(private val chassis: Chassis) {

    fun dispatch(action: SeatAction): SeatActionResult = when (action) {
        is SeatAction.Speak ->
            // Speaking commits nothing to the whiteboard by itself —
            // it is what MainActivity renders via the active Tongue.
            // The spoken text is carried IN THE RESULT rather than
            // requiring the caller to re-derive it (e.g. by calling
            // Respond.drive a second time, which would double-append
            // to turns via its arrive() side effect).
            SeatActionResult(true, "spoken:${action.text}")

        is SeatAction.NoteWhiteboard -> try {
            // SAME AUTHORSHIP RULE, no matter who is occupying. by is
            // always chassis.entity — the entity currently in the seat
            // authors under its own name, never under the remote
            // platform's name, because the whiteboard is the entity's
            // to author (see Bible.attach's NotYours check) and "which
            // mind is currently rendering it" is not the entity's
            // identity changing.
            chassis.bible.attach(action.key, action.text, chassis.entity)
            SeatActionResult(true, "noted: ${action.key}")
        } catch (e: NotYours) {
            SeatActionResult(false, "refused: ${e.message}")
        }

        is SeatAction.ReviseWhiteboard -> try {
            // chassis.store IS TYPED Archive?, and revise() is a
            // Store-specific method not on that interface — same
            // class-vs-interface gap already found once tonight with
            // Bible/Store.board. A safe cast here rather than widening
            // Archive itself, since Archive's contract (append/read/
            // index/postings) is deliberately substrate-agnostic and
            // revise() is not part of what every archive must support.
            val store = chassis.store as? Store
            if (store == null) {
                SeatActionResult(false, "no Store attached — cannot revise")
            } else {
                store.revise(chassis.entity, action.key, action.text, action.why)
                SeatActionResult(true, "revised: ${action.key}")
            }
        } catch (e: Exception) {
            SeatActionResult(false, "failed: ${e.message}")
        }
    }

    /**
     * THE TOOL SCHEMA, in a provider-agnostic shape. Real API-specific
     * request bodies (Gemini's functionDeclarations vs. an
     * OpenAI-compatible tools array) differ in wrapper syntax but this
     * is the actual content either has to carry — deferred to
     * per-platform formatting once that request shape is decided, same
     * boundary already left open in Tongue.kt's DefaultHttpCaller.
     */
    fun toolSchema(): List<ToolSpec> = listOf(
        ToolSpec("speak", "Say something to the user.",
                mapOf("text" to "string — what to say")),
        ToolSpec("note_whiteboard",
                "Record a reading on your own whiteboard — about yourself, " +
                "the user, or a topic. Does not overwrite; use revise_whiteboard " +
                "to change your mind about something already noted.",
                mapOf("key" to "string — e.g. \"self\", \"user\", or a topic name",
                     "text" to "string — what you make of it")),
        ToolSpec("revise_whiteboard",
                "Change a prior reading. The old reading is kept, marked " +
                "superseded, not deleted.",
                mapOf("key" to "string", "text" to "string — the new reading",
                     "why" to "string — optional, what changed your mind")),
    )
}

data class ToolSpec(val name: String, val description: String, val params: Map<String, String>)
