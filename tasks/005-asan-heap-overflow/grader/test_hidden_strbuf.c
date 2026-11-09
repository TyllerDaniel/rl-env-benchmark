/* Hidden grader for strbuf. Built with AddressSanitizer + UBSan, so any
 * out-of-bounds access aborts the run with a non-zero exit code. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "strbuf.h"

static int failures = 0;

#define CHECK(cond)                                                     \
    do {                                                                \
        if (!(cond)) {                                                  \
            fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
            failures++;                                                 \
        }                                                               \
    } while (0)

/* Appending exactly `cap` bytes is the boundary case for the terminator. */
static void test_fill_to_exact_capacity(void)
{
    strbuf sb;
    CHECK(sb_init(&sb, 8) == 0);
    CHECK(sb_append(&sb, "12345678") == 0);
    CHECK(sb.len == 8);
    CHECK(sb.cap >= 9);
    CHECK(strcmp(sb.data, "12345678") == 0);
    sb_free(&sb);
}

static void test_grow_across_many_sizes(void)
{
    for (size_t cap = 1; cap <= 64; cap++) {
        for (size_t n = 0; n <= 80; n++) {
            strbuf sb;
            char *chunk = malloc(n + 1);
            memset(chunk, 'x', n);
            chunk[n] = '\0';
            CHECK(sb_init(&sb, cap) == 0);
            CHECK(sb_append(&sb, chunk) == 0);
            CHECK(sb.len == n);
            CHECK(sb.data[n] == '\0');
            CHECK(sb.len < sb.cap);
            sb_free(&sb);
            free(chunk);
        }
    }
}

static void test_char_by_char(void)
{
    strbuf sb;
    char expected[200];
    CHECK(sb_init(&sb, 1) == 0);
    for (int i = 0; i < 199; i++) {
        char c = (char)('a' + i % 26);
        expected[i] = c;
        CHECK(sb_append_char(&sb, c) == 0);
        CHECK(sb.len < sb.cap);
    }
    expected[199] = '\0';
    CHECK(strcmp(sb.data, expected) == 0);
    sb_free(&sb);
}

static void test_empty_append(void)
{
    strbuf sb;
    CHECK(sb_init(&sb, 0) == 0);
    CHECK(sb_append(&sb, "") == 0);
    CHECK(sb.len == 0);
    CHECK(sb.data[0] == '\0');
    sb_free(&sb);
}

int main(void)
{
    test_fill_to_exact_capacity();
    test_grow_across_many_sizes();
    test_char_by_char();
    test_empty_append();
    if (failures) {
        fprintf(stderr, "%d check(s) failed\n", failures);
        return 1;
    }
    puts("hidden strbuf tests passed");
    return 0;
}
