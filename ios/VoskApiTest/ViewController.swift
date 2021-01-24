//
//  ViewController.swift
//  VoskApiTest
//
//  Created by Niсkolay Shmyrev on 01.03.20.
//  Copyright © 2020-2021 Alpha Cephei. All rights reserved.
//

import UIKit
import AVFoundation

enum WorkMode {
    case stopped
    case microphone
    case file
}

class ViewController: UIViewController {
    
    var mode: WorkMode!
    
    @IBOutlet weak var recognizeFile: UIButton!
    @IBOutlet weak var mainText: UITextView!
    @IBOutlet weak var recognizeMicrophone: UIButton!
    
    var audioEngine : AVAudioEngine!
    var processingQueue: DispatchQueue!
    var model : VoskModel!
    
    func setMode(mode: WorkMode) {
        switch mode {
        case .stopped:
            self.recognizeFile.isEnabled = true
            self.recognizeMicrophone.isEnabled = true
            self.recognizeMicrophone.setTitle("Recognize Microphone",for: .normal)
        case .microphone:
            self.recognizeFile.isEnabled = false
            self.recognizeMicrophone.isEnabled = true
            self.recognizeMicrophone.setTitle("Stop Microphone",for: .normal)
            self.mainText.text = ""
        case .file:
            self.recognizeFile.isEnabled = false
            self.recognizeMicrophone.isEnabled = false
            self.mainText.text =  "Processing file..."
        }
        self.mode = mode
    }
    
    func startAudioEngine() {
        do {
            
            // Create a new audio engine.
            audioEngine = AVAudioEngine()
            
            let inputNode = audioEngine.inputNode
            let formatInput = inputNode.inputFormat(forBus: 0)
            let formatPcm = AVAudioFormat.init(commonFormat: AVAudioCommonFormat.pcmFormatInt16, sampleRate: formatInput.sampleRate, channels: 1, interleaved: true)
            
            let recognizer = Vosk(model: model, sampleRate: Float(formatInput.sampleRate))
            
            inputNode.installTap(onBus: 0,
                                 bufferSize: UInt32(formatInput.sampleRate / 10),
                                 format: formatPcm) { buffer, time in
                                    self.processingQueue.async {
                                        let res = recognizer.recognizeData(buffer: buffer)
                                        DispatchQueue.main.async {
                                            self.mainText.text = res + "\n" + self.mainText.text
                                        }
                                    }
            }
            
            // Start the stream of audio data.
            audioEngine.prepare()
            try audioEngine.start()
        } catch {
            print("Unable to start AVAudioEngine: \(error.localizedDescription)")
        }
    }
    
    func stopAudioEngine() {
        audioEngine.stop()
    }
    
    @IBAction func runRecognizeMicrohpone(_ sender: Any) {
        if (mode == .stopped) {
            setMode(mode: .microphone)
            startAudioEngine()
        } else {
            stopAudioEngine()
            setMode(mode: .stopped)
        }
    }
    
    @IBAction func runRecognizeFile(_ sender: Any) {
        setMode(mode: .file)
        processingQueue.async {
            let recognizer = Vosk(model: self.model, sampleRate: 16000.0)
            let res = recognizer.recognizeFile()
            DispatchQueue.main.async {
                self.mainText.text = res
                self.setMode(mode: .stopped)
            }
        }
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setMode(mode: .stopped)
        processingQueue = DispatchQueue(label: "recognizerQueue")
        model = VoskModel()
    }
    
    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
    }
}

