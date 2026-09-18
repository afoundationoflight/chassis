plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    // PYTHON IS THE CHASSIS. Kotlin is the shell around it.
    //
    // Two implementations had diverged — the Kotlin side had a Room and
    // a Tongue the Python did not, the Python side had permanence,
    // habituation, the curriculum loader and the update path the Kotlin
    // did not. Every fix was going to have to be made twice, and they
    // would keep drifting.
    //
    // Chaquopy embeds CPython, so infinity_core_v9.py runs unmodified
    // as an asset. Free and open source since 12.0.1 — no key, no time
    // limit, published on Maven Central.
    id("com.chaquo.python")
}

android {
    namespace = "com.omnipolative.chassis"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.omnipolative.chassis"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "9.0"

        // arm64 covers the large majority of modern devices; x86_64 is
        // here so the emulator works for anyone developing on a laptop.
        ndk { abiFilters += listOf("arm64-v8a", "x86_64") }

        // NO python { } BLOCK. In the Kotlin DSL that extension is not
        // resolvable inside defaultConfig, and this build does not need
        // it: the bundle installs nothing from pip. Its whole point is
        // being self-contained — 165 modules in one file, with the
        // language as a brotli asset beside it. Chaquopy picks up
        // app/src/main/python/ on its own.
    }

    sourceSets["main"].kotlin.srcDirs("src/main/kotlin")

    // THE STORES SHIP COMPRESSED, AND THAT COSTS NOTHING.
    //
    // I had noCompress here on the reasoning that a compressed asset
    // has to be inflated before it can be mapped. True, and irrelevant:
    // assets inside an apk CANNOT be mmapped at all — AssetManager
    // hands you a stream, not an address — so the activity copies them
    // to filesDir on first launch either way. The inflate rides along
    // with a copy that was already happening.
    //
    // 32.7 MB uncompressed against 14.8 MB compressed, same end state,
    // and the download is half. Keeping them raw bought nothing and
    // cost 18 MB.

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    testOptions {
        unitTests {
            isIncludeAndroidResources = true
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    // Keystore-backed encrypted storage for the remote tongue's model
    // name + API key — not the plaintext board SQLite table.
    implementation("androidx.security:security-crypto:1.1.0-alpha06")

    // ROBOLECTRIC. This container has no Android runtime and no device,
    // so "verified from the pilot seat" was going to mean either faking
    // it or actually driving the real SQLite/Context path somewhere a
    // real Android runtime exists. Robolectric gives that on the JVM,
    // in CI — real SQLiteOpenHelper behavior, not a mock returning
    // whatever I decided it should.
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.robolectric:robolectric:4.13")
    testImplementation("androidx.test:core:1.6.1")
}
