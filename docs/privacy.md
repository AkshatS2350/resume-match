# Candidate-data lifecycle

1. Upload bytes live only in the request handler and are discarded after extraction.
2. Extracted text lives only in the process-memory `SessionStore` for its TTL.
3. Structured and corrected profile data live only in that same in-memory session.
4. Sanitization runs in `privacy.sanitizer`; failures persist nothing and transmit nothing.
5. A sanitized profile and its record remain only in the in-memory session.
6. Only `llm.gateway` may transmit an exact approved sanitized projection after consent.
7. Session deletion or expiry removes all candidate state; `test_no_candidate_data_in_persistent_writes` verifies no persistent candidate write path.
