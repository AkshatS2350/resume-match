# Canonical text normalization

Extraction applies these steps in order: NFKC; the fixed ligature expansion table; five space-like code points to ordinary spaces; U+2010 through U+2015 to `-`; curly quotes to straight quotes; CRLF/CR to LF; collapse two or more spaces; strip trailing spaces per line; collapse three or more newlines to two.
