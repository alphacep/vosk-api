//
//  Vosk.swift
//  VoskApiTest
//
//  Created by Niсkolay Shmyrev on 01.03.20.
//  Copyright © 2020 Alpha Cephei. All rights reserved.
//

import Foundation

public final class Vosk {
    
    func recognizeFile() -> String {
        var sres = ""
        if let resourcePath = Bundle.main.resourcePath {

            // Set to -1 to disable logs
            vosk_set_log_level(0);

            let modelPath = resourcePath + "/vosk-model-small-en-us-0.4"
            let spkModelPath = resourcePath + "/vosk-model-spk-0.4"

            let model = vosk_model_new(modelPath)
            let spkModel = vosk_spk_model_new(spkModelPath)
            let recognizer = vosk_recognizer_new_spk(model, spkModel, 16000.0)

            let audioFile = URL(fileURLWithPath: resourcePath + "/10001-90210-01803.wav")
            if let data = try? Data(contentsOf: audioFile) {
                let _ = data.withUnsafeBytes {
                    vosk_recognizer_accept_waveform(recognizer, $0, Int32(data.count))
                }
                let res = vosk_recognizer_final_result(recognizer);
                sres = String(validatingUTF8: res!)!;
                print(sres);
            }

            vosk_recognizer_free(recognizer)
            vosk_model_free(model)
        }
        return sres
    }
}
