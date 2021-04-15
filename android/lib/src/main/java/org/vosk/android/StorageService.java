// Copyright 2019 Alpha Cephei Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package org.vosk.android;

import android.content.Context;
import android.content.res.AssetManager;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import org.vosk.Model;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;

/**
 * Provides utility methods to sync model files to external storage to allow
 * C++ code access them. Relies on file named "uuid" to track updates.
 */
public class StorageService {

    protected static final String TAG = StorageService.class.getSimpleName();

    public interface Callback<R> {
        void onComplete(R result);
    }

    public static void unpack(Context context, String sourcePath, final String targetPath, final Callback<Model> completeCallback, final Callback<IOException> errorCallback) {
        Executor executor = Executors.newSingleThreadExecutor(); // change according to your requirements
        Handler handler = new Handler(Looper.getMainLooper());
        executor.execute(() -> {
            try {
                final String outputPath = sync(context, sourcePath, targetPath);
                Model model = new Model(outputPath);
                handler.post(() -> completeCallback.onComplete(model));
            } catch (final IOException e) {
                handler.post(() -> errorCallback.onComplete(e));
            }
        });
    }

    public static String sync(Context context, String sourcePath, String targetPath) throws IOException {

        AssetManager assetManager = context.getAssets();

        File externalFilesDir = context.getExternalFilesDir(null);
        if (externalFilesDir == null) {
            throw new IOException("cannot get external files dir, "
                    + "external storage state is " + Environment.getExternalStorageState());
        }

        File targetDir = new File(externalFilesDir, targetPath);
        String resultPath = new File(targetDir, sourcePath).getAbsolutePath();
        String sourceUUID = readLine(assetManager.open(sourcePath + "/uuid"));
        try {
            String targetUUID = readLine(new FileInputStream(new File(targetDir, sourcePath + "/uuid")));
            if (targetUUID.equals(sourceUUID)) return resultPath;
        } catch (FileNotFoundException e) {
            // ignore
        }
        deleteContents(targetDir);

        copyAssets(assetManager, sourcePath, targetDir);

        // Copy uuid
        copyFile(assetManager, sourcePath + "/uuid", targetDir);

        return resultPath;
    }

    private static String readLine(InputStream is) throws IOException {
        return new BufferedReader(new InputStreamReader(is)).readLine();
    }

    private static boolean deleteContents(File dir) {
        File[] files = dir.listFiles();
        boolean success = true;
        if (files != null) {
            for (File file : files) {
                if (file.isDirectory()) {
                    success &= deleteContents(file);
                }
                if (!file.delete()) {
                    success = false;
                }
            }
        }
        return success;
    }

    private static void copyAssets(AssetManager assetManager, String path, File outPath) throws IOException {
        String[] assets = assetManager.list(path);
        if (assets == null) {
            return;
        }
        if (assets.length == 0) {
            if (!path.endsWith("uuid"))
                copyFile(assetManager, path, outPath);
        } else {
            File dir = new File(outPath, path);
            if (!dir.exists()) {
                Log.v(TAG, "Making directory " + dir.getAbsolutePath());
                if (!dir.mkdirs()) {
                    Log.v(TAG, "Failed to create directory " + dir.getAbsolutePath());
                }
            }
            for (String asset : assets) {
                copyAssets(assetManager, path + "/" + asset, outPath);
            }
        }
    }

    private static void copyFile(AssetManager assetManager, String fileName, File outPath) throws IOException {
        InputStream in;

        Log.v(TAG, "Copy " + fileName + " to " + outPath);
        in = assetManager.open(fileName);
        OutputStream out = new FileOutputStream(outPath + "/" + fileName);

        byte[] buffer = new byte[4000];
        int read;
        while ((read = in.read(buffer)) != -1) {
            out.write(buffer, 0, read);
        }
        in.close();
        out.close();
    }
}
