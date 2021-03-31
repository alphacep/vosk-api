package org.vosk;

public enum LogLevel {
    WARNINGS(-1),  // Print warning and errors
    INFO(0),       // Print info, along with warning and error messages, but no debug
    DEBUG(1);      // Print debug info

    private final int value;

    LogLevel(int value) {
        this.value = value;
    }

    public int getValue() {
        return this.value;
    }
}
