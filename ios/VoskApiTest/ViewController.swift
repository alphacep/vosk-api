//
//  ViewController.swift
//  VoskApiTest
//
//  Created by Niсkolay Shmyrev on 01.03.20.
//  Copyright © 2020 Alpha Cephei. All rights reserved.
//

import UIKit

class ViewController: UIViewController {

    @IBOutlet var mainText: UITextView!

    override func viewDidLoad() {
        super.viewDidLoad()
    
        DispatchQueue.global(qos: .userInitiated).async {
            DispatchQueue.main.async {
                 self.mainText.text =  "Processing file..."
            }
            let vosk = Vosk()
            let res = vosk.recognizeFile()
            DispatchQueue.main.async {
                self.mainText.text = res
            }
        }
    }

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
    }
}

