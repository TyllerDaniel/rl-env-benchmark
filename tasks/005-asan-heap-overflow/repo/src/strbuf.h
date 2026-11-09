#ifndef STRBUF_H
#define STRBUF_H

#include <stddef.h>

/* A growable, always NUL-terminated string buffer. */
typedef struct {
    char *data;
    size_t len; /* bytes used, not counting the terminator */
    size_t cap; /* bytes allocated */
} strbuf;

/* Returns 0 on success, -1 on allocation failure. */
int sb_init(strbuf *sb, size_t initial_cap);
int sb_append(strbuf *sb, const char *s);
int sb_append_char(strbuf *sb, char c);
void sb_free(strbuf *sb);

#endif
