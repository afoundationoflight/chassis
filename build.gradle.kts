plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    // Free and open source since 12.0.1, published on Maven Central —
    // no license key and no runtime limit.
    // Chaquopy's checkAgpVersion calls org.gradle.util.VersionNumber,
    // which Gradle 9.0 removed — so the build must run on Gradle 8.
    // The workflow pins 8.9 through the wrapper; that is the fix, and
    // pinning an older Chaquopy on top of it would just be a guess at
    // which release stopped using the class.
    id("com.chaquo.python") version "16.0.0" apply false
}
