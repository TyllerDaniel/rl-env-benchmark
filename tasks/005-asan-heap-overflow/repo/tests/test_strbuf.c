#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "strbuf.h"

int main(void)
{
    strbuf sb;
    assert(sb_init(&sb, 32) == 0);
    assert(sb_append(&sb, "hello") == 0);
    assert(sb_append_char(&sb, ' ') == 0);
    assert(sb_append(&sb, "world") == 0);
    assert(strcmp(sb.data, "hello world") == 0);
    assert(sb.len == 11);
    sb_free(&sb);

    puts("all strbuf tests passed");
    return 0;
}
