#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>  // Added for bool type

// Detect platform
#if defined(_WIN32) || defined(_WIN64)
    #define PLATFORM_WINDOWS
#elif defined(__APPLE__)
    #define PLATFORM_MACOS
#elif defined(__linux__)
    #define PLATFORM_LINUX
#else
    #error "Unsupported platform"
#endif

// ==================== Common ====================
static bool is_requirements_file_present() {
    FILE *file = fopen("requirements.txt", "r");
    if (file) {
        fclose(file);
        return true;
    }
    return false;
}

// ==================== Linux / macOS ====================
#if defined(PLATFORM_LINUX) || defined(PLATFORM_MACOS)

static bool is_python_installed() {
    int status = system("python3 --version");
    return (status != -1);
}

static bool is_virtualenv_installed() {
    int status = system("python3 -m venv --help");
    return (status != -1);
}

static bool is_pip_installed() {
    int status = system("pip3 --version");
    return (status != -1);
}

static bool is_virtualenv_created() {
    FILE *file = fopen("venv/bin/activate", "r");
    if (file) {
        fclose(file);
        return true;
    }
    return false;
}

bool create_virtualenv() {
    if (!is_python_installed()) {
        fprintf(stderr, "Python is not installed.\n");
        return false;
    }
    if (!is_virtualenv_installed()) {
        fprintf(stderr, "Virtualenv is not installed.\n");
        return false;
    }
    int status = system("python3 -m venv venv");
    if (status == -1) {
        perror("system() failed to create virtual environment");
        return false;
    }
    return true;
}

bool update_requirements() {
    if (!is_python_installed()) {
        fprintf(stderr, "Python is not installed.\n");
        return false;
    }
    if (!is_virtualenv_installed()) {
        fprintf(stderr, "Virtualenv is not installed.\n");
        return false;
    }
    if (!is_pip_installed()) {
        fprintf(stderr, "Pip is not installed.\n");
        return false;
    }
    if (!is_requirements_file_present()) {
        fprintf(stderr, "requirements.txt file is not present.\n");
        return false;
    }
    if (!is_virtualenv_created()) {
        fprintf(stderr, "Virtual environment is not created.\n");
        return false;
    }
    // Use the venv's pip directly — "source activate" doesn't persist across system() calls
    int status = system("venv/bin/pip install -r requirements.txt");
    if (status == -1) {
        perror("system() failed to update requirements");
        return false;
    }
    return true;
}

bool activate_virtualenv() {
    if (!is_virtualenv_created()) {
        fprintf(stderr, "Virtual environment is not created.\n");
        return false;
    }
    // NOTE: You cannot persist activation across system() calls in C.
    // This only prints the instruction to the user.
    printf("To activate the virtual environment, run:\n");
    printf("    source venv/bin/activate\n");
    return true;
}

// ==================== Windows ====================
#elif defined(PLATFORM_WINDOWS)

static bool is_python_installed_windows() {
    int status = system("python --version");
    return (status != -1);
}

static bool is_virtualenv_installed_windows() {
    int status = system("python -m venv --help");
    return (status != -1);
}

static bool is_pip_installed_windows() {
    int status = system("pip --version");
    return (status != -1);
}

static bool is_virtualenv_created_windows() {
    FILE *file = fopen("venv/Scripts/activate", "r");
    if (file) {
        fclose(file);
        return true;
    }
    return false;
}

bool create_virtualenv_windows() {
    if (!is_python_installed_windows()) {
        fprintf(stderr, "Python is not installed.\n");
        return false;
    }
    if (!is_virtualenv_installed_windows()) {
        fprintf(stderr, "Virtualenv is not installed.\n");
        return false;
    }
    int status = system("python -m venv venv");
    if (status == -1) {
        perror("system() failed to create virtual environment");
        return false;
    }
    return true;
}

bool update_requirements_windows() {
    if (!is_python_installed_windows()) {
        fprintf(stderr, "Python is not installed.\n");
        return false;
    }
    if (!is_virtualenv_installed_windows()) {
        fprintf(stderr, "Virtualenv is not installed.\n");
        return false;
    }
    if (!is_pip_installed_windows()) {
        fprintf(stderr, "Pip is not installed.\n");
        return false;
    }
    if (!is_requirements_file_present()) {
        fprintf(stderr, "requirements.txt file is not present.\n");
        return false;
    }
    if (!is_virtualenv_created_windows()) {
        fprintf(stderr, "Virtual environment is not created.\n");
        return false;
    }
    // Use the venv's pip directly — activation doesn't persist across system() calls
    int status = system("venv\\Scripts\\pip.exe install -r requirements.txt");
    if (status == -1) {
        perror("system() failed to update requirements");
        return false;
    }
    return true;
}

bool activate_virtualenv_windows() {
    if (!is_virtualenv_created_windows()) {
        fprintf(stderr, "Virtual environment is not created.\n");
        return false;
    }
    printf("To activate the virtual environment, run:\n");
    printf("    venv\\Scripts\\activate\n");
    return true;
}

#endif

// ==================== Main ====================
int main(void) {
    printf("Setting up Python virtual environment...\n\n");

#if defined(PLATFORM_LINUX) || defined(PLATFORM_MACOS)
    if (!create_virtualenv()) {
        fprintf(stderr, "Failed to create virtual environment.\n");
        return EXIT_FAILURE;
    }
    if (!update_requirements()) {
        fprintf(stderr, "Failed to update requirements.\n");
        return EXIT_FAILURE;
    }
    if (!activate_virtualenv()) {
        fprintf(stderr, "Failed to activate virtual environment.\n");
        return EXIT_FAILURE;
    }
#elif defined(PLATFORM_WINDOWS)
    if (!create_virtualenv_windows()) {
        fprintf(stderr, "Failed to create virtual environment.\n");
        return EXIT_FAILURE;
    }
    if (!update_requirements_windows()) {
        fprintf(stderr, "Failed to update requirements.\n");
        return EXIT_FAILURE;
    }
    if (!activate_virtualenv_windows()) {
        fprintf(stderr, "Failed to activate virtual environment.\n");
        return EXIT_FAILURE;
    }
#endif

    printf("\nSetup completed successfully!\n");
    return EXIT_SUCCESS;
}