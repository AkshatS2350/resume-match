# 0003 — PII overlap resolution

Status: accepted

RM-PRIV-002 c1 resolves every directly or transitively overlapping removal-subject PII detection as one connected group. The resolved span covers the complete range union. Its category is selected by highest confidence, then lexicographically ascending category identifier, lower start offset, and greater end offset.

This deliberately permits bounded over-redaction so that no detected PII tail can survive overlap resolution. Resolved output spans are pairwise non-overlapping and every detected removal character is covered exactly once.
