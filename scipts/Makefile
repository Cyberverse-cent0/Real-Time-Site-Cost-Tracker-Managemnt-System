# ============================================================
#  Makefile — C project build
#  Supports: Linux, macOS
#  Auto-detects: gcc / clang
#  Features: out-of-tree build, header dep tracking, colors
# ============================================================

# ---------- Config ----------
TARGET      := app
SRC_DIR     := src
BUILD_DIR   := build
OBJS_DIR    := $(BUILD_DIR)/objs
DEPS_DIR    := $(BUILD_DIR)/deps

CFLAGS      := -Wall -Wextra -O2f
LDFLAGS     :=
LDLIBS      :=

# ---------- Colors ----------
C_RESET  := \033[0m
C_GREEN  := \033[32m
C_YELLOW := \033[33m
C_RED    := \033[31m
C_BLUE   := \033[34m

# ---------- Platform detection ----------
UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Linux)
    PLATFORM := LINUX
else ifeq ($(UNAME_S),Darwin)
    PLATFORM := MACOS
else
    $(error Unsupported OS '$(UNAME_S)'. This Makefile supports Linux and macOS only.)
endif

# ---------- Root check (informational) ----------
ifeq ($(shell whoami),root)
    $(info $(C_YELLOW)Note: running as root$(C_RESET))
endif

# ---------- Compiler detection ----------
# If the user (or make's default) provides CC, respect it.
# Otherwise auto-detect gcc, then clang.
ifeq ($(origin CC),default)
    CC := $(shell command -v gcc 2>/dev/null)
endif
ifeq ($(CC),)
    CC := $(shell command -v clang 2>/dev/null)
endif
ifeq ($(CC),)
    $(error Neither gcc nor clang is installed. Please install one to proceed.)
endif

# ---------- Platform-specific flags ----------
ifeq ($(PLATFORM),LINUX)
    CFLAGS  += -D_GNU_SOURCE
    LDLIBS  += -lpthread
endif
ifeq ($(PLATFORM),MACOS)
    CFLAGS  += -D_DARWIN_C_SOURCE
endif

# ---------- Sources / objects ----------
SRCS    := $(wildcard $(SRC_DIR)/*.c)
OBJS    := $(patsubst $(SRC_DIR)/%.c,$(OBJS_DIR)/%.o,$(SRCS))
DEPS    := $(patsubst $(SRC_DIR)/%.c,$(DEPS_DIR)/%.d,$(SRCS))
TARGET  := $(BUILD_DIR)/$(TARGET)

# ---------- Header dependency tracking ----------
# -MMD -MP writes .d files next to .o; we redirect them to DEPS_DIR.
DEPFLAGS := -MMD -MP -MF $(DEPS_DIR)/$*.d

# ---------- Rules ----------
.PHONY: all build run clean rebuild info help

all: build

build: $(TARGET)

$(TARGET): $(OBJS)
	@mkdir -p $(dir $@)
	@echo "$(C_BLUE)[LD]$(C_RESET)  $@"
	@$(CC) $(OBJS) $(LDFLAGS) $(LDLIBS) -o $@
	@echo "$(C_GREEN)✔ Build complete: $@$(C_RESET)"

$(OBJS_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(OBJS_DIR) $(DEPS_DIR)
	@echo "$(C_BLUE)[CC]$(C_RESET)  $<"
	@$(CC) $(CFLAGS) $(DEPFLAGS) -c $< -o $@

# Pull in generated dependency files (if they exist)
-include $(DEPS)

# ---------- Convenience targets ----------
run: build
	@echo "$(C_BLUE)[RUN]$(C_RESET) $(TARGET)"
	@./$(TARGET)

clean:
	@rm -rf $(BUILD_DIR)
	@echo "$(C_GREEN)✔ Cleaned$(C_RESET)"

rebuild: clean build

info:
	@echo "Platform:  $(PLATFORM) ($(UNAME_S))"
	@echo "Compiler:  $(CC)"
	@echo "CFLAGS:    $(CFLAGS)"
	@echo "LDFLAGS:   $(LDFLAGS)"
	@echo "LDLIBS:    $(LDLIBS)"
	@echo "SRCS:      $(SRCS)"
	@echo "OBJS:      $(OBJS)"
	@echo "DEPS:      $(DEPS)"
	@echo "TARGET:    $(TARGET)"

help:
	@echo "Targets:"
	@echo "  make            Build the project (default)"
	@echo "  make build      Same as default"
	@echo "  make run        Build and run"
	@echo "  make clean      Remove build artifacts"
	@echo "  make rebuild    clean + build"
	@echo "  make info       Show resolved config"
	@echo "  make help       Show this help"