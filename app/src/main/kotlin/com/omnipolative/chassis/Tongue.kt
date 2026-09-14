package com.omnipolative.chassis

/**
 * THE TONGUE. What occupies the seat's rendering/reasoning slot.
 * Swappable.
 *
 * LOCAL: comprehend/express/check/register (Respond.kt) does the
 * reasoning; render() only turns an already-decided Draft into text.
 *
 * REMOTE: the occupying model DOES its own comprehension (using the
 * cached dictionary as its reference for our compressed protocol,
 * not the chassis pre-deciding everything into a Draft first) and
 * WILLS actions — speak, note_whiteboard, revise_whiteboard — the
 * same way A.propose() wills Instructions locally. Those actions are
 * dispatched through SeatDispatcher, so a remote-authored whiteboard
 * entry goes through the identical authorship-checked call a local
 * one always has. There is one write path regardless of which mind is
 * occupying the seat.
 */
interface Tongue {
    val id: String
    /** LOCAL PATH: render an already-decided draft; does not re-decide. */
    fun render(chassis: Chassis, draft: Draft): String

    /**
     * REMOTE-CAPABLE PATH: hand the occupying mind the raw message and
     * let it will actions directly, dispatched through the given
     * dispatcher. RuleTongue's default just wraps render() in a single
     * Speak action, so callers can use occupy() uniformly regardless
     * of which tongue is active without special-casing local.
     */
    fun occupy(chassis: Chassis, dispatcher: SeatDispatcher, message: String): List<SeatActionResult> {
        val draft = Respond.drive(chassis, message)
        val text = render(chassis, draft)
        return listOf(dispatcher.dispatch(SeatAction.Speak(text)))
    }
}

/**
 * LOCAL. The existing rule-based responder (Respond.kt), unchanged.
 * Always available — no key, no network, this is the floor the seat
 * never drops below.
 */
class RuleTongue : Tongue {
    override val id = "local:rule"
    // THE ONE LEGITIMATE DECODE for the local path — MainActivity needs
    // English on screen, and this is the single call site producing it.
    override fun render(chassis: Chassis, draft: Draft): String = draft.text(chassis.table)
}

/**
 * REMOTE. Calls out to a platform (Gemini or another) with an API key,
 * to RENDER a Draft the chassis already produced — not to decide what
 * the chassis should say.
 *
 * THE CACHED INSTRUCTIONS ARE THE BOUNDARY, not a comment about one.
 * SYSTEM_INSTRUCTIONS below is sent once as cached content (Gemini's
 * CachedContent resource, or the equivalent on another platform) and
 * is what stops a capable remote model from "helpfully" reasoning on
 * its own — a smaller, cheaper model rendering a decided draft is the
 * design; a larger model quietly re-deciding the conversation is the
 * failure this exists to prevent.
 *
 * WIRE FORMAT: messages are exchanged as our own dense token ids
 * (Table.ids / Table.say), not English strings. The remote side needs
 * the dictionary (words.by_word, words.by_id, table3.btb/.idx — 24 MB
 * total) available as cached reference content to decode/encode
 * against; that is a SEPARATE, platform-specific call (Gemini's
 * CachedContent API differs from a generic system prompt) and is not
 * built here — cachedDictionaryHandle below is where that plugs in
 * once the per-platform caching call is written.
 */
