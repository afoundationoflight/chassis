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
/**
 * WHAT ACTUALLY GOES IN THE CACHE, MEASURED CORRECTLY THE SECOND TIME.
 *
 * The first version of this file called Table.say() on every gloss —
 * which fully DECOMPRESSES token ids back into space-separated English
 * words — before measuring the result. That produced 22 MB of
 * expanded prose and an estimated 5.5M tokens, the opposite of what a
 * compressed cache payload should be. The dictionary was never that
 * large; the measurement was wrong.
 *
 * THE ACTUAL FORMAT, as specified: one word<->id table (English
 * equivalents, written once, not per definition) plus a pos/gloss
 * column and a definitions column written IN TOKEN SYMBOLS — ids, not
 * expanded English — with a crawler-style reader that consumes ids
 * directly rather than extracting/decompressing them first. This
 * version keeps glosses as raw id sequences and reports id counts, not
 * decompressed character counts, which is the honest measure of what
 * a token-symbol cache payload actually contains.
 */
object CacheSizer {

    data class Measurement(
        val entries: Int,
        /** Distinct word<->id table entries — written ONCE, not per gloss. */
        val vocabularySize: Int,
        /** Total token ids across every gloss, still compressed form. */
        val glossTokenIds: Long,
        val estimatedTokens: Long,
        val clearsMinimum: Boolean,
    )

    private const val CACHE_MINIMUM_TOKENS = 32_768L
    // A token id (e.g. "482") is not one model-token; conservatively
    // budget ~1.3 model-tokens per id (integers are usually 1, longer
    // ids occasionally split) rather than assume 1:1.
    private const val ESTIMATED_TOKENS_PER_ID = 1.3

    /**
     * Build the cache payload in the SPECIFIED shape:
     *   [vocabulary]  word<TAB>id, one line per word, written once
     *   [glosses]     wordId<TAB>posId<TAB>id,id,id...  — TOKEN IDS, not English
     *
     * Nothing here calls table.say() — that is the decompression step,
     * and doing it before caching defeats the entire point of shipping
     * a compressed representation to the remote side.
     */
    fun serializeDictionary(table: Table): Pair<String, Measurement> {
        val vocab = StringBuilder()
        val glosses = StringBuilder()
        var vocabCount = 0
        var glossIdCount = 0L
        var i = 1  // word id 0 is "not found" per Table.word()
        val n = table.size()
        while (i <= n) {
            val w = table.word(i)
            if (w != "?") {
                vocab.append(w).append('\t').append(i).append('\n')
                vocabCount++
                val senses = table.mean(w)
                for (sense in senses) {
                    // RAW IDS, comma-joined — the compressed form, the
                    // same representation Crawler.mean() already
                    // returns. Nothing is expanded to English here.
                    glosses.append(i).append('\t')
                        .append(sense.joinToString(",")).append('\n')
                    glossIdCount += sense.size
                }
            }
            i++
        }
        val content = "[vocabulary]\n$vocab[glosses]\n$glosses"
        val estTokens = ((vocabCount + glossIdCount) * ESTIMATED_TOKENS_PER_ID).toLong()
        val m = Measurement(
            entries = vocabCount,
            vocabularySize = vocabCount,
            glossTokenIds = glossIdCount,
            estimatedTokens = estTokens,
            clearsMinimum = estTokens >= CACHE_MINIMUM_TOKENS,
        )
        return content to m
    }

    /**
     * The real decision. Dictionary first; if it alone does not clear
     * the minimum, curriculum/grammar source is APPENDED (not
     * substituted) until it does, or until there is nothing left to
     * add.
     */
    fun buildCacheContent(table: Table, curriculumSource: String? = null,
                         grammarSource: String? = null): Pair<String, Measurement> {
        var (content, m) = serializeDictionary(table)
        if (!m.clearsMinimum && grammarSource != null) {
            content += "\n[grammar]\n" + grammarSource
            val extra = (grammarSource.length / 4.0).toLong()
            m = m.copy(estimatedTokens = m.estimatedTokens + extra,
                      clearsMinimum = m.estimatedTokens + extra >= CACHE_MINIMUM_TOKENS)
        }
        if (!m.clearsMinimum && curriculumSource != null) {
            content += "\n[curriculum]\n" + curriculumSource
            val extra = (curriculumSource.length / 4.0).toLong()
            m = m.copy(estimatedTokens = m.estimatedTokens + extra,
                      clearsMinimum = m.estimatedTokens + extra >= CACHE_MINIMUM_TOKENS)
        }
        return content to m
    }
}
