//
//  Vosk.swift
//  VoskApiTest
//
//  Created by Niсkolay Shmyrev on 01.03.20.
//  Copyright © 2020-2021 Alpha Cephei. All rights reserved.
//

import Foundation
import AVFoundation

public final class Vosk {
    
    var recognizer : OpaquePointer!

    init(model: VoskModel, sampleRate: Float) {
        recognizer = vosk_recognizer_new_spk(model.model, sampleRate, model.spkModel)
    }
    
    deinit {
        vosk_recognizer_free(recognizer);
    }
    
    func recognizeFile() -> String {
        var sres = ""
        
        if let resourcePath = Bundle.main.resourcePath {
            
            let audioFile = URL(fileURLWithPath: resourcePath + "/10001-90210-01803.wav")
    
            if let data = try? Data(contentsOf: audioFile) {
                    let _ = data.withUnsafeBytes {
                        vosk_recognizer_accept_waveform(recognizer, $0, Int32(data.count))
                    }
                    let res = vosk_recognizer_final_result(recognizer);
                    sres = String(validatingUTF8: res!)!;
                    print(sres);
            }
        }
        
        return sres
    }
    
    
    func recognizeData(buffer : AVAudioPCMBuffer) -> String {
        let dataLen = Int(buffer.frameLength * 2)
        let channels = UnsafeBufferPointer(start: buffer.int16ChannelData, count: 1)
        let endOfSpeech = channels[0].withMemoryRebound(to: Int8.self, capacity: dataLen) {
            vosk_recognizer_accept_waveform(recognizer, $0, Int32(dataLen))
        }
        let res = endOfSpeech == 1 ?vosk_recognizer_result(recognizer) :vosk_recognizer_partial_result(recognizer)
        return String(validatingUTF8: res!)!;
    }
}
