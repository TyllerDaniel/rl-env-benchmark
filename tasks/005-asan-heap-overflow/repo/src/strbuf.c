#include "strbuf.h"

#include <stdlib.h>
#include <string.h>

int sb_init(strbuf *sb, size_t initial_cap)
{
    if (initial_cap == 0)
        initial_cap = 16;
    sb->data = malloc(initial_cap);
    if (!sb->data)
        return -1;
    sb->data[0] = '\0';
    sb->len = 0;
    sb->cap = initial_cap;
    return 0;
}

/* Make sure at least `needed` bytes are allocated. */
static int sb_reserve(strbuf *sb, size_t needed)
{
    if (needed <= sb->cap)
        return 0;
    size_t new_cap = sb->cap * 2;
    while (new_cap < needed)
        new_cap *= 2;
    char *grown = realloc(sb->data, new_cap);
    if (!grown)
        return -1;
    sb->data = grown;
    sb->cap = new_cap;
    return 0;
}

int sb_append(strbuf *sb, const char *s)
{
    size_t n = strlen(s);
    if (sb_reserve(sb, sb->len + n) != 0)
        return -1;
    memcpy(sb->data + sb->len, s, n);
    sb->len += n;
    sb->data[sb->len] = '\0';
    return 0;
}

int sb_append_char(strbuf *sb, char c)
{
    char tmp[2] = {c, '\0'};
    return sb_append(sb, tmp);
}

void sb_free(strbuf *sb)
{
    free(sb->data);
    sb->data = NULL;
    sb->len = 0;
    sb->cap = 0;
}
