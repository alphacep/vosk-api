# JNA rules - required for Vosk to work with R8/ProGuard minification
-keep class com.sun.jna.** { *; }
-keepclassmembers class * extends com.sun.jna.** { public *; }
-dontwarn java.awt.**
