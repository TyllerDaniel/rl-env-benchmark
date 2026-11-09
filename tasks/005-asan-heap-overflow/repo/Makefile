CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -O1 -g
ASAN_FLAGS = -fsanitize=address,undefined -fno-omit-frame-pointer

.PHONY: test asan clean

build/test_strbuf: src/strbuf.c tests/test_strbuf.c src/strbuf.h
	mkdir -p build
	$(CC) $(CFLAGS) -Isrc src/strbuf.c tests/test_strbuf.c -o $@

build/test_strbuf_asan: src/strbuf.c tests/test_strbuf.c src/strbuf.h
	mkdir -p build
	$(CC) $(CFLAGS) $(ASAN_FLAGS) -Isrc src/strbuf.c tests/test_strbuf.c -o $@

test: build/test_strbuf
	./build/test_strbuf

asan: build/test_strbuf_asan
	ASAN_OPTIONS=detect_leaks=0 ./build/test_strbuf_asan

clean:
	rm -rf build
