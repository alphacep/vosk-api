plugins {
	id("com.android.library")
}

android {
	namespace = "page.doomsdayrs.libs.clapack"
	compileSdk = 34

	defaultConfig {
		minSdk = 24

		testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
		consumerProguardFiles("consumer-rules.pro")
		externalNativeBuild {
			cmake {
				arguments(
					"-DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY",
					"-DCMAKE_CROSSCOMPILING=True",
					"-DCMAKE_SYSTEM_NAME=Generic",
					"-Wno-dev"
				)
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