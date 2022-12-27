plugins {
	kotlin("jvm")
	application
}

group = "com.alphacephei"
version = "0.0.0"

application {
	mainClass.set("DecoderDemo")
}

repositories {
	mavenCentral()
}

dependencies {
	implementation(project(":"))
}