//
//  ViewController.swift
//  VoskApiTest
//
//  Created by Niсkolay Shmyrev on 01.03.20.
//  Copyright © 2020 Alpha Cephei. All rights reserved.
//

import UIKit

class ViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()
        
        let vosk = Vosk();
        vosk.run();
    }

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
    }


}

