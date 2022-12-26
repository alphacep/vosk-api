plugins {
	kotlin("multiplatform") version "1.7.21"
	id("com.android.library")
}

group = "org.vosk"
version = "0.0.0"

repositories {
	google()
	mavenCentral()
}

kotlin {
	jvm {
		compilations.all {
			kotlinOptions.jvmTarget = "17"
		}
		testRuns["test"].executionTask.configure {
			useJUnitPlatform()
		}
	}
	mingwX64 {
		binaries {
			executable {
				entryPoint = "main"
			}
		}
	}
	linuxX64 {
		binaries {
			executable {
				entryPoint = "main"
			}
		}
	}
	android()
	sourceSets {
		val commonMain by getting
		val commonTest by getting {
			dependencies {
				implementation(kotlin("test"))
			}
		}
		val jvmMain by getting
		val jvmTest by getting
		val mingwX64Main by getting
		val mingwX64Test by getting
		val linuxX64Main by getting
		val linuxX64Test by getting
		val androidMain by getting {
			dependencies {
				implementation("com.google.android.material:material:1.5.0")
			}
		}
		val androidTest by getting {
			dependencies {
				implementation("junit:junit:4.13.2")
			}
		}
	}
}

android {
	compileSdk = 33
	sourceSets["main"].manifest.srcFile("src/androidMain/AndroidManifest.xml")
	defaultConfig {
		minSdk = 24
		targetSdk = 33
	}
	compileOptions {
		sourceCompatibility = JavaVersion.VERSION_11
		targetCompatibility = JavaVersion.VERSION_11
	}
}