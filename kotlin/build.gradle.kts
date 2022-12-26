/*
 * Copyright 2020 Alpha Cephei Inc. & Doomsdayrs
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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
	/*
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
	 */
	android()
	sourceSets {
		val commonMain by getting
		val commonTest by getting {
			dependencies {
				implementation(kotlin("test"))
			}
		}
		val jvmMain by getting {
			dependencies {
				api("net.java.dev.jna:jna:5.12.1")
			}
		}
		val jvmTest by getting
		//val mingwX64Main by getting
		//val mingwX64Test by getting
		//val linuxX64Main by getting
		//val linuxX64Test by getting
		val androidMain by getting {
			dependsOn(jvmMain)
			dependencies {
				api("net.java.dev.jna:jna:5.12.1@aar")
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