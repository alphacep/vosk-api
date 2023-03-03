/*
 * Copyright 2023 Alpha Cephei Inc.
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
package org.vosk.android

import android.content.Context
import android.content.res.AssetManager
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.util.Log
import org.vosk.Model
import java.io.*
import java.util.concurrent.Executor
import java.util.concurrent.Executors
import java.util.function.Consumer

/**
 * Provides utility methods to sync model files to external storage to allow
 * C++ code access them. Relies on file named "uuid" to track updates.
 */
object StorageService {
	private val TAG = StorageService::class.simpleName

	@JvmStatic
	fun unpack(
		context: Context,
		sourcePath: String,
		targetPath: String,
		completeCallback: Consumer<Model>,
		errorCallback: Consumer<IOException>
	) {
		val executor: Executor =
			Executors.newSingleThreadExecutor() // change according to your requirements
		val handler = Handler(Looper.getMainLooper())
		executor.execute {
			try {
				val outputPath = sync(context, sourcePath, targetPath)
				val model = Model(outputPath)
				handler.post { completeCallback.accept(model) }
			} catch (e: IOException) {
				handler.post { errorCallback.accept(e) }
			}
		}
	}

	@JvmStatic
	@Throws(IOException::class)
	fun sync(context: Context, sourcePath: String, targetPath: String): String {
		val assetManager = context.assets
		val externalFilesDir = context.getExternalFilesDir(null)
			?: throw IOException(
				"cannot get external files dir, "
						+ "external storage state is " + Environment.getExternalStorageState()
			)
		val targetDir = File(externalFilesDir, targetPath)
		val resultPath = File(targetDir, sourcePath).absolutePath
		val sourceUUID = readLine(assetManager.open("$sourcePath/uuid"))
		try {
			val targetUUID = readLine(FileInputStream(File(targetDir, "$sourcePath/uuid")))
			if (targetUUID == sourceUUID) return resultPath
		} catch (e: FileNotFoundException) {
			// ignore
		}
		deleteContents(targetDir)
		copyAssets(assetManager, sourcePath, targetDir)

		// Copy uuid
		copyFile(assetManager, "$sourcePath/uuid", targetDir)
		return resultPath
	}

	@Throws(IOException::class)
	private fun readLine(inputStream: InputStream): String {
		return BufferedReader(InputStreamReader(inputStream)).use { it.readLine() }
	}

	private fun deleteContents(dir: File): Boolean {
		val files = dir.listFiles()
		var success = true
		if (files != null) {
			for (file in files) {
				if (file.isDirectory) {
					success = success and deleteContents(file)
				}
				if (!file.delete()) {
					success = false
				}
			}
		}
		return success
	}

	@Throws(IOException::class)
	private fun copyAssets(assetManager: AssetManager, path: String, outPath: File) {
		val assets = assetManager.list(path) ?: return
		if (assets.isEmpty()) {
			if (!path.endsWith("uuid")) copyFile(assetManager, path, outPath)
		} else {
			val dir = File(outPath, path)
			if (!dir.exists()) {
				Log.v(TAG, "Making directory " + dir.absolutePath)
				if (!dir.mkdirs()) {
					Log.v(TAG, "Failed to create directory " + dir.absolutePath)
				}
			}
			for (asset in assets) {
				copyAssets(assetManager, "$path/$asset", outPath)
			}
		}
	}

	@Throws(IOException::class)
	private fun copyFile(assetManager: AssetManager, fileName: String, outPath: File) {
		Log.v(TAG, "Copy $fileName to $outPath")
		assetManager.open(fileName).use { inputStream ->
			FileOutputStream("$outPath/$fileName").use { out ->
				val buffer = ByteArray(4000)
				var read: Int
				while (inputStream.read(buffer).also { read = it } != -1) {
					out.write(buffer, 0, read)
				}
			}
		}
	}
}