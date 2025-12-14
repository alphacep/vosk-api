plugins {
	id("com.android.library")
}

android {
	namespace = "page.doomsdayrs.libs.openblas"
	compileSdk = 34

	defaultConfig {
		minSdk = 24

		testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
		consumerProguardFiles("consumer-rules.pro")
		ndk {
			abiFilters += "arm64-v8a"
			abiFilters += "armeabi-v7a"
			// TODO x86
		}
		externalNativeBuild {
			cmake {
				cppFlags("-marm", "-mfpu=vfp", "-mfloat-abi=softfp", "-Wno-dev")
			}
		}
	}

	buildTypes {
		release {
			isMinifyEnabled = false
			proguardFiles(
				getDefaultProguardFile("proguard-android-optimize.txt"),
				"proguard-rules.pro"
			)
		}
	}
	externalNativeBuild {
		cmake {
			path("src/main/cpp/CMakeLists.txt")
			version = "3.22.1"
		}
	}
	compileOptions {
		sourceCompatibility = JavaVersion.VERSION_1_8
		targetCompatibility = JavaVersion.VERSION_1_8
	}
}