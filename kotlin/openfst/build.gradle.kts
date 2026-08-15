plugins {
	id("com.android.library")
}

android {
	namespace = "page.doomsdayrs.libs.openfst"
	compileSdk = 34

	defaultConfig {
		minSdk = 24

		testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
		consumerProguardFiles("consumer-rules.pro")
		externalNativeBuild {
			cmake {
				cppFlags("-O3", "-DFST_NO_DYNAMIC_LINKING")
				arguments(
					"-DBUILD_SHARED_LIBS=ON",
					"-DHAVE_BIN=OFF",
					"-DHAVE_LOOKAHEAD=ON",
					"-DHAVE_NGRAM=ON",

					"-DHAVE_COMPACT=OFF",
					"-DHAVE_CONST=OFF",
					"-DHAVE_FAR=OFF",
					"-DHAVE_GRM=OFF",
					"-DHAVE_PDT=OFF",
					"-DHAVE_MPDT=OFF",
					"-DHAVE_LINEAR=OFF",
					"-DHAVE_LOOKAHEAD=OFF",
					"-DHAVE_SPECIAL=OFF",

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