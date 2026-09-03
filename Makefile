CC ?= gcc
CFLAGS ?= -std=c99 -O2 -Wall -Wextra -Wno-unused-parameter -pedantic -D_DEFAULT_SOURCE
SRCDIR = engine_src
BINDIR = bin
TARGET = $(BINDIR)/bypass-engine

SOURCES = $(SRCDIR)/packets.c \
          $(SRCDIR)/main.c \
          $(SRCDIR)/conev.c \
          $(SRCDIR)/proxy.c \
          $(SRCDIR)/desync.c \
          $(SRCDIR)/mpool.c \
          $(SRCDIR)/extend.c

all: $(TARGET)

$(TARGET): $(SOURCES)
	@mkdir -p $(BINDIR)
	$(CC) $(CFLAGS) -I$(SRCDIR) -o $(TARGET) $(SOURCES)

clean:
	rm -f $(TARGET)

.PHONY: all clean