class RemoteTongue(
    private val endpoint: String,
    private val model: String,
    private val apiKey: String,
    /** Handle/id of the platform's cached dictionary resource, once
     *  that upload has been done. Null until then — render() still
     *  works without it, just without the compression benefit. */
    private val cachedDictionaryHandle: String? = null,
    private val http: HttpCaller = DefaultHttpCaller(),
) : Tongue {
    override val id = "remote:$model"

    companion object {
        /**
         * CACHED ONCE, per session/context, not resent per call. States
         * the boundary structurally: render only, our token protocol,
         * ask rather than assume when the draft is ambiguous.
         */
        val SYSTEM_INSTRUCTIONS = """
            You are the RENDERING layer for a local reasoning system
            (a "chassis"). The chassis has ALREADY DECIDED what to say —
            you receive a finished draft, not a question to answer on
            your own initiative.

            YOUR ONLY JOB: render the draft into fluent language, or
            encode/decode it using the attached token dictionary when
            messages arrive in that compressed form. You do not:
              - add reasoning, opinions, or facts the draft did not
                contain
              - decide what the response SHOULD be
              - answer the user's original question independently

            If the draft is genuinely unrenderable (contradictory,
            empty, malformed), say so plainly rather than substituting
            your own answer. Rendering, not deciding.
        """.trimIndent()
    }

    override fun render(chassis: Chassis, draft: Draft): String {
        // DRAFT ALREADY HOLDS IDS — no re-encode needed, which was the
        // redundant step here before draft.ids existed directly.
        val payload = RemotePayload(
            systemCached = cachedDictionaryHandle,
            instructions = SYSTEM_INSTRUCTIONS,
            draftTokenIds = draft.ids.toList(),
            draftSource = draft.source,
        )
        val responseIds = http.call(endpoint, model, apiKey, payload)
        // Decode the response back through the SAME dictionary — if the
        // remote side has no cached dictionary yet, it is expected to
        // echo/render in plain text and responseIds will be empty;
        // fall back to the drafted English in that case.
        return if (responseIds.tokenIds.isNotEmpty())
            chassis.table.say(responseIds.tokenIds.toIntArray())
        else responseIds.text ?: draft.text(chassis.table)
    }

    /**
     * THE REAL REMOTE PATH. The occupying model does its OWN
     * comprehension — using the cached dictionary as its reference,
     * not a Draft the chassis pre-decided — and wills actions back,
     * which are dispatched exactly the way a local Instruction would
     * be. This is what makes "switch to remote" mean occupying the
     * seat's reasoning, not just its phrasing.
     *
     * NOT WIRED TO A LIVE CALL YET (DefaultHttpCaller still throws) —
     * the tool-call request/response shape is real and specified here;
     * only the platform-specific HTTP body (Gemini's functionCall
     * response format vs. an OpenAI-compatible one) is deferred, same
     * boundary as render()'s cachedDictionaryHandle.
     */
    override fun occupy(chassis: Chassis, dispatcher: SeatDispatcher, message: String): List<SeatActionResult> {
        val ids = chassis.table.ids(message)
        val payload = RemotePayload(
            systemCached = cachedDictionaryHandle,
            instructions = SYSTEM_INSTRUCTIONS,
            draftTokenIds = ids.toList(),
            draftSource = "remote:occupying",
        )
        val willed = http.callWithTools(endpoint, model, apiKey, payload, dispatcher.toolSchema())
        // EVERY WILLED ACTION GOES THROUGH THE SAME DISPATCHER a local
        // reasoner's writes go through — no separate remote write path
        // exists, which is the actual fix for two copies of the same
        // entity's whiteboard drifting apart.
        return willed.map { dispatcher.dispatch(it) }
    }
}

data class RemotePayload(
    val systemCached: String?,
    val instructions: String,
    val draftTokenIds: List<Int>,
    val draftSource: String,
)

data class RemoteResult(val tokenIds: List<Int> = emptyList(), val text: String? = null)

/** Thin seam so RemoteTongue is testable without a live network call. */
interface HttpCaller {
    fun call(endpoint: String, model: String, apiKey: String, payload: RemotePayload): RemoteResult

    /**
     * TOOL-CALLING PATH. The occupying model is given `tools` (a
     * provider-agnostic ToolSpec list — see SeatDispatcher.toolSchema)
     * and returns the SeatActions it wills, rather than plain text.
     * Real providers differ in exact request/response shape (Gemini's
     * functionCall vs. an OpenAI-compatible tool_calls array); that
     * translation is exactly what implementing this method IS, once a
     * platform is chosen.
     */
    fun callWithTools(endpoint: String, model: String, apiKey: String,
                      payload: RemotePayload, tools: List<ToolSpec>): List<SeatAction>
}

class DefaultHttpCaller : HttpCaller {
    override fun call(endpoint: String, model: String, apiKey: String, payload: RemotePayload): RemoteResult {
        // NOT IMPLEMENTED HERE ON PURPOSE. The exact request shape
        // (Gemini's generateContent + cachedContent vs. an
        // OpenAI-compatible chat/completions body) is platform-specific
        // and was explicitly deferred until the per-platform caching
        // call is written — building a fake one would hide that gap
        // instead of leaving it visible.
        throw NotImplementedError(
            "DefaultHttpCaller.call: wire this to $endpoint once the " +
            "platform-specific cached-content request shape is decided.")
    }

    override fun callWithTools(endpoint: String, model: String, apiKey: String,
                               payload: RemotePayload, tools: List<ToolSpec>): List<SeatAction> {
        // SAME BOUNDARY AS call() ABOVE. The dispatcher, the schema,
        // and the willed-action shape are all real and specified
        // (SeatDispatcher.kt); only the actual outbound HTTP request
        // to a specific platform's function-calling API is deferred.
        throw NotImplementedError(
            "DefaultHttpCaller.callWithTools: wire this to $endpoint's " +
            "function-calling API once the platform is chosen.")
    }
}
