#include "cleaner.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>   // for getcwd

/* Check if a directory contains only .pyc files */
static bool all_pyc(char* dir) {
    if (dir == NULL) {
        return false;
    }

    DIR* d = opendir(dir);
    if (!d) return false;

    struct dirent* entry;
    bool only_pyc = true;
    while ((entry = readdir(d)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 ||
            strcmp(entry->d_name, "..") == 0) {
            continue;
        }
        size_t len = strlen(entry->d_name);
        if (len < 4 || strcmp(entry->d_name + len - 4, ".pyc") != 0) {
            only_pyc = false;
            break;
        }
    }
    closedir(d);
    return only_pyc;
}

/* Count '/' characters in a path */
static int all_dir_in_dit(char* dir) {
    if (dir == NULL) {
        return 0;
    }
    int count = 0;
    for (size_t i = 0; i < strlen(dir); i++) {
        if (dir[i] == '/') {
            count++;
        }
    }
    return count;
}

/* Return parent directory of `dir` (newly allocated string) */
static char* get_absolute_path_of_dir_in_dir(char* dir) {
    if (dir == NULL) {
        return NULL;
    }

    size_t len = strlen(dir);

    /* Walk backwards to find last '/' */
    for (size_t j = len; j > 0; j--) {
        if (dir[j - 1] == '/') {
            size_t parent_len = j - 1;
            if (parent_len == 0) parent_len = 1;  // root "/"

            char* parent = malloc(parent_len + 1);
            if (!parent) return NULL;

            strncpy(parent, dir, parent_len);
            parent[parent_len] = '\0';
            return parent;
        }
    }

    /* No '/' found — return current directory */
    char* cwd = malloc(1024);
    if (cwd && getcwd(cwd, 1024) == NULL) {
        free(cwd);
        return NULL;
    }
    return cwd;
}

bool clean_pyc_files(char* dir) {
    if (dir == NULL) {
        return false;
    }

    DIR* d = opendir(dir);
    if (!d) return false;

    struct dirent* entry;
    while ((entry = readdir(d)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 ||
            strcmp(entry->d_name, "..") == 0) {
            continue;
        }

        char path[1024];
        snprintf(path, sizeof(path), "%s/%s", dir, entry->d_name);

        if (entry->d_type == DT_DIR) {
            clean_pyc_files(path);
        } else if (entry->d_type == DT_REG) {
            size_t len = strlen(entry->d_name);
            if (len >= 4 && strcmp(entry->d_name + len - 4, ".pyc") == 0) {
                remove(path);
            }
        }
    }
    closedir(d);
    return true;
}
