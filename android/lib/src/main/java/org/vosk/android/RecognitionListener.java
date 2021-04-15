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

/**
 * Interface to receive recognition results
 */
public interface RecognitionListener {

    /**
     * Called when partial recognition result is available.
     */
    void onPartialResult(String hypothesis);

    /**
     * Called after silence occured.
     */
    void onResult(String hypothesis);

    /**
     * Called after stream end.
     */
    void onFinalResult(String hypothesis);

    /**
     * Called when an error occurs.
     */
    void onError(Exception exception);

    /**
     * Called after timeout expired
     */
    void onTimeout();
}
