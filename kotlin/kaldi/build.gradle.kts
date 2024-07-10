plugins {
	id("com.android.library")
}

android {
	namespace = "page.doomsdayrs.libs.kaldi"
	compileSdk = 34

	defaultConfig {
		minSdk = 24

		testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
		consumerProguardFiles("consumer-rules.pro")
		externalNativeBuild {
			cmake {
				arguments(
					"-DMATHLIB=OpenBLAS",
					"-DBUILD_SHARED_LIBS=ON",

					"-Wno-dev",
					"-DKALDI_BUILD_EXE=OFF",
					"-DKALDI_BUILD_TEST=OFF",
				)
				cppFlags("-O3", "-DFST_NO_DYNAMIC_LINKING")
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

dependencies {
	compileOnly(project(":openfst"))
	compileOnly(project(":openblas"))
}