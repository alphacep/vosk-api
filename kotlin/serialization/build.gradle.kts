plugins {
	kotlin("multiplatform")
	kotlin("plugin.serialization") version "1.7.20"
	`maven-publish`
}

group = "com.alphacephei"
version = "0.0.0"

repositories {
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

	/*
	native {
		val main by compilations.getting
		val libvosk by main.cinterops.creating

		binaries {
			sharedLib()
		}
	}
	 */

	sourceSets {
		val commonMain by getting {
			dependencies {
				api(project(":"))
				api("org.jetbrains.kotlinx:kotlinx-serialization-json:1.4.1")
			}
		}
		val commonTest by getting {
			dependencies {
				implementation(kotlin("test"))
			}
		}
	}
}