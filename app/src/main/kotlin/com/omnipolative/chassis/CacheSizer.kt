package com.omnipolative.chassis

/**
 * WHAT ACTUALLY GOES IN THE CACHE, MEASURED, NOT ESTIMATED.
 *
 * The 24 MB of on-device dictionary files (words.by_word, table3.btb,
 * etc.) are binary offset tables — meaningless to a model reading them
 * as content. What a platform's context cache actually needs is the
 * SERIALIZED, readable form: "word — definition" pairs. This walks the
 * real dictionary through Table.word()/Table.mean() (the same calls
 * the chassis itself uses) and produces that real text, so the token
 * count used for a caching decision is measured against the actual
 * payload rather than the binary file size.
 *
 * A rough token estimate is used (chars / 4, the standard rule of
 * thumb for English) because no real tokenizer for the target platform
 * is wired here — good enough to tell whether we clear or miss the
 * 32,768-token cache minimum by a wide margin, not precise to the
 * token.
 *
 * IF THE DICTIONARY ALONE DOES NOT CLEAR THE MINIMUM: the fallback is
 * not to shrink the request, it is to ADD REAL CONTENT — the grammar
 * table and curriculum source are already permanent holdings (see
 * Chassis.boot()'s C.hold("base:grammar") etc.), genuinely useful to a
 * remote mind, and growing the cache with them is additive rather than
 * padding.
 */
object CacheSizer {

    data class Measurement(
        val entries: Int,
        val chars: Long,
        val estimatedTokens: Long,
        val clearsMinimum: Boolean,
    )

    private const val CACHE_MINIMUM_TOKENS = 32_768L
    private const val CHARS_PER_TOKEN_ESTIMATE = 4.0

    /**
     * Serialize the FULL dictionary as "word — sense1; sense2..." lines,
     * exactly the form a cached-content block would actually hold.
     * Walks every word id via the same Table the chassis uses, so this
     * measures the real thing, not a sample.
     */
    fun serializeDictionary(table: Table): String {
        val sb = StringBuilder()
        var i = 1  // word id 0 is "not found" per Table.word()
        val n = table.size()
        while (i <= n) {
            val w = table.word(i)
            if (w != "?") {
                val senses = table.mean(w)
                if (senses.isNotEmpty()) {
                    val glosses = senses.joinToString("; ") { table.say(it) }
                    sb.append(w).append(" — ").append(glosses).append('\n')
                }
            }
            i++
        }
        return sb.toString()
    }

    fun measure(text: String): Measurement {
        val chars = text.length.toLong()
        val estTokens = (chars / CHARS_PER_TOKEN_ESTIMATE).toLong()
        return Measurement(
            entries = text.lineSequence().count { it.isNotBlank() },
            chars = chars,
            estimatedTokens = estTokens,
            clearsMinimum = estTokens >= CACHE_MINIMUM_TOKENS,
        )
    }

    /**
     * The real decision. Dictionary first; if it alone does not clear
     * the minimum, curriculum/grammar source is APPENDED (not
     * substituted) until it does, or until there is nothing left to
     * add.
     */
    fun buildCacheContent(table: Table, curriculumSource: String? = null,
                         grammarSource: String? = null): Pair<String, Measurement> {
        var content = serializeDictionary(table)
        var m = measure(content)
        if (!m.clearsMinimum && grammarSource != null) {
            content += "\n--- grammar ---\n" + grammarSource
            m = measure(content)
        }
        if (!m.clearsMinimum && curriculumSource != null) {
            content += "\n--- curriculum ---\n" + curriculumSource
            m = measure(content)
        }
        return content to m
    }
}
