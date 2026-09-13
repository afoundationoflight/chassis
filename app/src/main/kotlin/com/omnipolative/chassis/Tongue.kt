package com.omnipolative.chassis

/**
 * THE TONGUE. What renders A's output. Swappable, not the reasoner.
 *
 * The chassis (comprehend -> express -> check -> register) DOES THE
 * REASONING. A Tongue's only job is turning what was already decided
 * into language — or, for a remote tongue, into OUR compressed token
 * protocol and back. A tongue that free-forms its own response instead
 * of rendering the Draft it was handed is not a tongue anymore, it is
 * a second reasoner the chassis did not ask for.
 *
 * This is the same rule as core/attachment.py's Bible: authority is
 * scoped to exactly one job, and the interface makes the other jobs
 * unreachable rather than merely discouraged.
 */
interface Tongue {
    val id: String
    /** Render an ALREADY-DECIDED draft. Does not re-decide what to say. */
    fun render(chassis: Chassis, draft: Draft): String
}

/**
 * LOCAL. The existing rule-based responder (Respond.kt), unchanged.
 * Always available — no key, no network, this is the floor the seat
 * never drops below.
 */
class RuleTongue : Tongue {
    override val id = "local:rule"
    override fun render(chassis: Chassis, draft: Draft): String = draft.text
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
        // TOKEN IDS, NOT ENGLISH — this is the compressed protocol the
        // dictionary caching exists to make cheap. table.ids/table.say
        // are the only place English becomes/leaves ids (see Root in
        // Chassis.kt); this reuses that seam rather than inventing a
        // second one.
        val ids = chassis.table.ids(draft.text)
        val payload = RemotePayload(
            systemCached = cachedDictionaryHandle,
            instructions = SYSTEM_INSTRUCTIONS,
            draftTokenIds = ids.toList(),
            draftSource = draft.source,
        )
        val responseIds = http.call(endpoint, model, apiKey, payload)
        // Decode the response back through the SAME dictionary — if the
        // remote side has no cached dictionary yet, it is expected to
        // echo/render in plain text and responseIds will be empty;
        // fall back to the rendered text field in that case.
        return if (responseIds.tokenIds.isNotEmpty())
            chassis.table.say(responseIds.tokenIds.toIntArray())
        else responseIds.text ?: draft.text
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
}
