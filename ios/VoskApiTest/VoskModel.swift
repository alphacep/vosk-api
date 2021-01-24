//
//  Vosk.swift
//  VoskApiTest
//
//  Created by Niсkolay Shmyrev on 01.03.20.
//  Copyright © 2020-2021 Alpha Cephei. All rights reserved.
//

import Foundation

public final class VoskModel {
    
    var model : OpaquePointer!
    var spkModel : OpaquePointer!
    
    init() {
        
        // Set to -1 to disable logs
        vosk_set_log_level(0);
        
        if let resourcePath = Bundle.main.resourcePath {
            let modelPath = resourcePath + "/vosk-model-small-en-us-0.15"
            let spkModelPath = resourcePath + "/vosk-model-spk-0.4"
            
            model = vosk_model_new(modelPath)
            spkModel = vosk_spk_model_new(spkModelPath)
        }
    }
    
    deinit {
        vosk_model_free(model)
        vosk_spk_model_free(spkModel)
    }
    
}

